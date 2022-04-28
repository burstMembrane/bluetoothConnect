#!/usr/bin/bash
# install lib-bluetooth
sudo apt install libbluetooth-dev -y
# get the tar from pyblues
wget -c https://github.com/pybluez/pybluez/archive/master.tar.gz -O - | tar -xz
# untar
tar -xf master.tar.gz
cd pybluez-master
# install
sudo python setup.py install

PYCMD=$(cat <<EOF
try:
    import bluetooth
    print("Successfully imported the bluetooth module")
except ModuleNotFoundError as e:
    print(e)
    print("Couldn't import the bluetooth module...")
EOF
)
python3 -c "$PYCMD"

# remove source dir
sudo rm -rf pybluez-master
