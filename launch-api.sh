#!/bin/bash

set -e

. env.sh

which unbuffer || { echo "ERROR: Install 'unbuffer' please"; exit 1; }

num=`hostname | cut -d'-' -f 2`
port=$((5555+$num))

set -o pipefail

clear; clear;
echo -e "\nListening on port $port...\n"

unbuffer bin/inbox-api --port $port $@ 2>&1 | tee "api-${num}.log"
