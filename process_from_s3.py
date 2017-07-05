#!/usr/bin/env python3
# -*- coding: utf8 -*-
import boto
import os
import traceback
import time
from datetime import datetime
from urllib import parse
import hashlib
import psycopg2
from scripts.psql_firmware import psql


def getFileMd5(fileName):
    with open(fileName, mode='rb') as fin:
        return hashlib.md5(fin.read()).hexdigest()


def getBucketMd5(buck, obj):
    return buck.get_key(obj.key).etag[1:-1]


def main():
    try:
        conn = boto.connect_s3()
        buck = conn.get_bucket('grid-iot-firmware-harvest')
        for obj in buck.list('fw_files/D-Link/'):
            os.system(
                'python3 -u scripts/process_firmware_file.py "D-Link" "%s"' %
                ('s3://grid-iot-firmware-harvest/'+obj.key))
            try:
                os.remove(os.path.basename(parse.urlsplit(obj.key).path))
            except:
                pass
    except BaseException as ex:
        traceback.print_exc()


if __name__ == '__main__':
    main()
