#!/bin/bash
S3BUCKET=s3://grid-iot-firmware-harvest/fw_files/netgear/downloadcenter.netgear.com/


for fname in `aws s3 ls $S3BUCKET | awk '{$1=$2=$3=""; print $0}' | sed 's/^[ \t]*//' ` ; do
    echo "$fname"
    date +'%Y-%m-%d %H:%M:%S';
    aws s3 cp  "${S3BUCKET}$fname" "$fname" --region us-west-1
    scripts/process_firmware_file.sh "Netgear" "$fname"
    rm "$fname"
done

