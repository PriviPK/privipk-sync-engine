from rpc import rpclib
from common import KGC_PORT

import threading
from charm.core.math.integer import deserialize
from privipk.kgc import Kgc


class KgcRpcServer(rpclib.RpcServer):

    def __init__(self, lts, port=KGC_PORT):
        super(KgcRpcServer, self).__init__(port)
        self.port = port
        self.kgc = Kgc(lts)
        self.heartbeat = 0

    def start(self):
        print "Starting KGC server on port ", self.port

        t = threading.Thread(target=lambda: self.accept_loop())
        t.start()

    def stop(self):
        super(KgcRpcServer, self).stop()

    def rpc_heartbeat(self, beat=None):
        self.heartbeat = self.heartbeat + 1
        return (beat, self.heartbeat)

    def rpc_sign_identity(self, r_c, email, auth_token):
        # TODO: if an exception is thrown here due to bad type of parameters
        # the RPC server might exit?
        # TODO: authenticate request via auth_token (can be proof-of-work based)
        # TODO: serialize exceptions as well so I can throw one here
        r_c = deserialize(r_c)

        if not self.verify_auth_token(email, auth_token):
            #print "ERROR: Token '" + auth_token + "' did not verify for '" +\
            #    email + "'"
            return None

        sig = self.kgc.signIdentity(r_c, email)

        # FIXME: We do our own serialization here, to get around our limited
        # RPC library
        return sig.serialize()

    def rpc_request_auth_token(self, email):
        # TODO: send an auth_token to the email address. later, verify
        # 'rpc_sign_identity' requests against the auth_token
        return "dummy_auth_token"

    def verify_auth_token(self, email, auth_token):
        # TODO: implement
        return auth_token == "dummy_auth_token"
