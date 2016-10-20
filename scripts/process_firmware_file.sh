#!/bin/bash

set -u

brand=$1
fw_file=$2

python -u sources/extractor/extractor.py -b "${brand}" -sql 127.0.0.1 -np -nk "${fw_file}" images | tee extraction.log
IID=`cat extraction.log | sed -r 's/.*Database Image ID: ([0-9]+)/\1/;tx;d;:x'`
rm extraction.log
echo "\$IID = $IID"
echo "scripts/fw_file_to_psql.py \"$fw_file\" --brand $brand"
scripts/fw_file_to_psql.py "$fw_file" --brand $brand
[ -e images/${IID}.tar.gz ] || { echo "images/${IID}.tar.gz doesn't exist. Extraction failed."; exit 1; }

scripts/getArch.sh images/${IID}.tar.gz
arch=$(scripts/psql_firmware.py "SELECT arch FROM image WHERE id=${IID};")
scripts/tar2db_tlsh.py images/${IID}.tar.gz
sudo ./scripts/makeImage.sh ${IID} $arch
# infer network
echo "inferNetwork.sh ${IID}"
scripts/inferNetwork.sh ${IID} $arch
net_infer_OK=$(scripts/psql_firmware.py "SELECT network_inferred FROM image WHERE id=${IID};")
if [ "$net_infer_OK" == "False" ] ; then
    exit 0
fi
# net_reachable
python3 -u scripts/test_network_reachable.py ${IID} test | tee test_network_reachable.log
net_reachable=$(cat test_network_reachable.log | grep "network_reachable=" | grep -ohE 'True|False')
rm test_network_reachable.log
if [ "$net_reachable" == "False" ] ; then
    exit 0
fi
guest_ip=$(scripts/psql_firmware.py "SELECT guest_ip FROM image WHERE id=${IID}")
scripts/test_network_reachable.py ${IID} construct
while ! ping -c1 $guest_ip &>/dev/null; do :; done
analyses/runExploits.py -i ${IID}
scripts/test_network_reachable.py ${IID} destruct
scripts/merge_metasploit_logs.py ${IID}
