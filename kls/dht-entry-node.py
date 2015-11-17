#!/usr/bin/env python2.7

import click

from dht_provider import DhtProvider
from common import DHT_NODE_PORT


@click.command()
@click.argument('DHT_PORT', required=False, type=click.INT,
                default=DHT_NODE_PORT)
def main(dht_port):
    """
    Launches a DHT entry node that listens on the specified port.
    """

    provider = DhtProvider([], dht_port)
    provider.start(True)

if __name__ == '__main__':
    main()
