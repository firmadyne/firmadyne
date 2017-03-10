#!/usr/bin/env python3
import sys
import re
from psql_firmware import psql


def psql0(q, v=None):
    return psql(q, v)[0][0]


def parse_nmap_log(nmap, iid):
    services = []
    for line in nmap:
        m = re.search(r"^(\d+)/(tcp|udp)\s+(\w+)\s+(\w+)", line)
        if m:
            port, pro, _, service = m.groups()
            services += [(port, pro, service)]
    if services:
        psql(
            "UPDATE image SET open_ports = %(services)s::TEXT[] WHERE id=%(iid)s",
            locals())


def main():
    iid = int(sys.argv[1])
    guestip = psql0("SELECT guest_ip FROM image WHERE id=%d" % iid)
    print('guestip=', guestip)
    from subprocess import Popen
    pp = Popen('sudo /usr/local/bin/nmap -e tap%(iid)s -T4 -sS -sU --top-ports 500 -v %(guestip)s'
               '| tee nmap.log.txt 2>&1' % locals(),
               shell=True,
               bufsize=1, stderr=sys.stdout, stdout=sys.stdout, universal_newlines=True)
    pp.wait()
    with open('nmap.log.txt', 'r') as nmap:
        parse_nmap_log(nmap, iid)


if __name__ == '__main__':
    main()
