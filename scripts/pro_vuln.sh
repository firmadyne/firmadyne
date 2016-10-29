#!/usr/bin/env bash

set -u

IIDS=$(scripts/psql_firmware.py "SELECT id FROM image WHERE network_reachable=True AND (vulns IS NULL OR ARRAY_LENGTH(vulns,1)=0) ORDER BY id")
for IID in $IIDS ; do
    # net_reachable
    python3 -u scripts/test_network_reachable.py ${IID} test | tee test_network_reachable.log
    net_reachable=$(cat test_network_reachable.log | grep "network_reachable=" | grep -ohE 'True|False')
    rm test_network_reachable.log
    if [ "$net_reachable" == "False" ] ; then
        continue
    fi

    scripts/test_network_reachable.py $IID construct
    guest_ip=$(scripts/psql_firmware.py "SELECT guest_ip FROM image WHERE id=$IID;")
    while ! ping -c1 $guest_ip &>/dev/null ;  do  :; done
    analyses/runExploits.py -i $IID
    scripts/test_network_reachable.py $IID destruct
    scripts/merge_metasploit_logs.py $IID
done

