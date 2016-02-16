#!/usr/bin/env python

import tarfile
import getopt
import sys
import re
import hashlib
import psycopg2

def getFileHashes(infile):
    t = tarfile.open(infile)
    files = list()
    links = list()
    for f in t.getmembers():
        if f.isfile():
            # we use f.name[1:] to get rid of the . at the beginning of the path
            files.append((f.name[1:], hashlib.md5(t.extractfile(f).read()).hexdigest(),
                          f.uid, f.gid, f.mode))
        elif f.issym():
            links.append((f.name[1:], f.linkpath))
    return (files, links)

def getOids(objs, cur):
    # hashes ... all the hashes in the tar file
    hashes = [x[1] for x in objs]
    hashes_str = ",".join(["""'%s'""" % x for x in hashes])
    query = """SELECT id,hash FROM object WHERE hash IN (%s)"""
    cur.execute(query % hashes_str)
    res = [(int(x), y) for (x, y) in cur.fetchall()]

    existingHashes = [x[1] for x in res]

    missingHashes = set(hashes).difference(set(existingHashes))

    newObjs = createObjects(missingHashes, cur)

    res += newObjs

    result = dict([(y, x) for (x, y) in res])
    return result

def createObjects(hashes, cur):
    query = """INSERT INTO object (hash) VALUES (%(hash)s) RETURNING id"""
    res = list()
    for h in set(hashes):
        cur.execute(query, {'hash':h})
        oid = int(cur.fetchone()[0])
        res.append((oid, h))
    return res

def insertObjectToImage(iid, files2oids, links, cur):
    query = """INSERT INTO object_to_image (iid, oid, filename, regular_file, uid, gid, permissions) VALUES (%(iid)s, %(oid)s, %(filename)s, %(regular_file)s, %(uid)s, %(gid)s, %(mode)s)"""

    cur.executemany(query, [{'iid': iid, 'oid' : x[1], 'filename' : x[0][0],
                             'regular_file' : True, 'uid' : x[0][1],
                             'gid' : x[0][2], 'mode' : x[0][3]} \
                            for x in files2oids])
    cur.executemany(query, [{'iid': iid, 'oid' : 1, 'filename' : x[0],
                             'regular_file' : False, 'uid' : None,
                             'gid' : None, 'mode' : None} \
                            for x in links])

def process(iid, infile):
    dbh = psycopg2.connect(database="firmware", user="firmadyne",
                           password="firmadyne", host="127.0.0.1")
    cur = dbh.cursor()

    (files, links) = getFileHashes(infile)

    oids = getOids(files, cur)

    fdict = dict([(h, (filename, uid, gid, mode)) \
            for (filename, h, uid, gid, mode) in files])

    file2oid = [(fdict[h], oid) for (h, oid) in oids.iteritems()]

    insertObjectToImage(iid, file2oid, links, cur)

    dbh.commit()

    dbh.close()

def main():
    infile = iid = None
    opts, argv = getopt.getopt(sys.argv[1:], "f:i:")
    for k, v in opts:
        if k == '-i':
            iid = int(v)
        if k == '-f':
            infile = v

    if infile and not iid:
        m = re.match(r"(\d+)\.tar\.gz", infile)
        if m:
            iid = int(m.groups(1))

    process(iid, infile)

if __name__ == "__main__":
    main()
