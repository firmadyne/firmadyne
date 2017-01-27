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
    echo "Usage: run.armel-debug.sh <image ID>"
    exit 1
fi
IID=${1}

WORK_DIR=`get_scratch ${IID}`
IMAGE=`get_fs ${IID}`
KERNEL=`get_kernel "armel"`

QEMU_AUDIO_DRV=none qemu-system-arm -m 256 -M virt -kernel ${KERNEL} -drive if=none,file=${IMAGE},format=raw,id=rootfs -device virtio-blk-device,drive=rootfs -append "firmadyne.syscall=0 root=/dev/vda1 console=ttyS0 nandsim.parts=64,64,64,64,64,64,64,64,64,64 rdinit=/firmadyne/preInit.sh rw debug ignore_loglevel print-fatal-signals=1 user_debug=31" -nographic -device virtio-net-device,netdev=net1 -netdev socket,listen=:2000,id=net1 -device virtio-net-device,netdev=net2 -netdev socket,listen=:2001,id=net2 -device virtio-net-device,netdev=net3 -netdev socket,listen=:2002,id=net3 -device virtio-net-device,netdev=net4 -netdev socket,listen=:2003,id=net4
