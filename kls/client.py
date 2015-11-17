from rpc import rpclib

from common import KLS_SERVER_PORT


class KlsRpcClient(object):
    def __init__(self, host, port=KLS_SERVER_PORT):
        self.host = host
        self.port = port

    def heartbeat(self, beat=None):
        with rpclib.client_connect(self.host, self.port) as c:
            return c.call(method='heartbeat', beat=beat)

    # Returns the value for the specified key or the empty string
    def get(self, key):
        with rpclib.client_connect(self.host, self.port) as c:
            return c.call(method='get', key=key)

    # Returns nothing
    def put(self, key, value):
        with rpclib.client_connect(self.host, self.port) as c:
            return c.call(method='put', key=key, value=value)

    # Returns nothing
    def delete(self, key):
        with rpclib.client_connect(self.host, self.port) as c:
            return c.call(method='delete', key=key)
