#!/bin/bash

# How to run:
#    $ docker run --privileged --rm -v $PWD:/work -w /work -it --net=host firmadyne
#    $ /work/example_analysis.sh

set -e
set -x

# Download firmware image
pushd /firmadyne/firmadyne
wget http://www.downloads.netgear.com/files/GDC/WNAP320/WNAP320%20Firmware%20Version%202.0.3.zip
ZIP_FILE="WNAP320 Firmware Version 2.0.3.zip"

python3 ./sources/extractor/extractor.py -b Netgear -sql 127.0.0.1 -np -nk "$ZIP_FILE" images

./scripts/getArch.sh ./images/1.tar.gz
./scripts/tar2db.py -i 1 -f ./images/1.tar.gz

# FIXME: Why does the following command return error status?
set +e
echo "firmadyne" | sudo -SE ./scripts/makeImage.sh 1
set -e

echo "Detecting network configuration"
./scripts/inferNetwork.sh 1

echo "Booting..."
./scratch/1/run.sh
