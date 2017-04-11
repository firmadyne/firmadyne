#!/usr/bin/env python3
import os
import hashlib
from scripts.psql_firmware import psql


def getFileMd5(fileName):
    with open(fileName, mode='rb') as fin:
        return hashlib.md5(fin.read()).hexdigest()


def s3_search(fname, iid):
    import boto
    try:
        s3 = boto.connect_s3()
        buck = s3.get_bucket('grid-iot-firmware-harvest')
        for obj in buck.list('fw_files/netgear/'):
            if obj.key.endswith(fname):
                obj.get_contents_to_filename(fname)
                furl = "s3://%s/%s" % (buck.name, obj.key)
                psql("UPDATE image SET file_url=%(furl)s"
                     "WHERE id = %(iid)s", locals())
                return fname
        return None
    finally:
        s3.close()


def main():
    rows = psql("SELECT "
                "id, open_ports, file_url, brand, filename, hash "
                "FROM image "
                "WHERE network_inferred IS TRUE AND brand='Netgear' AND id>=10498"
                # "WHERE  open_ports @> array['(23,tcp,telnet)'] AND mirai_botnet_positive IS NULL "
                " ORDER BY id")
    rows = [_ for _ in rows]
    for row in rows:
        iid, open_ports, furl, brand, filename, md5 = row
        md5 = md5.replace("-", "")
        print("%(iid)s %(open_ports)s " % locals())
        print('scripts/process_firmware_file.py '
              ' "%(brand)s" "%(furl)s"' % locals())
        if not furl:
            furl = s3_search(filename, iid)
            if not furl:
                print("Failed to search %s in S3" % (filename))
                continue
        os.system('python3 -u scripts/process_firmware_file.py '
                  '"%(brand)s" "%(furl)s"' % locals())
        try:
            os.remove(furl)
        except:
            pass


if __name__ == '__main__':
    main()
