#!/bin/bash

set -u

brand=$1
fw_file=$2

set_finish_ts(){
    IID=$1
    python3 - <<EOF
import pytz
from datetime import datetime
ts = datetime.now(pytz.utc)
from scripts.psql_firmware import psql
iid=${IID}
psql('UPDATE image SET process_finish_ts=%(ts)s WHERE id=%(iid)s', locals())
EOF
}

echo "<<1>> extract fw_file\n"
python -u scripts/extractor.py -b "${brand}" "${fw_file}" images | tee extraction.log
IID=`cat extraction.log | sed -r 's/.*Database Image ID: ([0-9]+)/\1/;tx;d;:x'`
echo "\$IID = $IID"
python3 - <<EOF
import pytz
from datetime import datetime
ts = datetime.now(pytz.utc)
from scripts.psql_firmware import psql
iid=${IID}
psql('UPDATE image SET process_start_ts=%(ts)s WHERE id=%(iid)s', locals())
EOF
echo "scripts/fw_file_to_psql.py \"$fw_file\" --brand $brand"
scripts/fw_file_to_psql.py "$fw_file" --brand "$brand"
[ -e images/${IID}.tar.gz ] || { echo "images/${IID}.tar.gz doesn't exist. Extraction failed."; 
set_finish_ts $IID; exit 1; }

echo "<<2>> store unpacked file names and hashes\n"
scripts/getArch.sh images/${IID}.tar.gz
arch=$(scripts/psql_firmware.py "SELECT arch FROM image WHERE id=${IID};")
scripts/tar2db_tlsh.py images/${IID}.tar.gz
sudo ./scripts/makeImage.sh ${IID} $arch
sudo chown -R $USER:$USER scratch/${IID}

# infer network
echo "<<2>> infer network config\n"
echo "inferNetwork.sh ${IID}"
scripts/inferNetwork.sh ${IID} $arch
net_infer_OK=$(scripts/psql_firmware.py "SELECT network_inferred FROM image WHERE id=${IID};")
if [ "$net_infer_OK" != "True" ] ; then
    echo "network inferred = False"
    set_finish_ts $IID
    exit 0
fi
echo "<<4>> test network_reachable\n"
# net_reachable
python3 -u scripts/test_network_reachable.py ${IID} test | tee test_network_reachable.log
net_reachable=$(cat test_network_reachable.log | grep "network_reachable=" | grep -ohE 'True|False')
rm test_network_reachable.log
if [ "$net_reachable" != "True" ] ; then
    echo "network_reachable = False"
    set_finish_ts $IID
    exit 0
fi
echo "<<5>> Metasploit and Nmap scan\n"
guest_ip=$(scripts/psql_firmware.py "SELECT guest_ip FROM image WHERE id=${IID}")
scripts/test_network_reachable.py ${IID} construct
while ! ping -c1 $guest_ip &>/dev/null; do :; done
analyses/runExploits.py -i ${IID}
scripts/nmap_scan.py ${IID}
scripts/test_network_reachable.py ${IID} destruct
scripts/merge_metasploit_logs.py ${IID}
set_finish_ts $IID
