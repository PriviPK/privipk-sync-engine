#!/bin/bash

scriptdir=$(readlink -f $(dirname $BASH_SOURCE))

export PYTHONPATH="$scriptdir"
echo "Set \$PYTHONPATH to $PYTHONPATH..."
