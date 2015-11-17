#!/usr/bin/env python2.7

import click
from common import KGC_PORT
from server import KgcRpcServer
import privipk
from privipk.keys import LongTermSecretKey


@click.group()
def cli():
    """
    Use this tool to spawn a KGC server and/or to generate
    a private key for a KGC server.
    """
    pass


@cli.command()
@click.option('--port', '-p', required=False, metavar='PORT', default=KGC_PORT,
               help='TCP port for the KGC to listen on.')
@click.argument('secret_key_path', required=True)
@click.argument('group_params_path', required=False)
def start(port, secret_key_path, group_params_path):
    """
    Starts a KGC server. Loads the private key from the specified file.
    Setting the group parameters is not yet implemented
    """
    params = privipk.parameters.default
    lts = LongTermSecretKey.unserialize(params, open(secret_key_path).read())
    server = KgcRpcServer(lts, port)
    server.start()


@cli.command()
@click.argument('secret_key_path', required=True)
def genkey(secret_key_path):
    """
    Generates a private key and stores it in the specified file. Also
    stores the public key in the another file named by appending .pub
    to the first file.
    """
    params = privipk.parameters.default
    lts = LongTermSecretKey(params)
    open(secret_key_path, 'w').write(lts.serialize())
    ltp = lts.getPublicKey()
    open(secret_key_path + '.pub', 'w').write(ltp.serialize())

if __name__ == '__main__':
    cli()
