from rpc import rpclib
from common import KGC_PORT

from charm.core.math.integer import integer, serialize
from privipk.schnorr import SchnorrSignature


class KgcRpcClient(object):
    def __init__(self, host, port=KGC_PORT):
        self.host = host
        self.port = port

    def heartbeat(self, beat=None):
        with rpclib.client_connect(self.host, self.port) as c:
            return c.call(method='heartbeat', beat=beat)

    def sign_identity(self, r_c, email, auth_token):
        # FIXME: make serialization transparent
        # serialize r_c first because it's a custom type implemented
        # in the Charm Crypto library
        assert isinstance(r_c, integer)
        r_c = serialize(r_c)

        with rpclib.client_connect(self.host, self.port) as c:
            sigstr = c.call(method='sign_identity', email=email, r_c=r_c,
                            auth_token=auth_token)
            if sigstr is None:
                return None
            else:
                return SchnorrSignature.unserialize(sigstr)

    def request_auth_token(self, email):
        with rpclib.client_connect(self.host, self.port) as c:
            return c.call(method='request_auth_token', email=email)
