from twisted.internet import reactor
import twisted.internet.threads

from entangled.node import EntangledNode
from entangled.kademlia.datastore import DictDataStore
#from entangled.kademlia.datastore import SQLiteDataStore

import sys
import hashlib
import threading

class DhtNode:

    # entry_nodes: array of tuples of form (gethostbyname(addr), int(port))
    def __init__(self, entry_nodes, udp_port):
        self.udp_port = udp_port
        self.entry_nodes = entry_nodes
        self.started = threading.Semaphore(0)

    def start(self, sameThread=False):
        def thread(sameThread):
            # create a local data store
            self.dataStore = DictDataStore()
            #self.dataStore = SQLiteDataStore(
            #    dbFile='/tmp/dbFile%s.db' % self.udp_port)

            self.node = EntangledNode(udpPort=self.udp_port,
                                      dataStore=self.dataStore)

            if len(self.entry_nodes) > 0:
                print "Joining network using entry nodes:",\
                    self.entry_nodes, type(self.entry_nodes[0][0]),\
                    type(self.entry_nodes[0][1])
            else:
                print "Starting network by myself!"

            self.node.joinNetwork(self.entry_nodes)

            print "Running Twisted reactor loop..."
            #print "( sameThread =", sameThread, ")"

            # signal a semaphore when the reactor starts
            reactor.callWhenRunning(
                lambda: self.started.release())

            # Twisted can't install signal handlers when the reactor is
            # started in a different thread
            # TODO: not sure how to install those handlers then, and
            # what's the side-effect of not having them installed
            reactor.run(installSignalHandlers=sameThread)

        if not sameThread:
            import threading
            t = threading.Thread(target=thread, args=(False, ))
            t.start()
        else:
            thread(True)

    def stop(self):
        print "Destroying DHT node..."

        # Wait for the reactor to start before trying to stop it
        self.started.acquire()

        # NOTE: We need to use callFromThread here to stop the reactor
        # because we started it in a different thread
        reactor.callFromThread(
            reactor.stop)
        sys.stdout.flush()

    def OpAsync(self, op, key, value, execFn, errFn=None):
        self._log(op, key, value, "Executing...")

        hkey = hashlib.sha1(key).digest()
        #print "Hashed", key, "to", hkey.encode('hex')

        deferredResult = execFn(op, hkey, value)

        if op == 'Get':
            def successCallback(result):
                if type(result) == dict and hkey in result:
                    self.log_success("Get", key, result[hkey], "OK")
                    return result[hkey]
                else:
                    self.log_fail("Get", key, '', "Key '" + key + "' not found")
                    return None
            successFn = successCallback
        else:
            successFn = lambda *args, **kwargs: self.log_success(
                op, key, value, "OK")

        deferredResult.addCallback(successFn)

        if errFn is None:
            errFn = lambda fail: self.log_fail(op, key, value,
                                               str(fail))

        deferredResult.addErrback(errFn)

        return deferredResult

    def PutAsync(self, key, value):
        return self.OpAsync("Put", key, value, lambda o, k, v:
                            self.node.iterativeStore(k, v))

    def GetAsync(self, key):
        def errCallback(fail):
            self.log_fail("Get", key, '', str(fail))
            return None

        return self.OpAsync("Get", key, "", lambda o, k, v:
                            self.node.iterativeFindValue(k),
                            errCallback)

    def DeleteAsync(self, key):
        return self.OpAsync("Delete", key, "", lambda o, k, v:
                            self.node.iterativeDelete(k))

    def Put(self, key, value):
        result = twisted.internet.threads.blockingCallFromThread(
            reactor,
            lambda: self.PutAsync(key, value))

        return result

    def Get(self, key):
        result = twisted.internet.threads.blockingCallFromThread(
            reactor,
            lambda: self.GetAsync(key))

        return result

    def Delete(self, key):
        result = twisted.internet.threads.blockingCallFromThread(
            reactor,
            lambda: self.DeleteAsync(key))

        return result

    def _log(self, op, key, value, message):
        if op == "Put":
            #print op + "(" + key + ", " + value + "): " + message
            pass
        elif op == "Get" or op == "Delete":
            #print op + "(" + key + "): " + value + " (" + message + ")"
            pass
        else:
            #print "Unknown op: " + op
            pass

    def log_success(self, op, key, value, message):
        self._log(op, key, value, message)
        return True

    def log_fail(self, op, key, value, message):
        self._log(op, key, value, "FAIL: " + message)
        return False

    # destructor, gets called when object is destroyed
    #def __del__(self):
    #    self.stop()


#def parse_entry_nodes(entry_nodes):
#    new_entry_nodes = []
#    for node in entry_nodes:
#        host = node['host']
#        port = int(node['port'])
#        print host, port, type(host), type(port)
#        new_entry_nodes.append((host, port))
#    return new_entry_nodes
