#!/bin/bash

set -u

if [ -e ./firmadyne.config ]; then
    source ./firmadyne.config
elif [ -e ../firmadyne.config ]; then
    source ../firmadyne.config
else
    echo "Error: Could not find 'firmadyne.config'!"
    exit 1
fi

if [ $# -ne 1 ]; then
    echo "Usage: $0 <image ID>"
    exit 1
fi

IID=${1}
WORK_DIR=`get_scratch ${IID}`

#Nmap options to use for scanning:
NMAP_OPTS="-v -n -sSV"

if ! which nmap > /dev/null; then
    echo "[-] missing nmap binary"
    exit 1
fi

if ! [ -d ${WORK_DIR} ]; then
    echo "[-] missing working directory of image ID ${IID}"
    exit 1
fi

if ! [ -f ${WORK_DIR}/run.sh ]; then
    echo "[-] missing start script (run.sh) of image ID ${IID}"
    exit 1
fi

TARGET_IP=`grep "GUESTIP=" "${WORK_DIR}"/run.sh | cut -d= -f2`

if [ -z "${TARGET_IP}" ]; then
    echo "[-] Found no target IP address ..."
    exit 1
fi

echo "[+] Found IP: ${TARGET_IP}"

sudo nmap ${NMAP_OPTS} "${TARGET_IP}" -oA "$WORK_DIR"nmap-basic-tcp | tee "${WORK_DIR}"nmap-basic-tcp.txt 2>&1

echo -e "\nDumped Nmap scan details of ${TARGET_IP} to $WORK_DIR"


