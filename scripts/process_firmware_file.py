#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import re
import time
import pytz
# import argparse
from datetime import datetime
from psql_firmware import psql
import traceback
import hashlib


def psql00(query, params):
    return psql(query, params)[0][0]


def getFileMd5(fileName):
    with open(fileName, mode='rb') as fin:
        return hashlib.md5(fin.read()).hexdigest()


def getFileSha1(fileName):
    with open(fileName, mode='rb') as fin:
        return hashlib.sha1(fin.read()).hexdigest()


def grep(fname, regexpattern):
    with open(fname, 'r') as fin:
        for line in fin:
            m = re.search(regexpattern, line)
            if m:
                return m.group(1)


def ping_until_OK(host, timeOut=60.0):
    begin = time.time()
    while (time.time() - begin) < timeOut:
        ret = os.system("ping %(host)s -c 1 -w 2" % locals())
        if ret == 0:
            return True
        else:
            time.sleep(2)
    return False


def download_file(furl):
    if furl.startswith("s3://"):
        return download_s3_file(furl)
    elif furl.startswith("ftp://"):
        return download_ftp_file(furl)
    else:
        return download_http_file(furl)


def download_s3_file(furl):
    from urllib import parse
    fw_path = parse.urlsplit(furl).path
    netloc = parse.urlsplit(furl).netloc
    assert netloc=='grid-iot-firmware-harvest'
    import boto
    conn = boto.connect_s3()
    buck = conn.get_bucket('grid-iot-firmware-harvest')
    obj = buck.get_key(fw_path)
    fname = os.path.basename(fw_path)
    obj.get_contents_to_filename(fname)
    return fname


def download_ftp_file(furl):
    from urllib import parse
    import ftputil
    fw_path = parse.urlsplit(furl).path
    netloc = parse.urlsplit(furl).netloc
    with ftputil.FTPHost(netloc, 'anonymous', '') as host:
        fname = furl.split('/')[-1]
        host.download(fw_path, fname)
        return fname


def download_http_file(furl):
    import requests
    from urllib import parse
    fileName = os.path.basename(parse.urlparse(furl).path)
    fout = open(fileName, "wb")
    try:
        fin = requests.get(url=furl)
    except:
        fout.close()
        raise
    fout.write(fin.content)
    fout.close()
    if 'Content-Disposition' in fin.headers:
        newFileName = fin.headers['Content-Disposition'].split(';')[-1].split('=')[-1]
        os.rename(fileName, newFileName)
        fileName = newFileName
    fin.close()
    return fileName


def is_url_file(furl):
    return re.match(r'(http://|https://|ftp://|s3://)', furl)


