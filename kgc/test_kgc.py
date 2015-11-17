from server import KgcRpcServer
from client import KgcRpcClient

import privipk
from privipk.schnorr import SchnorrSignature
from privipk.keys import LongTermSecretKey

import unittest


class TestKgc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.params = privipk.parameters.default
        cls.lts = LongTermSecretKey(cls.params)
        cls.kgc_pk = cls.lts.getPublicKey()

        cls.kgc_server = KgcRpcServer(cls.lts)
        cls.kgc_server.start()
        cls.client = KgcRpcClient('localhost')

    @classmethod
    def tearDownClass(cls):
        cls.kgc_server.stop()

    def testHeartbeat(self):
        for i in range(0, 10):
            beat, j = self.client.heartbeat(i * 2)
            self.assertEquals(beat, i * 2)
            self.assertEquals(j, i + 1)

    def testSigning(self):
        # Bob's email and his secret key are set here
        bobEmail = 'bob@wonderbar.com'
        bobSk = LongTermSecretKey(self.params)
        signer = bobSk.getSigner()

        # Bob gets an authentication token from the KGC
        auth_token = self.client.request_auth_token(bobEmail)

        # Bob asks for a KGC signature on his email
        r_c = signer.getR()
        # ...first with a bad token
        self.assertEquals(
            self.client.sign_identity(r_c, bobEmail, 'bad token'),
            None)
        # ...then with the right token
        sig = self.client.sign_identity(r_c, bobEmail, auth_token)
        self.assertIsInstance(sig, SchnorrSignature)

        # Bob verifies the KGC signature
        kgcPk = self.kgc_pk
        verifier = kgcPk.getVerifier(sig)
        verifier.setHashedR(r_c * sig.getR())
        self.assertTrue(verifier.verify(bobEmail))

if __name__ == '__main__':
    unittest.main()
