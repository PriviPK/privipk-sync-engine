"""
When sending mail, Inbox tries to be a good citizen to the modern world.
This means everything we send is either ASCII or UTF-8.
That means no Latin-1 or ISO-8859-1.

All headers are converted to ASCII and if that doesn't work, UTF-8.

Note that plain text that's UTF-8 will be sent as base64. i.e.:
Content-Type: text/text; charset='utf-8'
Content-Transfer-Encoding: base64

This is because not all servers support 8BIT and so flanker drops to b64.
http://www.w3.org/Protocols/rfc1341/5_Content-Transfer-Encoding.html

"""
import pkg_resources

from flanker import mime
from flanker.addresslib import address
from html2text import html2text

from inbox.sqlalchemy_ext.util import generate_public_id
from inbox.log import get_logger
log = get_logger()

from inbox.crypto.crypto import crypto_symkey_encrypt, crypto_symkey_random,\
    crypto_privkey_get_mine, crypto_get_kls, crypto_pubkey_get_mine,\
    crypto_symkey_wrap, X_QUASAR_WRAPPEDKEYS, X_QUASAR_ENCRYPTED, X_QUASAR_ENCRYPTED_YES 
    
import privipk
from privipk.keys import PublicKey

VERSION = pkg_resources.get_distribution('inbox-sync').version

REPLYSTR = 'Re: '


# Patch flanker to use base64 rather than quoted-printable encoding for
# MIME parts with long lines. Flanker's implementation of quoted-printable
# encoding (which ultimately relies on the Python quopri module) inserts soft
# line breaks that end with '=\n'. Some Exchange servers fail to handle this,
# and garble the encoded messages when sending, unless you break the lines with
# '=\r\n'. Their expectation seems to be technically correct, per RFC1521
# section 5.1. However, we opt to simply avoid this mess entirely.
def fallback_to_base64(charset, preferred_encoding, body):
    if charset in ('ascii', 'iso8859=1', 'us-ascii'):
        if mime.message.part.has_long_lines(body):
            # In the original implementation, this was
            # return stronger_encoding(preferred_encoding, 'quoted-printable')
            return mime.message.part.stronger_encoding(preferred_encoding,
                                                       'base64')
        else:
            return preferred_encoding
    else:
        return mime.message.part.stronger_encoding(preferred_encoding,
                                                   'base64')

mime.message.part.choose_text_encoding = fallback_to_base64