def main():
    brand = sys.argv[1]
    furl = sys.argv[2]
    if is_url_file(furl):
        fw_file = download_file(furl)
        md5 = getFileMd5(fw_file)
        try:
            iid, file_url = psql(
                    'SELECT id, file_url FROM image WHERE hash=%(md5)s'
                    ' LIMIT 1', locals())[0]
            if not file_url:
                psql('UPDATE image SET file_url=%(furl)s, filename=%(fw_file)s '
                     'WHERE id=%(iid)s', locals())
        except IndexError:
            sha1 = getFileSha1(fw_file)
            fsize = os.path.getsize(fw_file)
            iid = psql("INSERT INTO image "
                       " (filename, brand, hash, file_sha1, file_size, file_url) VALUES"
                       " (%(fw_file)s, %(brand)s, %(md5)s, %(sha1)s, %(fsize)s, %(furl)s)"
                       " RETURNING id", locals())
            iid = iid[0][0]
        print("UPDATE file_url for id=%(iid)s " % locals())
    else:
        fw_file = furl
        md5 = getFileMd5(fw_file)

    rows = psql(
        'SELECT id, process_finish_ts, process_start_ts FROM image WHERE hash=%(md5)s',
        locals())
    if rows and rows[0][1]:
        iid, process_finish_ts, process_start_ts = rows[0][0], rows[0][1], rows[0][2]
        diff = process_finish_ts - process_start_ts
        print(
            "Already processed id=%(iid)s at %(process_start_ts)s, difftime=%(diff)s" %
            locals())
        if process_start_ts >  datetime(2017,4,12):
            print('Too recent processed firmware 2017/04/12')
            return
    try:
        process_start_ts = datetime.now(pytz.utc)
        print("<<1>> extract firmware file\n")

        os.system(
            'python -u scripts/extractor.py -b "%(brand)s" "%(fw_file)s" images | tee extraction.log' %
            locals())
        iid = grep('extraction.log', r'Database Image ID: (\d+)')
        iid = int(iid)
        os.remove('extraction.log')
        psql(
            'UPDATE image SET process_start_ts=%(process_start_ts)s WHERE id=%(iid)s',
            locals())
        print(
            'python3 -u scripts/fw_file_to_psql.py "%(fw_file)s" --brand %(brand)s' %
            locals())
        os.system(
            'python3 -u scripts/fw_file_to_psql.py "%(fw_file)s" --brand "%(brand)s"' %
            locals())
        rootfs_extracted_ts = datetime.now(pytz.utc)
        psql(
            'UPDATE image SET rootfs_extracted_ts=%(rootfs_extracted_ts)s WHERE id=%(iid)s',
            locals())
        if not os.path.exists("images/%(iid)s.tar.gz" % locals()):
            print(
                'images/%(iid)s.tar.gz doesn\'t exist. Extraction failed.' %
                locals())
            return

        print('<<2>> store unpacked file names and hashes\n')
        os.system('scripts/getArch.sh images/%(iid)s.tar.gz' % locals())
        arch = psql("SELECT arch FROM image WHERE id=%(iid)s" % locals())
        arch = arch[0][0]
        os.system(
            'python3 scripts/tar2db_tlsh.py images/%(iid)s.tar.gz' %
            locals())
        os.system('sudo ./scripts/makeImage.sh %(iid)s %(arch)s' % locals())
        os.system(
            os.path.expandvars('sudo chown -R $USER:$USER scratch/%(iid)s') %
            locals())

        # infer network

        print("<<3>> infer network config\n")
        print("inferNetwork.sh %(iid)s" % locals())
        os.system('scripts/inferNetwork.sh %(iid)s %(arch)s' % locals())

        net_infer_OK = psql(
            "SELECT network_inferred FROM image WHERE id=%(iid)s",
            locals())
        net_infer_OK = net_infer_OK[0][0]
        if not net_infer_OK:
            net_infer_OK = False 

        network_inferred_ts = datetime.now(pytz.utc)
        psql(
            'UPDATE image SET network_inferred_ts=%(network_inferred_ts)s WHERE id=%(iid)s',
            locals())
        psql(
            'UPDATE image SET network_inferred=%(net_infer_OK)s WHERE id=%(iid)s',
            locals())
        if not net_infer_OK:
            print('network inference failed')
            return

        # print("<<4>> test network_reachable\n")

        # # net_reachable
        # os.system(
        #     'python3 -u scripts/test_network_reachable.py %(iid)s test' % locals())
        # net_reachable = psql00(
        #     "SELECT network_reachable FROM image WHERE id=%(iid)s", locals())
        # print("network_reachable = ", net_reachable)
        # network_reachable_ts = datetime.now(pytz.utc)
        # psql('UPDATE image SET network_reachable_ts=%(network_reachable_ts)s '
        #      'WHERE id=%(iid)s',
        #      locals())
        # if net_reachable is not True:
        #     return

        print("<<5>> Metasploit and Nmap scan\n")
        os.system(
            'python3 -u scripts/test_network_reachable.py %(iid)s construct' %
            locals())
        guest_ip = psql(
            "SELECT guest_ip FROM image WHERE id=%(iid)s",
            locals())
        guest_ip = guest_ip[0][0]
        network_reachable = True
        if not ping_until_OK(guest_ip, 80.0):
            network_reachable = False
            print("network_reachable = ", network_reachable)
            psql('UPDATE image SET network_reachable=%(network_reachable)s '
                 'WHERE id=%(iid)s', locals())
            os.system(
                'python3 -u scripts/test_network_reachable.py %(iid)s destruct' %
                locals())
            return
        else:
            psql('UPDATE image SET network_reachable=%(network_reachable)s '
                 'WHERE id=%(iid)s', locals())


        print("<<5.0>> Mirai Vulnerable Test\n")
        os.system('python3 -u scripts/telnet_login_test.py %(iid)s' % locals())

        os.system('python3 -u analyses/runExploits.py -i %(iid)s' % locals())
        os.system('scripts/merge_metasploit_logs.py %(iid)s' % locals())

        # vulns_ts = datetime.now(pytz.utc)
        # psql('UPDATE image SET vulns_ts=%(vulns_ts)s WHERE id=%(iid)s', locals())

        os.system('python3 -u scripts/nmap_scan.py %(iid)s' % locals())

        # open_ports_ts = datetime.now(pytz.utc)
        # psql(
        #     'UPDATE image SET open_ports_ts=%(open_ports_ts)s WHERE id=%(iid)s',
        #     locals())

        os.system(
            'scripts/test_network_reachable.py %(iid)s destruct' %
            locals())

    except BaseException as ex:
        traceback.print_exc()
    finally:
        process_finish_ts = datetime.now(pytz.utc)
        psql(
            'UPDATE image SET process_finish_ts=%(process_finish_ts)s WHERE id=%(iid)s',
            locals())
        print('UPDATE process_finish_ts = %(process_finish_ts)s' % locals())
        psql('UPDATE image SET filename=%(fw_file)s WHERE id=%(iid)s', locals())


if __name__ == "__main__":
    main()
