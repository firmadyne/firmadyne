#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from shellutils import shell
import argparse
import sys
import re
from os import path
from psql_firmware import psql


parser = argparse.ArgumentParser()
parser.add_argument('brand', metavar='brand', type=str, help='brand name. E.g. "Asus", "Netgear".')
parser.add_argument('fw_file', metavar='fw_file', type=str, help='path to firmware file.')
args = parser.parse_args()
brand = args.brand
fw_file = args.fw_file
if not brand or not fw_file:
    parser.print_usage()
    sys.exit()


ret, txt = shell('./sources/extractor/extractor.py -b "%(brand)s" '
                '-sql 127.0.0.1 -np -nk "%(fw_file)s" images 2>&1'%locals())
if ret!=0:
    sys.exit(ret)
# >> Database Image ID: 774
iid =  int(re.search(r'Image ID: (\d+)', txt).group(1))
if not path.exists('images/%(iid)d.tar.gz'%locals()):
    print('failed to extract "%(fw_file)s" '%locals(), file=sys.stderr)
    sys.exit()

ret, txt = shell('./scripts/getArch.sh ./images/%(iid)d.tar.gz 2>&1'%locals())
if ret!=0:
    print('failed to getArch.sh %(iid)s'%locals(), file=sys.stderr)
    sys.exit(ret)
arch = psql("SELECT arch FROM image WHERE id=%d"%iid)
if arch not in ['mipsel','mipseb','armel']:
    print('unknown CPU Architect "%(arch)s" for %(iid)d'%locals(), file=sys.stderr)
    sys.exit(1)

ret, txt = shell('./scripts/tar2db.py -i %(iid)d -f images/%(iid)d.tar.gz 2>&1'%locals())
if ret!=0:
    if 'duplicate key value' not in  txt:
        print('failed to tar2db.py -i %(iid)d -f "images/%(iid)d.tar.gz"'%locals(), file=sys.stderr)
        sys.exit(ret)

ret, txt = shell('sudo ./scripts/makeImage.sh %(iid)d %(arch)s'%locals())
shell('sudo rm -f images/%(iid)d.tar.gz'%locals())
if not path.exists('./scratch/%(iid)d/image.raw'%locals()):
    print('failed to makeImage for %(iid)d'%locals(), file=sys.stderr)
    sys.exit(ret)

print('inferNetwork.sh %(iid)s %(arch)s'%locals())
ret, txt = shell('./scripts/inferNetwork.sh %(iid)s %(arch)s'%locals())
if 'network_inferred=true' not in txt:
    print('failed to inferNetwork.sh %(iid)d %(arch)s'%locals(), file=sys.stderr)
    sys.exit(ret)

print('test_network_reachable')
from test_network_reachable import test_network_reachable
test_network_reachable(iid)
# ret ,txt= shell('./scripts/run.sh %(iid)s'%locals())
# shell('./analyses/runExploits.py -t %(guest_ip)s'%locals())

