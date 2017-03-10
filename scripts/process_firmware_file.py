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
        fileName= newFileName
    fin.close()
    return fileName


def is_url_file(furl):
    return furl.startswith("https://") or furl.startswith("ftp://") or \
        furl.startswith("http://")


def main():
    brand = sys.argv[1]
    furl = sys.argv[2]
    if is_url_file(furl):
        fw_file = download_file(furl)
        md5 = getFileMd5(fw_file)
        try:
            iid = psql00('SELECT id FROM image WHERE hash=%(md5)s', locals())
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

        network_inferred_ts = datetime.now(pytz.utc)
        psql(
            'UPDATE image SET network_inferred_ts=%(network_inferred_ts)s WHERE id=%(iid)s',
            locals())
        if not net_infer_OK:
            print('network inference failed')
            return

        print("<<4>> test network_reachable\n")

        # net_reachable
        os.system(
            'python3 -u scripts/test_network_reachable.py %(iid)s test' % locals())
        net_reachable = psql00(
            "SELECT network_reachable FROM image WHERE id=%(iid)s", locals())
        print("network_reachable = ", net_reachable)
        network_reachable_ts = datetime.now(pytz.utc)
        psql('UPDATE image SET network_reachable_ts=%(network_reachable_ts)s '
             'WHERE id=%(iid)s',
             locals())
        if net_reachable is not True:
            return

        print("<<5>> Metasploit and Nmap scan\n")
        os.system(
            'python3 -u scripts/test_network_reachable.py %(iid)s construct' %
            locals())
        guest_ip = psql(
            "SELECT guest_ip FROM image WHERE id=%(iid)s",
            locals())
        guest_ip = guest_ip[0][0]
        ping_until_OK(guest_ip, 60.0)

        print("<<5.0>> Mirai Vulnerable Test\n")
        os.system('python3 -u scripts/telnet_login_test.py %(iid)s' % locals())

        os.system('python3 -u analyses/runExploits.py -i %(iid)s' % locals())
        os.system('scripts/merge_metasploit_logs.py %(iid)s' % locals())

        vulns_ts = datetime.now(pytz.utc)
        psql('UPDATE image SET vulns_ts=%(vulns_ts)s WHERE id=%(iid)s', locals())

        os.system('python3 -u scripts/nmap_scan.py %(iid)s' % locals())

        open_ports_ts = datetime.now(pytz.utc)
        psql(
            'UPDATE image SET open_ports_ts=%(open_ports_ts)s WHERE id=%(iid)s',
            locals())

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
