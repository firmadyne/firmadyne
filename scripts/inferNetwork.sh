#!/bin/bash

set -e
set -u

if [ -e ./firmadyne.config ]; then
    source ./firmadyne.config
elif [ -e ../firmadyne.config ]; then
    source ../firmadyne.config
else
    echo "Error: Could not find 'firmadyne.config'!"
    exit 1
fi

if check_number $1; then
    echo "Usage: inferNetwork.sh <image ID> [<architecture>]"
    exit 1
fi
IID=${1}

if [ $# -gt 1 ]; then
    if check_arch "${2}"; then
        echo "Error: Invalid architecture!"
        exit 1
    fi

    ARCH=${2}
else
    echo -n "Querying database for architecture... "
    ARCH=$(python ./scripts/psql_firmware.py "SELECT arch from image WHERE id=${1};")
    ARCH="${ARCH#"${ARCH%%[![:space:]]*}"}"
    echo "${ARCH}"
    if [ -z "${ARCH}" ]; then
        echo "Error: Unable to lookup architecture. Please specify {armel,mipseb,mipsel} as the second argument!"
        exit 1
    fi
fi

echo "Running firmware ${IID}: terminating after 60 secs..."
# timeout --preserve-status --signal SIGINT 60 "${SCRIPT_DIR}/run.${ARCH}.sh" "${IID}"
"${SCRIPT_DIR}/run.${ARCH}.sh" "${IID}" &
WORK_DIR=`get_scratch ${IID}`
# echo "\$ARCH = $ARCH, \$WORK_DIR=$WORK_DIR"
sleep 3
echo 'wait for inet_insert_ifa'
python3 scripts/wait_for_inet_insert_ifa.py ${WORK_DIR}/qemu.initial.serial.log --timeout 30 --archend ${ARCH}
QEMU=`get_qemu ${ARCH}`
# echo "\$QEMU = $QEMU"
killall ${QEMU} # qemu-system-mipsel
sleep 1

echo "Inferring network..."
"${SCRIPT_DIR}/makeNetwork.py" -i "${IID}" -q -o -a "${ARCH}" -S "${SCRATCH_DIR}"

echo "Done!"
