Cleanup before posting
----------------------

 - Get rid of the email from README.md
 - Get rid of gigi and costica from test_rpcnode.py

Correctness
-----------

 - Is there a way to have those start() methods return **after** the server
   has blocked waiting on accept? This would be nice in order to avoid failing
   to start a server and having the calling code unaware of it.

Efficiency
----------

 + Ineffective serialization in libprivipk (JSON, but MsgPack would be smaller)
 + avoid manually serializing/deserializing in KGC, make it transparent
   - also, it adds overhead because we are double JSON encoding

Crypto
------

### Right now we only allow one key per user
 
 + need to change code to be able to deal with a user having multiple keys
   and verifying that they chain together maybe

### How to deal with BCC field?

 + if we include a wrapped key, that would give away that someone has 
   been BCC'd
 + one way is to include their keys in different headers:
   + X-Quasar-Bcc-Keyids
   + X-Quasar-Bcc-WrappedKeys
   + then change the SMTP server to look for X-Quasar-Bcc-Keyids/WrappedKeys
     and take those headers out for non-BCC recipients
 + another way is to just send a different email to the BCC'd users, if we 
   can specify to the SMTP server not to send the email to the other users,
   while including them in the recipients list
   + see [this](https://stackoverflow.com/questions/1546367/python-how-to-send-mail-with-to-cc-and-bcc)

Others
------

 + Figure out why file upload doesn't work
 + it looks like no POST request to /files/ is sent, so the file is never
   uploaded. there's an empty `setAttachments` method in the `inbox-scaffold-html5`
   web app which suggests they did not implement this yet.
 + Nylas's semantics for Archive folder in its inbox web ui
   - After deleting all messages in Gmail, some messages were left in Archive in
     the inboxwebapp.
 + Email message threading
   - Threading doesn't seem to work in inbox web app... Not sure if it ever worked.
 + [DONE] Sending email to oneself fails sometimes in `inbox-start` in
   `crypto_unwrap_keys` because the HMAC verification fails on the wrapped key
   ctext for some reason
   - noticed that it failed on one VM, but succeeded on another
   - noticed that `create_email` was called twice in `inbox-api` when sending an
     email to oneself
     + this was true both for the successful VM and the failed VM
     + both VMs got the 2nd `create_email`-generated ciphertext 
   - noticed that `crypto_wrap_keys` is called with the same derivedkey the 2nd
     time as expected.  However, the ciphertext is different because the plaintext
     (i.e. the randomly generated symmetric key) is different.
   - verified (with SHA256) that the two wrapped key ctexts (`inbox-api`
     generated and `inbox-start` received) are the same `=>` no corruption
     happening here
   - confirmed that `myemail == fromemail == 'whatitshouldbe'` in `inbox-sync`
     + how about in `inbox-api`?
   - not sure why two calls to `create_email`
     + not sure why succeeding one one VM but not on the other
   - **Idiot:** The new public key was not Put in the KLS, so was using wrong shared
     secret to unwrap key
 + [DONE] Base64 / encoding overhead
   - [DONE] A three letter message is too large when encrypted:
     + `ctext1 (from logs): 
        gAAAAABVShHYuKKPhUaSVvwBArMSvNTcdrIESWoBgvLnTtI43LhEHC1LiX6S5i3CL0dbjifeEuEJf3oubokhYoP50B0hF_nylg==`
     + `ctext2 (from test_cio [ ptext -> unicode(ptext).encode('utf-8) -> encrypt())])
       gAAAAABVShM2LehLSZJ39jxpoRUwtAP_lYH08ji3FCxxEwVQP8uhXWfyrQSeLuku92cBXoVtsi6LeLTUdMppFVgagUBMMBEgug==`
   - [DONE] Seems to be the same size, even outside the sync-engine. Maybe Fernet adds some
     metadata to the ciphertext? Should look more into source of overhead.
     + Yes, it adds one byte, the current time, the IV and an HMAC to each ciphertext
 + [DONE] Check that when we Put we succeed and check that we are actually
   connected to a DHT network instead of merely starting our own if the entry nodes
   do not reply
 + [DONE] How do we get our own PK/SK? we would have to store it in the DB and associate it with our namespace/account
 + [DONE] make sure that the ciphertext can be properly MIME encoded (proper line length,
   newlines, etc)
   + for the body of the email, I think outputting base64-encoded text should
     be alright (outputing RAW bytes will not be alright though)
   + for attachments, not sure what format they are in
