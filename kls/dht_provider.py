from dht_node import DhtNode
from common import DHT_NODE_PORT


class DhtProvider():
    def __init__(self, entry_nodes=[], dht_node_port=DHT_NODE_PORT):
        self.entry_nodes = entry_nodes
        self.dht_port = dht_node_port

        self.node = DhtNode(self.entry_nodes, self.dht_port)

    def start(self, sameThread=False):
        print "Starting DHT node at port", self.dht_port
        self.node.start(sameThread)

    def stop(self):
        print "Stopping DHT node at port", self.dht_port
        self.node.stop()

    def get(self, key):
        value = self.node.Get(key)
        #print "Get(", key, ") returned:", value
        return value

    def put(self, key, value):
        ret = self.node.Put(key, value)
        #print "Put(", key, ",", value, ") returned:", ret
        return ret

    #def delete(self, key):
    #    ret = self.node.Delete(key)
    #    print "Delete returned:", ret
