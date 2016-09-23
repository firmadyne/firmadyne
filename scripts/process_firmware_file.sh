#!/bin/bash

set -u

brand=$1
fw_file=$2

## IID=$(sources/extractor/extractor.py -b "${brand}" -sql 127.0.0.1 -np -nk "${fw_file}" images | tee /dev/tty | grep  -E 'Database Image ID:' | grep -o -E '[0-9]+')
sources/extractor/extractor.py -b "${brand}" -sql 127.0.0.1 -np -nk "${fw_file}" images
IID=$(scripts/psql_firmware.py "SELECT MAX(id) FROM image")
extract_OK=$(scripts/psql_firmware.py "SELECT rootfs_extracted FROM image WHERE id=${IID};")
if [ "$extract_OK" == "False" ] ; then
    exit 0
fi

scripts/getArch.sh images/${IID}.tar.gz
arch=$(scripts/psql_firmware.py "SELECT arch FROM image WHERE id=${IID};")
scripts/tar2db_tlsh.py images/${IID}.tar.gz
# scripts/tar2db.py -i ${IID} -f images/${IID}.tar.gz
sudo ./scripts/makeImage.sh ${IID} $arch
echo "inferNetwork.sh ${IID}"
scripts/inferNetwork.sh ${IID} $arch
net_infer_OK=$(scripts/psql_firmware.py "SELECT network_inferred FROM image WHERE id=${IID};")
if [ "$net_infer_OK" == "False" ] ; then
    exit 0
fi
scripts/test_network_reachable.py ${IID}
