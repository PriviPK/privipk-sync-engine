"""
    RPC code was copied and slightly modified from 6.858 Fall 2014
"""

import socket
import errno
import time
import json
import yaml
import traceback
import threading


def parse_req(req):
    #return json.loads(req)
    # JSON decodes ASCII strings as Unicode, so will use this to get around it
    return yaml.safe_load(req)


def format_req(method, kwargs):
    return json.dumps([method, kwargs])


def parse_resp(resp):
    #return json.loads(resp)
    # JSON decodes ASCII strings as Unicode, so will use this to get around it
    return yaml.safe_load(resp)


def format_resp(resp):
    return json.dumps(resp)


def buffered_readlines(sock):
    buf = ''
    while True:
        while '\n' in buf:
            (line, nl, buf) = buf.partition('\n')
            yield line
        try:
            newdata = sock.recv(4096)
            if newdata == '':
                break
            buf += newdata
        except IOError, e:
            print "ERROR: Connection reset"
            if e.errno == errno.ECONNRESET:
                break


class RpcServer(object):

    def __init__(self, port=9000):
        self.port = port
        self.started = threading.Semaphore(0)

    def run_sock(self, sock):
        lines = buffered_readlines(sock)
        for req in lines:
            (method, kwargs) = parse_req(req)
            m = self.__getattribute__('rpc_' + method)
            ret = m(**kwargs)
            sock.sendall(format_resp(ret) + '\n')

    def accept_loop(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('', self.port))

        self.server.listen(128)
        self.started.release()
        #print "Waiting for connections on port", self.port
        try:
            self.server.settimeout(1)
        except:
            # we assume an exception here happened because the stop() method
            # closed the socket
            pass

        while True:
            try:
                conn, addr = self.server.accept()
            except socket.timeout:
                # we use timeouts to make sure accept() exits after a while
                # otherwise, I don't know of (easier) ways to interrupt
                # the accept() call from the stop() method
                continue
            except socket.error:
                # an error will be thrown when we close the server socket
                # in the stop() method and we catch it here and break out
                # of the server loop
                break

            conn.settimeout(None)
            try:
                self.run_sock(conn)
            except:
                print "Exception was thrown:", traceback.format_exc()
                break
            finally:
                conn.close()

        #print "Exited RPC server's accept loop on port", self.port
        self.server.close()

    def stop(self):
        #print "Forcefully closing RPC server socket on port", self.port
        self.started.acquire()
        # NOTE: need to make sure self.server is set before calling close =>
        # use a semaphore
        self.server.close()


class RpcClient(object):

    def __init__(self, sock):
        self.sock = sock
        self.lines = buffered_readlines(sock)

    def call(self, method, **kwargs):
        self.sock.sendall(format_req(method, kwargs) + '\n')
        return parse_resp(self.lines.next())

    def close(self):
        self.sock.close()

    # __enter__ and __exit__ make it possible to use RpcClient()
    # in a "with" statement, so that it's automatically closed.
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def client_connect(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Our testing code will sometimes connect __too fast__ to the
    # server, so we retry here a few times in case the server hasn't
    # started listening yet
    milli = 10
    for _ in range(0, 5):
        try:
            #print "Trying to connect to", host, port
            sock.connect((host, port))
            return RpcClient(sock)
        except:
            time.sleep(milli / 1000.0)
            milli = milli * 2

    raise IOError("Could not connect to " + str(host) + ":" + str(port))
