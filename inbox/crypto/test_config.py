import privipk
from privipk.keys import LongTermPublicKey

import os
import unittest


class ConfigTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def testHasKgcPublicKey(self):
        self._testHasKgcPublicKey('test')
        self._testHasKgcPublicKey('dev')

    def _testHasKgcPublicKey(self, env):
        os.environ['INBOX_ENV'] = env
        from inbox.config import config
        pkstr = config.get_required('KGC_PUBLIC_KEY')
        LongTermPublicKey.unserialize(privipk.parameters.default, pkstr)

    def testEtcHosts(self):
        f = open('/etc/hosts', 'r')
        lines = f.read().split('\n')

        def hasEntry(entry):
            for line in lines:
                if entry in line:
                    return True
            return False

        for entry in ['kls', 'kgc']:
            if not hasEntry(entry):
                raise LookupError("You need to have a '" + entry +
                    "' entry in /etc/hosts")

if __name__ == '__main__':
    os.environ['INBOX_ENV'] = 'test'
    unittest.main()
