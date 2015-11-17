import string
import base64
from hashlib import sha256
from cryptography.fernet import Fernet

from kls.common import KLS_SERVER_PORT
from kls.client import KlsRpcClient

from inbox.log import get_logger
log = get_logger()

import privipk
from privipk.keys import PublicKey, SecretKey

X_QUASAR_ENCRYPTED = "X-Quasar-Encrypted"
X_QUASAR_ENCRYPTED_YES = "yes"
X_QUASAR_WRAPPEDKEYS = "X-Quasar-WrappedKeys"
X_QUASAR_WRAP_KEY_TYPE = "wrap|key|type"
X_QUASAR_AEAD_KEY_TYPE = "aead|key|type"

INSEP = '|'
OUTSEP = ', '
g_kls_client = None


# returns the public key fingerprint for that user
def crypto_pubkey_fp_get(pk):
    assert isinstance(pk, PublicKey)
    return sha256(pk.serialize()).hexdigest()


def crypto_privkey_get_mine(account):
    secret_key_str = account.secret_key.encode('utf-8')
    return SecretKey.unserialize(privipk.parameters.default, secret_key_str)


# returns my own public key
def crypto_pubkey_get_mine(account):
    public_key_str = account.public_key.encode('utf-8')
    return PublicKey.unserialize(privipk.parameters.default, public_key_str)


# returns a randomly-generated symmetric key
# the key is a URL-safe base64-encoded 32-byte key.
def crypto_symkey_random():
    # NOTE: Fernet keys are 256 bits, but the first 128 bits are used
    # for encryption and the last 128 bits are used for MACing
    key = Fernet.generate_key()
    return key


def crypto_symkey_create(key=None):
    if key is None:
        return crypto_symkey_random()
    else:
        return base64.urlsafe_b64encode(key)


# returns the encryption of 'symkey' under the public key in 'pk'
def crypto_symkey_wrap(symkey, mysk, theirpk, theiremail, wrappedkeys=''):
    assert isinstance(theirpk, PublicKey)
    assert isinstance(mysk, SecretKey)

    # derive the shared symmetric key between me and them
    sharedkey = mysk.deriveKey(theirpk, theiremail, X_QUASAR_WRAP_KEY_TYPE)
    sharedkey = crypto_symkey_create(sharedkey)

    # TODO: not sure why we would need b64 here. are bytes outputted?
    #wkey = base64.b64encode(crypto_symkey_encrypt(sharedkey, symkey))
    wkey = crypto_symkey_encrypt(sharedkey, symkey)
    newkey = theiremail + INSEP +\
             crypto_pubkey_fp_get(theirpk) + INSEP + wkey

    if len(wrappedkeys) > 0:
        return wrappedkeys + OUTSEP + newkey
    else:
        return newkey


# returns the symmetric key for the specified account, by looking it up
# in the 'wrappedkeys' string
#
# the person with 'mysk' and 'mypk' and 'myemail' calls this function
# to unwrap keys from the person with 'theirpk' and 'theiremail'
# (sometimes my == their, such as when syncing your sent messages)
def crypto_symkey_unwrap(wrappedkeys, theirpk, theiremail, mysk, mypk, myemail):
    assert isinstance(mypk, PublicKey)
    assert isinstance(mysk, SecretKey)
    assert isinstance(theirpk, PublicKey)

    myfp = crypto_pubkey_fp_get(mypk)

    log.info("quasar|crypto_symkey_unwrap", wrappedkeys=wrappedkeys,
             myemail=myemail)
    wrappedkeys = string.split(wrappedkeys, OUTSEP)

    # last key might be empty
    if wrappedkeys[-1] == '':
        del wrappedkeys[-1]

    for wkey in wrappedkeys:
        split = string.split(wkey, INSEP)
        email = split[0]
        fp = split[1]
        #encKey = base64.b64decode(split[2])
        encKey = split[2]

        if email == myemail and fp == myfp:
            sharedkey = mysk.deriveKey(theirpk, theiremail,
                                       X_QUASAR_WRAP_KEY_TYPE)
            sharedkey = crypto_symkey_create(sharedkey)
            return crypto_symkey_decrypt(sharedkey, encKey)

    log.error("quasar|crypto_symkey_unwrap",
              error="Could not find key for myself",
              myemail=myemail, myfp=myfp, wrappedkeys=wrappedkeys)
    raise LookupError("Could not find a key wrapped for me")


# returns an authenticated symmetric encryption of 'ptext' under symkey
# uses AES-CBC with random IV. the cryptography.io library also adds the
# current time and some padding
def crypto_symkey_encrypt(symkey, ptext):
    log.info("quasar|crypto_symkey_encrypt", symkey=symkey, ptext=ptext)
    return Fernet(symkey).encrypt(ptext)


# returns the plaintext by decrypting 'ctext' using the 'symkey' key
def crypto_symkey_decrypt(symkey, ctext):
    log.info("quasar|crypto_symkey_decrypt", symkey=symkey, ctext=ctext)
    return Fernet(symkey).decrypt(ctext)


def _crypto_init_kls(config):
    global g_kls_client

    if g_kls_client is not None:
        raise RuntimeError('KLS RPC client has already been initialized' +
                           ' (cannot call _crypto_init_kls twice)')

    kls_host = config.get_required('KLS_HOST')
    kls_port = config.get('KLS_PORT')
    kls_port = kls_port if kls_port is not None else KLS_SERVER_PORT
    log.info("quasar|_crypto_init_kls", kls_host=kls_host, kls_port=kls_port)

    g_kls_client = KlsRpcClient(kls_host, kls_port)


def crypto_get_kls():
    if g_kls_client is None:
        raise RuntimeError('KLS RPC client not initialized' +
                           ' (call _crypto_init_kls please)')

    return g_kls_client

def crypto_test_kls():
    beat = "hello mate!"
    kls_client = crypto_get_kls()
    reply, _ = kls_client.heartbeat(beat)
    if reply != beat:
        raise RuntimeError("Could not talk to the KLS at '" + kls_client.host + ":" + kls_client.port + "'")
