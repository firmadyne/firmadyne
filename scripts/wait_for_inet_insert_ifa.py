#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import getopt
import argparse
import time
import re
import struct
import socket


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('logfile', metavar='logfile', type=str, help='path of qemu.initial.serial.log')
    parser.add_argument('--timeout', dest='timeout', default=42, type=int,
            help='timeout to wait for __inet_insert_ifa')
    parser.add_argument('--archend', dest='archend', type=str, default='mipsel',
            help='architecture+endianness, allowable values: "armel", "mipsel", "mipseb" ')
    args = parser.parse_args()
    try:
        logfile = args.logfile
        timeout = args.timeout
        endianness = args.archend[-2:]
    except (AttributeError, TypeError):
        parser.print_usage()
        return "Bad arguments"

    begin = time.time()
    while True:
        with open(logfile, mode='r') as fin:
            s = fin.read()
        i = s.find('__inet_insert_ifa')
        if i!=-1:
            m = re.search(r'0x[0-9a-z]{8}', s[i:], flags=re.I)
            fmt = '>I' if endianness=='eb' else '<I'
            ip = socket.inet_ntoa(struct.pack(fmt, int(m.group(0)[2:], 16)))
            if ip not in ['0.0.0.0', '127.0.0.1']:
                return ip

        time.sleep(10)
        if time.time()-begin > timeout:
            return 'Not found'

if __name__=="__main__":
    msg = main()
    print(msg)

