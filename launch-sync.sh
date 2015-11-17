#!/bin/bash

set -e

. env.sh

which unbuffer || { echo "ERROR: Install 'unbuffer' please"; exit 1; }

num=`hostname | cut -d'-' -f 2`

set -o pipefail

clear; clear;
unbuffer bin/inbox-start 2>&1 | tee "sync-${num}.log"