# NOTE: JOHNNY: Here we are ready to encrypt before the email is sent out to
# SMTP or to IMAP
#
# Things to do:
# - generate a symmetric key
# - wrap the key for the recipient (if encrypt_just_for_me = false)
#   + TODO: QUASAR: ideally, we want a different symmetric key for each recipient =>
#     => must send different emails to each recipient (since they are
#     encrypted differently) => must be able to tell SMTP server to
#     not send an email to all recipients (so that I can encrypt for Bob and
#     send the email to Bob, and Bob can see it was also sent to Alice, but
#     Alice won't get an email encrypted under Bob's PK, which would
#     be useless to her)
#   + for now, we use the same key for all like OpenPGP
#     (http://www.rainydayz.org/content/831-encrypting-message)
# - wrap the key for me
# - encrypt attachmentsc
#   + might be multiple parts
# - encrypt body
#   + might have multiple parts
def create_email(from_name,
                 from_email,
                 reply_to,
                 inbox_uid,
                 to_addr,
                 cc_addr,
                 bcc_addr,
                 subject,
                 html,
                 in_reply_to,
                 references,
                 attachments,
                 encrypt_just_for_me,
                 account=None):
    """
    Creates a MIME email message (both body and sets the needed headers).

    Parameters
    ----------
    from_name: string
        The name aka phrase of the sender.
    from_email: string
        The sender's email address.
    to_addr, cc_addr, bcc_addr: list of pairs (name, email_address), or None
        Message recipients.
    reply_to: tuple or None
        Indicates the mailbox in (name, email_address) format to which
        the author of the message suggests that replies be sent.
    subject : string
        a utf-8 encoded string
    html : string
        a utf-8 encoded string
    in_reply_to: string or None
        If this message is a reply, the Message-Id of the message being replied
        to.
    references: list or None
        If this message is a reply, the Message-Ids of prior messages in the
        thread.
    attachments: list of dicts, optional
        a list of dicts(filename, data, content_type)
    """
    html = html if html else ''
    plaintext = html2text(html)
    
    # NOTE: JOHNNY: We set an 'encrypt' flag so that we can later easily call this
    # function to create unencrypted emails
    # TODO: QUASAR: Move this as a parameter set to false by default to maintain backwards compatibility
    encrypt = True
    symkey = None
    public_keys = dict()

    log.info("quasar|create_email", mid=inbox_uid, has_attachments=(attachments != None),
             subject=subject, encrypt_just_for_me=encrypt_just_for_me,
             to_addr=to_addr,cc_addr=cc_addr,bcc_addr=bcc_addr)

    # Create a multipart/alternative message
    msg = mime.create.multipart('alternative')

    # Gmail sets the From: header to the default sending account. We can
    # however set our own custom phrase i.e. the name that appears next to the
    # email address (useful if the user has multiple aliases and wants to
    # specify which to send as), see: http://lee-phillips.org/gmailRewriting/
    # For other providers, we simply use name = ''
    from_addr = address.EmailAddress(from_name, from_email)
    msg.headers['From'] = from_addr.full_spec()

    # QUASAR: We set up the headers and lookup the public keys here
    if encrypt == True:
        log.debug("quasar|create_email (-> encrypting)")
        msg.headers[X_QUASAR_ENCRYPTED] = X_QUASAR_ENCRYPTED_YES
        symkey = crypto_symkey_random()
        my_sk = crypto_privkey_get_mine(account)
        my_address = str(from_addr)
        wrappedkeys = ''

        # lookup public keys of recipients
        kls_client = crypto_get_kls()
        if encrypt_just_for_me == False:
            # TODO: QUASAR: Need to handle BCC properly. Revealing BCCd users here...
            all_but_me = []
            if to_addr != None and to_addr != account.email_address:
                all_but_me.extend(to_addr)
            if cc_addr != None and cc_addr != account.email_address:
                all_but_me.extend(cc_addr)
            if bcc_addr != None and bcc_addr != account.email_address:
                all_but_me.extend(bcc_addr)

            for t in all_but_me:
                name = t[0]
                spec = t[1]
                emailAddr = str(address.EmailAddress(name, spec))

                # TODO: QUASAR: graceful degradation when pubkey cannot be found
                pkstr = kls_client.get(emailAddr) 
                if pkstr is None:
                    raise LookupError("Could not lookup public key for '" + emailAddr + "'")
                
                # NOTE: nothing to verify here: using certificateless crypto, so if pubkey is wrong
                # then shared symmetric key will be wrong
                public_keys[emailAddr] = PublicKey.unserialize(privipk.parameters.default, pkstr)

        # include my public key as well
        public_keys[my_address] = crypto_pubkey_get_mine(account)

        # wrap the symmetric key up for the recipients to be able to decrypt it
        for emailAddr, pk in public_keys.iteritems():
            wrappedkeys = crypto_symkey_wrap(symkey, my_sk, pk, emailAddr, wrappedkeys)

        # add the info to the headers
        msg.headers[X_QUASAR_WRAPPEDKEYS] = wrappedkeys

        log.debug("quasar|create_email", wrappedkeys=msg.headers[X_QUASAR_WRAPPEDKEYS])

        # encrypt subject, plaintext and HTML
        # TODO: QUASAR: need base64 encoding here or utf8 or something but
        # the result will also be base64 encoded again due to MIME!
        # => silly overheads
        plaintext = crypto_symkey_encrypt(symkey, unicode(plaintext).encode('utf-8'))
        html = crypto_symkey_encrypt(symkey, unicode(html).encode('utf-8'))
        subject = crypto_symkey_encrypt(symkey, unicode(subject).encode('utf-8'))
    else:
        log.debug("quasar|create_email (-> NOT encrypting)")

    msg.append(
        mime.create.text('plain', plaintext),
        mime.create.text('html', html))

    # Create an outer multipart/mixed message
    if attachments:
        text_msg = msg
        msg = mime.create.multipart('mixed')

        # The first part is the multipart/alternative text part
        msg.append(text_msg)

        # The subsequent parts are the attachment parts
        for a in attachments:
            # QUASAR: Encrypt attachments
            ctext = a['data']
            filename = a['filename']
            if encrypt == True:
                ctext = crypto_symkey_encrypt(symkey, a['data'])
                #filename = crypto_symkey_encrypt(symkey, a['filename'])

            # Disposition should be inline if we add Content-ID
            msg.append(mime.create.attachment(
                a['content_type'],
                ctext,
                filename=filename,
                disposition='attachment'))

    msg.headers['Subject'] = subject if subject else ''

    # Gmail sets the From: header to the default sending account. We can
    # however set our own custom phrase i.e. the name that appears next to the
    # email address (useful if the user has multiple aliases and wants to
    # specify which to send as), see: http://lee-phillips.org/gmailRewriting/
    # For other providers, we simply use name = ''
    from_addr = address.EmailAddress(from_name, from_email)
    msg.headers['From'] = from_addr.full_spec()

    # Need to set these headers so recipients know we sent the email to them
    # TODO(emfree): should these really be unicode?
    if to_addr:
        full_to_specs = [address.EmailAddress(name, spec).full_spec()
                         for name, spec in to_addr]
        msg.headers['To'] = u', '.join(full_to_specs)
    if cc_addr:
        full_cc_specs = [address.EmailAddress(name, spec).full_spec()
                         for name, spec in cc_addr]
        msg.headers['Cc'] = u', '.join(full_cc_specs)
    if bcc_addr:
        full_bcc_specs = [address.EmailAddress(name, spec).full_spec()
                          for name, spec in bcc_addr]
        msg.headers['Bcc'] = u', '.join(full_bcc_specs)
    
    if reply_to:
        # reply_to is only ever a list with one element
        reply_to_spec = address.EmailAddress(reply_to[0][0], reply_to[0][1])
        msg.headers['Reply-To'] = reply_to_spec.full_spec()

    add_inbox_headers(msg, inbox_uid)

    if in_reply_to:
        msg.headers['In-Reply-To'] = in_reply_to
    if references:
        msg.headers['References'] = '\t'.join(references)

    rfcmsg = _rfc_transform(msg)

    return rfcmsg


