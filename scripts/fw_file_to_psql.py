#!/usr/bin/env python3
#-*- coding: utf8 -*-
import sys
import hashlib
import psycopg2
import os
import argparse
from datetime import datetime


parser = argparse.ArgumentParser()
parser.add_argument('fw_file', help='firmware file path')
parser.add_argument('--brand', dest='brand', help='brand')
parser.add_argument('--model', dest='model', help='model')
parser.add_argument('--rev', dest='rev', help='hardware revision')
parser.add_argument('--ver', dest='ver', help='firmware version')
parser.add_argument('--rel_date', dest='rel_date', help='release date, such as "2016-12-31 23:10:59"')
parser.add_argument('--description', dest='desc', help='description')
parser.add_argument('--file_url', dest='file_url', help='firmware file url')
args = parser.parse_args()

try:
    fw_file = args.fw_file
    with open(fw_file,'rb') as fin:
        cont = fin.read()
        md5 = hashlib.md5(cont).hexdigest()
        sha1 = hashlib.sha1(cont).hexdigest()
    fsize = os.path.getsize(fw_file)
    brand = args.brand; model = args.model; rev = args.rev; ver = args.ver; file_url = args.file_url
    rel_date=args.rel_date; desc = args.desc
    if rel_date:
        rel_date=datetime.strptime(rel_date, "%Y-%m-%d %H:%M:%S")

    db = psycopg2.connect(database="firmware", user="firmadyne", 
            password="firmadyne", host="127.0.0.1")
    cur = db.cursor()
    sqls="INSERT INTO image "\
            "(filename,    hash,   file_sha1,  brand,      model,   hw_rev, file_size, version,   file_url,     rel_date,    description ) VALUES "\
            "(%(fw_file)s, %(md5)s,%(sha1)s,  %(brand)s, %(model)s, %(rev)s, %(fsize)s, %(ver)s, %(file_url)s, %(rel_date)s, %(desc)s )"\
            "ON CONFLICT (hash) DO UPDATE SET filename=%(fw_file)s, file_sha1=%(sha1)s, file_size=%(fsize)s "
    if brand: sqls += ", brand=%(brand)s"
    if model: sqls += ", model=%(model)s"
    if rev: sqls += ", hw_rev=%(rev)s"
    if ver: sqls += ", version=%(ver)s"
    if file_url: sqls += ", file_url=%(file_url)s"
    if rel_date: sqls += ", rel_date=%(rel_date)s"
    if desc: sqls += ", description=%(desc)s"

    cur.execute(sqls, locals())
    db.commit()
except Exception as ex:
    print(ex)
    import traceback
    traceback.print_exc()
finally:
    db.close()
