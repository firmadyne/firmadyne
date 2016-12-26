import os
import sys
import re
import time
import pytz
import argparse
from datetime import datetime
from psql_firmware import psql
import traceback
import hashlib


def getFileMd5(fileName)->str:
    with open(fileName,mode='rb') as fin:
        return hashlib.md5(fin.read()).hexdigest()


def grep(fname, regexpattern):
    with open(fname, 'r') as fin:
        for line in fin:
            m = re.search(regexpattern, line)
            if m:
                return m.group(1)
    

def main():
    brand = sys.argv[1]
    fw_file = sys.argv[2]
    md5 = getFileMd5(fw_file)
    rows = psql('SELECT id, process_finish_ts, process_start_ts FROM image WHERE hash=%(md5)s', locals())
    if rows and rows[0][1]:
        iid, process_finish_ts, process_start_ts = rows[0][0], rows[0][1], rows[0][2]
        diff = process_finish_ts - process_start_ts
        print("Already processed id=%(iid)s at %(process_start_ts)s, difftime=%(diff)s" % locals())
        return
    try:
        ts = datetime.now(pytz.utc)
        print("<<1>> extract fw_file\n")
        
        os.system('python -u scripts/extractor.py -b "%(brand)s" "%(fw_file)s" images | tee extraction.log' % locals())
        iid = grep('extraction.log', r'Database Image ID: (\d+)')
        iid = int(iid)
        os.remove('extraction.log')
        psql('UPDATE image SET process_start_ts=%(ts)s WHERE id=%(iid)s', locals())
        print('scripts/fw_file_to_psql.py "%(fw_file)s" --brand %(brand)s' % locals())
        os.system('scripts/fw_file_to_psql.py "%(fw_file)s" --brand "%(brand)s"' % locals())
        if not os.path.exists("images/%(iid)s.tar.gz" % locals()):
            print('images/%(iid)s.tar.gz doesn\'t exist. Extraction failed.' % locals())
            return

        print('<<2>> store unpacked file names and hashes\n')
        os.system('scripts/getArch.sh images/%(iid)s.tar.gz' % locals())
        arch = psql("SELECT arch FROM image WHERE id=%(iid)s" % locals())
        arch = arch[0][0]
        os.system('scripts/tar2db_tlsh.py images/%(iid)s.tar.gz' % locals())
        os.system('sudo ./scripts/makeImage.sh %(iid)s %(arch)s' % locals())
        os.system(os.path.expandvars('sudo chown -R $USER:$USER scratch/%(iid)s') % locals())

        # infer network

        print("<<3>> infer network config\n")
        print("inferNetwork.sh %(iid)s" % locals())
        os.system('scripts/inferNetwork.sh %(iid)s %(arch)s' % locals())

        net_infer_OK=psql("SELECT network_inferred FROM image WHERE id=%(iid)s", locals())
        net_infer_OK = net_infer_OK[0][0]
        if not net_infer_OK:
            print('network inference failed')
            return

        print("<<4>> test network_reachable\n")
        # net_reachable
        os.system('python3 -u scripts/test_network_reachable.py %(iid)s test | tee test_network_reachable.log' % locals())

        net_reachable = grep('test_network_reachable.log', r'network_reachable=(\w+)')
        os.remove('test_network_reachable.log')
        if net_reachable != 'True':
            print("network_reachable = False")
            return

        print( "<<5>> Metasploit and Nmap scan\n" )
        guest_ip=psql("SELECT guest_ip FROM image WHERE id=%(iid)s", locals())
        guest_ip=guest_ip[0][0]
        os.system('python3 -u scripts/test_network_reachable.py %(iid)s construct' % locals())
        while True:
            ret = os.system('ping -c1 %(guest_ip)s &>/dev/null' % locals())
            if ret==0:
                break
            else:
                time.sleep(1)

        os.system('python3 -u analyses/runExploits.py -i %(iid)s' % locals())
        os.system('scripts/nmap_scan.py %(iid)s' % locals())
        os.system('scripts/test_network_reachable.py %(iid)s destruct' % locals())
        os.system('scripts/merge_metasploit_logs.py %(iid)s' % locals())

    except BaseException as ex:
        traceback.print_exc()
    finally:
        ts = datetime.now(pytz.utc)
        psql('UPDATE image SET process_finish_ts=%(ts)s WHERE id=%(iid)s', locals())


if __name__=="__main__":
    main()

