# Table of Contents

- [Introduction](#introduction)
- [Setup](#setup)
- [Usage](#usage)
  - [pp_main.sh](#pp_main.sh)
  - [autoGenrun.py](#autoGenrun.py)
  - [autoExtract.py](#autoExtract.py)


#Introduction

There is two automated scripts.
1. `pp_main.sh`
2. `autoGenrun.py`

#Setup

First, these automated scripts require `expect` library.
So, we need to install `expect` library with `sudo apt install expect` command.
Also, The database should set ID=`firmadyne`, PASSWORD=`firmadyne` as instruction of README.md.

#Usage

This automated scripts require all firmware images in directory which named vendor's name.(optional)
Also, These scripts extracts `-np -nk -sql 127.0.0.1` mode.

##pp_main.sh
- coded by 3ncag3
1. `sudo bash ./scripts/pp_main.sh {firmwareDirectory}`
* firmwareDirectory should be given rel path of firmadyne directory.
* You can change timeout period by change `timeout` in pp_main.sh.(default is 600 seconds per image)
* This script will generate `dev_log.txt` and `timeout_log.txt` files which contain list of visited file and timeouted file.(Recommend run firmadyne manually on timeout_log.txt file)


##autoGenrun.py
- coded by nodapCoder
1. `sudo python ./scripts/autoGenrun.py` will automatically generate run.sh of every firmware image if possible. 
* This script will generate `visited.txt` and `success.txt` which contain list of visited file and successfully generated run.sh files.
* Note that this script does not have timeout functionality.(But, pp_main.sh have timeout functinality.)

##autoExtract.py
- coded by nodapCoder
This program will extract all firmware images in this directory.
There is three options whcih can run auto/non-auto mode.(Default is auto mode)
1. `python ./scripts/autoExtract.py` will automatically extract every firmware image if possible.
* This program does not have timeout functionality.

