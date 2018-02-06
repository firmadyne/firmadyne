#!/bin/bash
#pre-processing script for executing run.sh easliy

directory=$1

images_dir="./images"
scratch_dir="./scratch"
analyzed_entries=()
log_file="./dev_log.txt"
timeout_log="./timeout_log.txt"

if [ -z ${directory} ];then
	echo "usage : ./pp_script.sh [firmware_directory]"
	exit 0
fi

if ! type expect &>/dev/null; then
  echo "Please install 'expect' first, using 'sudo apt-get install expect'"
  exit 0
fi

if [ "$EUID" -ne 0 ]
  then echo "Please run as root using 'sudo ./pp_main.sh [firmware_directory]"
  exit 0
fi

while IFS= read -r line
do
	analyzed_entries+=("$line")
done <"$log_file"

for entry in "./"${directory}/*

do
	if [[ " ${analyzed_entries[*]} " == *" $entry "* ]]; then
		echo -e "\n\n----------------------------------------------------"
    	echo "Already analyzed $entry! continue..."
    	echo -e "----------------------------------------------------\n\n"
    	continue
	fi

	echo -e "\nPreparing for analyzing firmware named \"$entry\"\n"

	echo "executing extractor..."
	start=`date +%s`
	timeout 600 sh -c "./sources/extractor/extractor.py -b ${directory} -sql 127.0.0.1 -np -nk \"$entry\" images"
	end=`date +%s`

	runtime=$((end-start))
	if [ "$runtime" -gt 298 ]
		then echo -e '\nWell, it takes too long.... I have to check it later.\n'
		echo $entry >> $timeout_log
		continue
	fi

	count_query=$(sh -c "PGPASSWORD=firmadyne psql -U firmadyne -d firmware -h 127.0.0.1 -c 'Select count(*) from image'")
	query_array=(${count_query// / })
	tar_count=${query_array[2]}

	if [ ! -f ./images/${tar_count}.tar.gz ]; then
		echo -e "\n\n----------------------------------------------------"
		echo "No such file named ${tar_count}.tar.gz was found..."
		echo "Extraction failed... skip that"
		echo -e "----------------------------------------------------\n\n\n\n"
		echo $entry >> $log_file
		continue
	fi

	echo "executing getArch..."
	expect -c "
	set timeout 4
	spawn ./scripts/getArch.sh ./images/${tar_count}.tar.gz
	expect 'firmadyne:'
		send \"firmadyne\r\"
	interact"
	
	echo "executing tar2db..."
	./scripts/tar2db.py -i ${tar_count} -f ./images/${tar_count}.tar.gz

	echo "executing makeImage..."
	expect -c "
	set timeout 4
	spawn ./scripts/makeImage.sh ${tar_count}
	expect 'firmadyne:'
		send \"firmadyne\r\"
	interact"
	
	echo "executing inferNetwork..."
	expect -c "
	set timeout 4
	spawn ./scripts/inferNetwork.sh ${tar_count}
	expect 'firmadyne:'
		send \"firmadyne\r\"
	expect 'anyway'
		send \"y\r\"
	interact"

	echo $entry >> $log_file
	let tar_count=tar_count+1
	
done

