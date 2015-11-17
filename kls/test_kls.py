from kvs_provider import KvsProvider
from dht_provider import DhtProvider
from server import KlsRpcServer
from client import KlsRpcClient

import errno
import os
import unittest


class KlsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        path = '/tmp/test_kvstore.json'
        try:
            os.remove(path)
        except OSError, e:
            if e.errno != errno.ENOENT:
                raise

        cls.kvs_server = KlsRpcServer(KvsProvider(path), 9001)
        cls.kvs_server.start()
        cls.kvs_client = KlsRpcClient('localhost', 9001)

        cls.dht_server = KlsRpcServer(DhtProvider(dht_node_port=4500), 9002)
        cls.dht_server.start()
        cls.dht_client = KlsRpcClient('localhost', 9002)

    @classmethod
    def tearDownClass(cls):
        cls.kvs_server.stop()
        cls.dht_server.stop()

    def testHeartbeat(self):
        for client in [self.kvs_client, self.dht_client]:
            for i in range(0, 10):
                beat, j = client.heartbeat(i * 2)
                self.assertEquals(beat, i * 2)
                self.assertEquals(j, i + 1)

    # NOTE: the key-value store starts out empty
    def testKvs(self):
        client = KlsRpcClient('localhost', 9001)
        self._testKls(client)

    def testDht(self):
        client = KlsRpcClient('localhost', 9002)
        self._testKls(client)

    def _testKls(self, client):
        self.assertEqual(client.get('a'), None)

        client.put('a', 'val1')
        a = client.get('a')
        self.assertEqual(a, 'val1')

        client.put('b', 'val2')
        b = client.get('b')
        self.assertEqual(b, 'val2')

        for i in range(0, 10):
            a = a + ',' + str(i)
            client.put('a', a)
            self.assertEqual(client.get('a'), a)

            b = b + ',' + str(i)
            client.put('b', b)
            self.assertEqual(client.get('b'), b)


if __name__ == '__main__':
    unittest.main()
