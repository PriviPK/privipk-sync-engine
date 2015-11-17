from crypto import crypto_pubkey_fp_get, crypto_symkey_random,\
    crypto_symkey_encrypt, crypto_symkey_decrypt,\
    crypto_symkey_wrap, crypto_symkey_unwrap, crypto_symkey_create,\
    X_QUASAR_AEAD_KEY_TYPE\

import privipk
from privipk.keys import LongTermSecretKey, KeyPair
from privipk.kgc import Kgc

import os
import re
import unittest


class CryptoTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.params = privipk.parameters.default
        cls.kgc = Kgc(LongTermSecretKey(cls.params))

        cls.sk = []
        cls.pk = []
        cls.kp = []
        cls.emails = []
        for i in range(0, 3):
            email = 'bob' + str(i)
            kp = cls._genKeyPair(email, cls.kgc, cls.params)
            sk = kp.getSecretKey()
            pk = kp.getPublicKey()
            cls.emails.append(email)
            cls.kp.append(kp)
            cls.sk.append(sk)
            cls.pk.append(pk)

    @classmethod
    def tearDownClass(cls):
        pass

    def testSymKeyType(self):
        symkey = crypto_symkey_random()
        self.assertTrue(self._isUrlSafeBase64(symkey))
        self.assertTrue(isinstance(symkey, str))

        sharedkey = self.sk[0].deriveKey(
            self.pk[1], self.emails[1], X_QUASAR_AEAD_KEY_TYPE)
        sharedkey = crypto_symkey_create(sharedkey)
        self.assertTrue(self._isUrlSafeBase64(sharedkey))

    def testSymCrypto(self):
        self.assertTrue(self._isUrlSafeBase64('aAbB09cc-_=='))
        self.assertTrue(self._isBase64('aAbB09cc+/=='))

        self._testSymCrypto("a")
        self._testSymCrypto("hi")
        self._testSymCrypto("how's it going?\n")
        self._testSymCrypto(os.urandom(512))

        # test ever increasing cypher text sizes
        ptext = 't'
        for i in range(1, 1024):
            ptext += 't'
            self._testSymCrypto(ptext)

    def _testSymCrypto(self, ptext):
        symkey = crypto_symkey_random()
        ctext = crypto_symkey_encrypt(symkey, ptext)
        assert isinstance(symkey, str)

        # Ensure decoding works
        self.assertTrue(self._isUrlSafeBase64(ctext))

        dtext = crypto_symkey_decrypt(symkey, ctext)
        assert isinstance(dtext, type(ptext))

    def testPubkeyFingerprint(self):
        fp = []
        for i in range(0, len(self.pk)):
            fp.append(crypto_pubkey_fp_get(self.pk[i]))

        self.assertEqual(fp[0], crypto_pubkey_fp_get(self.pk[0]))

        for i in range(0, len(fp) - 1):
            for j in range(i + 1, len(fp)):
                self.assertNotEqual(fp[i], fp[j])

    def testKeyWrapping(self):
        #
        # We have 3 key-pairs setup for 3 users => have each user email
        # the other 2 users => wrap the symmetric key that encrypts the
        # email for all 3 users under the sender's public key
        #
        for i in range(0, len(self.kp)):
            keys = ''
            mysk = self.sk[i]
            mypk = self.pk[i]
            myemail = self.emails[i]

            symkey = crypto_symkey_random()

            for j in range(0, len(self.kp)):
                keys = crypto_symkey_wrap(
                    symkey, mysk, self.pk[j], self.emails[j], keys)

            for j in range(0, len(self.kp)):
                key = crypto_symkey_unwrap(
                    keys, mypk, myemail,
                    self.sk[j], self.pk[j], self.emails[j])

                self.assertEqual(key, symkey)

    def _isBase64(self, s):
        return (len(s) % 4 == 0) and re.match('^[A-Za-z0-9+/]+[=]{0,2}$', s)

    def _isUrlSafeBase64(self, s):
        # just replaces the + with a -, and replaces the / with a _
        return (len(s) % 4 == 0) and re.match('^[A-Za-z0-9\-\_]+[=]{0,2}$', s)

    @classmethod
    def _genKeyPair(cls, ident, kgc, params):
        lts = LongTermSecretKey(params)
        signer = lts.getSigner()
        r_c = signer.getR()

        svSig = kgc.signIdentity(r_c, ident)
        verifier = kgc.getPublicKey().getVerifier(svSig)
        verifier.setHashedR(r_c * svSig.getR())
        assert verifier.verify(ident)

        signer.setHashedR(r_c * svSig.getR())
        mySig = signer.sign(ident)

        return KeyPair.create(params, lts, kgc.getPublicKey(), signer, mySig, svSig)

if __name__ == '__main__':
    unittest.main()
