#!/bin/sh

TARGET_IP=$1

snmpwalk -v2c -c public $1 .iso > snmp.public.txt 2>&1
snmpwalk -v2c -c private $1 .iso > snmp.private.txt 2>&1

echo "Dumped to snmp.public.txt and snmp.private.txt!"
