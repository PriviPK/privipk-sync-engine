dirs="rpc/ kls/ kgc/ inbox/crypto"

for f in `find $dirs -name "test_*.py"`; do
    echo
    echo " * Running test in '$f' ..."
    echo
    python $f
done
