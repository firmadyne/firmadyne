#!/bin/bash
file=$1
args=$2
expect -c "
set timeout 600
spawn ${file} ${args}
expect \"firmadyne: \"
    send \"firmadyne\r\"
interact"