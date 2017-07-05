#!/usr/bin/env python3
# -*- coding: utf8 -*-

import psycopg2
from psycopg2 import errorcodes as psqlerr
import hashlib
import os
import traceback


def find_file(fname, brand):
    from os.path import exists,join
    brand=brand.lower()
    fpath = "./sources/scraper/output/%(brand)s/%(fname)s"%locals()
    if exists(fpath):
        return fpath
    brand = brand.replace('-', '').replace('&','')
    fpath = "./sources/scraper/output/%(brand)s/%(fname)s"%locals()
    if exists(fpath):
        return fpath
    fpath = "./%(fname)s"%locals()
    if exists(fpath):
        return fpath
    else:
        return None


try:
    db2=psycopg2.connect(database='firmware', user='firmadyne',
                         password='firmadyne', host='127.0.0.1')
    cur = db2.cursor()
    cur.execute("SELECT id, filename,brand FROM image")
    rows = cur.fetchall()
    for iid, fname, brand in rows:
        fpath = find_file(fname, brand)
        if not fpath:
            print('cannot find %(iid)s, %(brand)s, %(fname)s'%locals())
            sha1=None
            cur.execute("UPDATE image SET file_sha1=%(sha1)s where id=%(iid)s", locals())
            db2.commit()
            continue
        with open(fpath, 'rb') as fin:
            sha1 = hashlib.sha1(fin.read()).hexdigest()
            print('%(iid)s, %(brand)s, %(fname)s, %(sha1)s'%locals())
            cur.execute("UPDATE image SET file_sha1=%(sha1)s where id=%(iid)s", locals())
            db2.commit()

except Exception as ex:
    print(ex)
    traceback.print_exc()
finally:
    db2.close()

