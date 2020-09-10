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
    echo "Usage: mount.sh <image ID>"
    exit 1
fi
IID=${1}

if check_root; then
    echo "Error: This script requires root privileges!"
    exit 1
fi

echo "----Running----"
WORK_DIR=`get_scratch ${IID}`
IMAGE=`get_fs ${IID}`
IMAGE_DIR=`get_fs_mount ${IID}`

echo "----Adding Device File----"
DEVICE=$(get_device "$(kpartx -a -s -v "${IMAGE}")")
sleep 1

if [ ! -e "${IMAGE_DIR}" ]
then
    echo "----Making image directory ${IMAGE_DIR}----"
    mkdir "${IMAGE_DIR}"
fi

echo "----Mounting ${DEVICE}----"
#sudo /bin/mount /dev/nbd0p1 "${IMAGE_DIR}"
mount "${DEVICE}" "${IMAGE_DIR}"

echo "----Mounted at ${IMAGE_DIR}----"
