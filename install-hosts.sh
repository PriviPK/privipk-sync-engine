#!/bin/bash

if [ $UID -ne 0 ]; then
    echo "ERROR: Must be run as root"
    exit 1
fi

# assume the KLS and KGC run on the host machine (for testing)
if ! grep kls /etc/hosts >/dev/null; then
    echo -e "192.168.10.1\tkls" >>/etc/hosts
fi

if ! grep kgc /etc/hosts >/dev/null; then
    echo -e "192.168.10.1\tkgc" >>/etc/hosts
fi
