from rpc import rpclib

from common import KLS_SERVER_PORT

import sys
import threading


class KlsRpcServer(rpclib.RpcServer):
    def __init__(self, provider, port=KLS_SERVER_PORT):
        super(KlsRpcServer, self).__init__(port)
        self.provider = provider
        self.heartbeat = 0

    def start(self):
        self.provider.start()

        print "Starting KLS RPC server accept loop on port", self.port

        t = threading.Thread(target=lambda: self.accept_loop())
        t.start()

    def stop(self):
        super(KlsRpcServer, self).stop()
        self.provider.stop()

    def rpc_heartbeat(self, beat=None):
        self.heartbeat = self.heartbeat + 1
        return (beat, self.heartbeat)

    def rpc_get(self, key):
        try:
            if not isinstance(key, str):
                raise TypeError(
                    "Expected a string in Get, got a " + str(type(key)))

            return self.provider.get(key)
        except:
            print "Unexpected exception:", sys.exc_info()[0]
            return None

    def rpc_put(self, key, value):
        try:
            if not isinstance(key, str):
                raise TypeError(
                    "Expected key in Put to be a string. " + "Got a " +
                    str(type(key)))

            if not isinstance(value, str):
                raise TypeError(
                    "Expected value in Put to be a string. " + "Got a " +
                    str(type(value)))

            return self.provider.put(key, value)
        except:
            print "Unexpected exception:", sys.exc_info()[0]
            return None

    #def rpc_delete(self, key):
    #    return self.provider.delete(key)
