# Needs to be forwarded if running in a VM, because other DHT nodes running
# need to be able to reach this node. Unless the host's DHT_NODE_PORT is
# forwarded to the guest's (VM) DHT_NODE_PORT, that won't be possible.
DHT_NODE_PORT = 9000

# The KLS can be an external service if it's using a key-value store or it
# can run as VM-local proxy which interacts with the DHT node running
# in the VM. Only the sync-engine code needs to talk to the proxy, so this
# need not be forwarded
KLS_SERVER_PORT = 8999
