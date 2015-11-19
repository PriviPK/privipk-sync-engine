set -e

echo "Note: This script is to be run inside the VM"

[ -d /vagrant ] || { echo "ERROR: You are not in the VM!"; exit 1; }

if [ ! -f libprivipk/src/setup.py ]; then
    git clone https://github.com/PriviPK/libprivipk.git
fi

cd libprivipk/
./install-deps.sh

cd src/
python setup.py install
./run-tests.sh
