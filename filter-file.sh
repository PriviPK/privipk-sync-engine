clear; clear;

set -e

if [ -z "$file" ]; then
    echo "INTERNAL ERROR: Please set the 'file' variable before sourcing this script"
    exit 1
fi

is_vm=0
if hostname | grep "nylas-"; then
    echo "Running inside VM..."
    is_vm=1
    num=`hostname | cut -d'-' -f 2`
else
    if [ $# -lt 1 ]; then
        echo "Usage: `basename $0` [num] [cmd]"
        echo
        echo "When running in the VM, the 'num' argument is deduced."
        echo "When running on the host machine, 'num' must be specified."
        echo "'num' can be either 0 or 1 for now."
        echo
        echo "'cmd' defaults to 'tail -f'. You can replace it with 'cat' for instance."
        exit 1
    fi

    num=$1
    shift

    if [ $num -ne 1 -a $num -ne 0 ]; then
        echo "The 'num' parameter must be either 0 or 1. You gave: $num"
        exit 1
    fi
fi

cmd="tail -f"
if [ $# -gt 0 ]; then
    cmd="$1"
fi

echo -e "\nFiltering file: ${file}-${num}.log ...\n"
${cmd} ${file}-${num}.log | grep -i "ERROR\|quasar\|Exception" --color=always
