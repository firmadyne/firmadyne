#!/usr/bin/env python3
import os
import hashlib
from scripts.psql_firmware import psql
import boto


def getFileMd5(fileName):
    with open(fileName, mode='rb') as fin:
        return hashlib.md5(fin.read()).hexdigest()


def s3_download(furl, fname):
    from urllib.parse import urlsplit
    try:
        sr = urlsplit(furl)
        s3 = boto.connect_s3()
        buck = s3.get_bucket(sr.netloc)
        obj = buck.get_key(sr.path)
        obj.get_contents_to_filename(fname)
        return fname
    finally:
        s3.close()


def s3_search(fname, iid, brand, md5):
    try:
        s3 = boto.connect_s3()
        buck = s3.get_bucket('grid-iot-firmware-harvest')
        def find(b):
            for obj in buck.list('fw_files/%s/', b):
                if obj.key.endswith(fname):
                    obj.get_contents_to_filename(fname)
                    if getFileMd5(fname) != md5:
                        print('md5 not match ', obj.key)
                        continue
                    furl = "s3://%s/%s" % (buck.name, obj.key)
                    psql("UPDATE image SET file_url=%(furl)s"
                         "WHERE id = %(iid)s", locals())
                    return fname
        if find(brand):
            return fanme
        elif find(brand.lower()):
            return fname
        elif find(brand.lower().replace('-', '')):
            return fname
        return None
    finally:
        s3.close()


def s3_check_md5(furl, fname, md5, iid, brand):
    fname = s3_download(furl, fname)
    if md5 != getFileMd5(fname):
        print("erase iid=%(iid)s")
        psql("UPDATE image SET file_url=NULL "
             "WHERE id = %(iid)s", locals())
        return s3_search(fname, iid, brand, md5)
    else:
        return fname


def main():
    rows = psql("SELECT "
                "id, open_ports, file_url, brand, filename, hash "
                "FROM image "
                # "WHERE file_url ILIKE 's3://%' "
                # "WHERE  open_ports @> array['(23,tcp,telnet)'] AND mirai_botnet_positive IS NULL "
                " WHERE id>1230"
                " ORDER BY id")
    # rows = [_ for _ in rows]
    for row in rows:
        statvfs = os.statvfs('/home')
        free_gb = statvfs.f_frsize * statvfs.f_bavail/1000/1000/1000
        if free_gb < 2.0:
            print("free space not enought")
            break
        iid, open_ports, furl, brand, filename, md5 = row
        md5 = md5.replace("-", "")
        print("%(iid)s %(open_ports)s " % locals())
        print('scripts/process_firmware_file.py '
              ' "%(brand)s" "%(furl)s"' % locals())
        if not furl:
            furl = s3_search(filename, iid, brand, md5)
            if not furl:
                print("Failed to search %s in S3" % (filename))
                continue
        elif furl.startswith('s3://'):
            furl = s3_check_md5(furl, filename, md5, iid, brand)
        os.system('python3 -u scripts/process_firmware_file.py '
                  '"%(brand)s" "%(furl)s"' % locals())
        try:
            os.remove(furl)
        except:
            pass


if __name__ == '__main__':
    main()
