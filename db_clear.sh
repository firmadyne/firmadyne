#!/bin/bash
#drop and create firmware db

sudo rm -rf ./images/*.tar.gz
sudo rm -rf ./scratch/*
sudo rm -rf ./dev_log.txt
sudo -u postgres dropdb firmware
sudo -u postgres createdb -O firmadyne firmware
sudo -u postgres psql -d firmware < ./database/schema
clear