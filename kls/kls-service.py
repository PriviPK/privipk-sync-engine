#!/usr/bin/env python2.7

import time
import click
from socket import gethostbyname

from client import KlsRpcClient
from server import KlsRpcServer
from common import KLS_SERVER_PORT, DHT_NODE_PORT
from kvs_provider import KvsProvider
from dht_provider import DhtProvider


@click.group()
def cli():
    """
    This tool can be used to create the KLS service. The 'kvs' command
    creates a centralized KLS service that can be ran outside the user's
    client machines. The 'dht' command creates a decentralized KLS
    service based on DHTs. The KLS service should be launched locally
    as it behaves more like a trusted proxy when using the 'dht' mode.
    """
    pass


@cli.command()
@click.argument('entry_node_host', required=True, type=click.STRING)
@click.argument('entry_node_port', required=True, type=click.INT)
@click.option('--extra-node', '-n', type=click.Tuple([unicode, int]),
              multiple=True, metavar='HOST PORT',
              help='Extra entry node in HOST PORT format. Can specify multiple times.')
@click.option('--port', '-p', required=False, type=click.INT,
              default=KLS_SERVER_PORT,
              help='TCP port for the KLS proxy to listen on.')
@click.option('--dht-port', required=False, type=click.INT,
              default=DHT_NODE_PORT,
              help='UDP port for the DHT node to listen on.')
def dht(entry_node_host, entry_node_port, extra_node, port, dht_port):
    """
    Spawns a KLS proxy that talks to a DHT. Email users run the
    KLS proxy locally and trust it to correctly query the DHT
    network. At least one DHT entry node must be specified. The
    entry node can be launched using the ./dht-entry-node.py script.
    """
    entry_nodes = []

    if entry_node_host is not None:
        h = gethostbyname(entry_node_host)
        p = entry_node_port
        entry_nodes.append((h, p))

    #print 'Num extra node(s):', len(extra_node)
    if extra_node is not None:
        parsed_nodes = [(gethostbyname(x[0]), x[1]) for x in extra_node]
        entry_nodes.extend(parsed_nodes)
    #else:
    #    print 'No extra nodes.'

    #print 'Entry node(s):', entry_nodes

    provider = DhtProvider(entry_nodes, dht_port)
    server = KlsRpcServer(provider, port)
    server.start()

    testDht(port)


@cli.command()
@click.argument('path', required=False, default='/tmp/kvstore.json')
def kvs(path):
    """
    Spawns a KLS service backed by a key-value store.
    """
    provider = KvsProvider(path)
    server = KlsRpcServer(provider)
    server.start()


def testDht(port):
    time.sleep(1)
    client = KlsRpcClient('localhost', port)
    count = client.get('count')
    count = count if count is not None else '0'
    count = str(int(count) + 1)
    client.put('count', count)
    print "Updated count to", count


if __name__ == '__main__':
    cli()
