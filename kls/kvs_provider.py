from persistentdict import PersistentDict


class KvsProvider():
    def __init__(self, path):
        self.path = path
        self.store = PersistentDict(path, 'c', format='json')
        print "Current public keys:"
        for k, v in self.store.iteritems():
            print k, "->", v

    def start(self):
        print "Starting KVS provider at '" + self.path + "'"

    def stop(self):
        print "Stopping KVS provider at '" + self.path + "'"

    def get(self, key):
        try:
            val = self.store[key]
            return val
        except KeyError:
            return None

    def put(self, key, value):
        try:
            self.store[key] = value
            self.store.sync()
            return True
        except:
            return False

    #def delete(self, key):
    #    del self.store[key]
    #    self.store.sync()