def add_inbox_headers(msg, inbox_uid):
    """
    Set a custom `X-INBOX-ID` header so as to identify messages generated by
    Inbox.

    The header is set to a unique id generated randomly per message,
    and is needed for the correct reconciliation of sent messages on
    future syncs.

    Notes
    -----
    We generate the UUID as a base-36 encoded string, and is the same as the
    public_id of the message object.

    """

    our_uid = inbox_uid if inbox_uid else \
        generate_public_id()  # base-36 encoded string

    # Set our own custom header for tracking in `Sent Mail` folder
    msg.headers['X-INBOX-ID'] = our_uid
    msg.headers['Message-Id'] = '<{}@mailer.nylas.com>'.format(our_uid)

    # Potentially also use `X-Mailer`
    msg.headers['User-Agent'] = 'NylasMailer/{0}'.format(VERSION)


def _rfc_transform(msg):
    """ Create an RFC-2821 compliant SMTP message.
    (Specifically, this means splitting the References header to conform to
    line length limits.)

    TODO(emfree): should we split recipient headers too?
    (The answer is probably yes)
    """
    msgstring = msg.to_string()

    start = msgstring.find('References: ')

    if start == -1:
        return msgstring

    end = msgstring.find('\r\n', start + len('References: '))

    substring = msgstring[start:end]

    separator = '\n\t'
    rfcmsg = msgstring[:start] + substring.replace('\t', separator) +\
        msgstring[end:]

    return rfcmsg
