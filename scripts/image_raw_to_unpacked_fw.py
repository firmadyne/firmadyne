#!/usr/bin/env python3
# -*- coding: utf8 -*-
import os
from os import path
import psycopg2
import tlsh
import hashlib
import sys


parent_id = int(sys.argv[1])
prelen = len('scratch/%(parent_id)d/image/'%locals())

try:
    db = psycopg2.connect(database="firmware", user="firmadyne", 
            password="firmadyne", host="127.0.0.1")
    cur = db.cursor()
    for root, dirs, files in os.walk('scratch/%(parent_id)d/image/'%locals()):
        for f in files:
            f2 = path.join(root,f)
            try:
                fname ='./'+f2[prelen:] 
                if path.isfile(f2):
                    fsize=path.getsize(f2)
                    perm=os.stat(f2).st_mode
                    with open(f2, 'rb') as fin:
                        cont = fin.read()
                        sha1_hash = hashlib.sha1(cont).hexdigest()
                        md5_hash = hashlib.md5(cont).hexdigest()
                        tlsh_hash = tlsh.hash(cont)
                    symtgt=None
                elif path.islink(f2):
                    symtgt=path.realpath(f2)
                    perm=os.stat(f2, follow_symlinks=False).st_mode
                    fsize=None
                    sha1_hash=md5_hash=tlsh_hash=None
                else:
                    perm=os.stat(f2, follow_symlinks=False).st_mode
                    fsize=path.getsize(f2)
                    sha1_hash=md5_hash=tlsh_hash=None

                print(fname, f2)
                cur.execute("INSERT INTO unpacked_fw "
                        "(parent_id,filename,sha1_hash,md5_hash,tlsh_hash,linkpath,filesize,permission) VALUES "
                        "(%(parent_id)s, %(fname)s, %(sha1_hash)s, %(md5_hash)s, %(tlsh_hash)s, %(symtgt)s, %(fsize)s, %(perm)s )",
                        locals())
            except FileNotFoundError:
                print('%s error'%(f2))
    db.commit()
except Exception as ex:
    print(ex)
finally:
    db.close()
