#!/usr/bin/env python3
# -*- coding: utf8 -*-
import boto
import os
import traceback
import time
from datetime import datetime 
import hashlib
import psycopg2
from scripts.psql_firmware import psql


def getFileMd5(fileName):
    with open(fileName,mode='rb') as fin:
        return hashlib.md5(fin.read()).hexdigest()

def getBucketMd5(buck, obj):
    return buck.get_key(obj.key).etag[1:-1]

def main():
    try:
        conn = boto.connect_s3()
        buck = conn.get_bucket('grid-iot-firmware-harvest')
        for obj in buck.list('fw_files/Zyxel/'):
            md5 = getBucketMd5(buck, obj)
            psql("UPDATE image SET brand ='Zyxel' WHERE hash=%(md5)s", locals())
            idlist= psql("SELECT id FROM image WHERE hash=%(md5)s and open_ports_ts is not NULL LIMIT 1", locals())
            if bool(idlist):
                # print('Already processed "%(fname)s"' % locals())
                continue
            fname = os.path.basename(obj.key)
            print('download "%s"' % fname)
            obj.get_contents_to_filename(fname)
            begin = time.time()
            print('begin=%s' % datetime.fromtimestamp(begin))
            os.system('python3 -u scripts/process_firmware_file.py "Zyxel" "%s"'%fname)
            os.remove(fname)
            end = time.time()
            print('end=%s' % datetime.fromtimestamp(end))
            print('consumed %s minutes'%((end-begin)/60.0))
    except BaseException as ex:
        traceback.print_exc()

if __name__=='__main__':
    main()

