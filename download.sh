#!/bin/sh

set -e

download(){
 wget -N --continue -P./binaries/ $*
}

echo "Downloading binaries..."

echo "Downloading kernel 2.6 (MIPS)..."
download https://github.com/firmadyne/kernel-v2.6/releases/download/v1.1/vmlinux.mipsel
download https://github.com/firmadyne/kernel-v2.6/releases/download/v1.1/vmlinux.mipseb

echo "Downloading kernel 4.1 (ARM)..."
download https://github.com/firmadyne/kernel-v4.1/releases/download/v1.1/zImage.armel

echo "Downloading console..."
download https://github.com/firmadyne/console/releases/download/v1.0/console.armel
download https://github.com/firmadyne/console/releases/download/v1.0/console.mipseb
download https://github.com/firmadyne/console/releases/download/v1.0/console.mipsel

echo "Downloading libnvram..."
download https://github.com/firmadyne/libnvram/releases/download/v1.0c/libnvram.so.armel
download https://github.com/firmadyne/libnvram/releases/download/v1.0c/libnvram.so.mipseb
download https://github.com/firmadyne/libnvram/releases/download/v1.0c/libnvram.so.mipsel

echo "Done!"
