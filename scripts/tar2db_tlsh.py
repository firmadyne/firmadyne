#!/usr/bin/env python3
#-*- coding:utf8 -*-

import tlsh
import hashlib
import tarfile
import sys
import psycopg2
from psycopg2 import errorcodes as psqlerr
import re
import traceback


def main:
    if len(sys.argv)<2:
        print('eg:\n  %s images/123.tar.gz'%(sys.argv[0]))
        return
    fname = sys.argv[1]
    m = re.search(r'(\d+)\.tar\.gz', fname)
    if m:
        parent_id = int(m.group(1))
    elif len(sys.argv)>2:
        parent_id = sys.argv[2]
    else:
        print('please give me firmware image ID')
        sys.exit(1)
    tfile = tarfile.open(fname)

    try:
        db = psycopg2.connect(database='firmware',host='127.0.0.1',
                user='firmadyne',password='firmadyne')
        cur = db.cursor()

        for mem in tfile.getmembers():
            fname = mem.name
            if mem.isfile():
                f = tfile.extractfile(mem)
                cont = f.read()
                sha1_hash = hashlib.sha1(cont).hexdigest()
                md5_hash = hashlib.md5(cont).hexdigest()
                filesize = mem.size
                tlsh_hash = tlsh.hash(cont)
                try:
                    cur.execute("INSERT INTO unpacked_fw \
                            (  parent_id,   filename,    sha1_hash,    md5_hash,    tlsh_hash,       filesize) VALUES \
                            (%(parent_id)s, %(fname)s, %(sha1_hash)s, %(md5_hash)s, %(tlsh_hash)s, %(filesize)s)", 
                            locals())
                    db.commit()
                except psycopg2.Error as ex:
                    if ex.pgcode not in [psqlerr.UNIQUE_VIOLATION]:
                        print(ex)
                    db.rollback()
            elif mem.issym():
                linkpath = mem.linkpath
                try:
                    cur.execute("INSERT INTO unpacked_fw \
                            (  parent_id,   filename,   linkpath) VALUES \
                            (%(parent_id)s, %(fname)s,  %(linkpath)s)", 
                            locals())
                    db.commit()
                except psycopg2.Error as ex:
                    if ex.pgcode not in [psqlerr.UNIQUE_VIOLATION]:
                        print(ex)
                    db.rollback()
    except Exception as ex:
        print(ex)
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
