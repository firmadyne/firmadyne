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

function getArch() {
    if (echo ${FILETYPE} | grep -q "MIPS64")
    then
        ARCH="mips64"
    elif (echo ${FILETYPE} | grep -q "MIPS")
    then
        ARCH="mips"
    elif (echo ${FILETYPE} | grep -q "ARM64")
    then
        ARCH="arm64"
    elif (echo ${FILETYPE} | grep -q "ARM")
    then
        ARCH="arm"
    elif (echo ${FILETYPE} | grep -q "Intel 80386")
    then
        ARCH="intel"
    elif (echo ${FILETYPE} | grep -q "x86-64")
    then
        ARCH="intel64"
    elif (echo ${FILETYPE} | grep -q "PowerPC")
    then
        ARCH="ppc"
    else
        ARCH=""
    fi
}

function getEndian() {
    if (echo ${FILETYPE} | grep -q "LSB")
    then
        END="el"
    elif (echo ${FILETYPE} | grep -q "MSB")
    then
        END="eb"
    else
        END=""
    fi
}

INFILE=${1}
BASE=$(basename "$1")
IID=${BASE%.tar.gz}

mkdir -p "/tmp/${IID}"

FILES="$(tar -tf $INFILE | grep -e "/busybox\$") "
FILES+="$(tar -tf $INFILE | grep -E "/sbin/[[:alpha:]]+")"
for TARGET in ${FILES}
do
    SKIP=$(echo "${TARGET}" | fgrep -o / | wc -l)
    tar -xf "${INFILE}" -C "/tmp/${IID}/" --strip-components=${SKIP} ${TARGET}
    TARGETLOC="/tmp/$IID/${TARGET##*/}"

    if [ -h ${TARGETLOC} ] || [ ! -f ${TARGETLOC} ]
    then
        continue
    fi

    FILETYPE=$(file ${TARGETLOC})

    echo -n "${TARGET}: "
    getArch
    getEndian

    if [ -n "${ARCH}" ] && [ -n "${END}" ]
    then
        ARCHEND=${ARCH}${END}
        echo ${ARCHEND}

        psql -d firmware -U firmadyne -h 127.0.0.1 -q -c "UPDATE image SET arch = '$ARCHEND' WHERE id = $IID;"

        rm -fr "/tmp/${IID}"
        exit 0
    else
        echo -n ${ARCH}
        echo ${END}
    fi
done

rm -fr "/tmp/${IID}"

exit 1
