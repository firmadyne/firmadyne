#!/bin/bash

tail -n +2484 ftp.dlink.eu/s3.txt | while read line
do
  echo "$line"; date +'%Y-%m-%d %H:%M:%S'; aws s3 cp "s3://grid-iot-firmware-harvest/fw_files/D-Link/ftp.dlink.eu/$line" "$line" --region us-west-1 ; scripts/process_firmware_file.sh "D-Link" "$line" ; rm "$line";
done

