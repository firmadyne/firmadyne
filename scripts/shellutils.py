#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
from os import path
import sys

def shell(cmd):
    bufsize=8
    cmd = path.expandvars(cmd)
    proc= subprocess.Popen(cmd, shell=True,bufsize=1, 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    ret=None
    cmdout=''
    while True:
        s = proc.stdout.readline()
        print(s, flush=True)
        # s = proc.stdout.read(bufsize).decode('utf8')
        # print(s, end='', flush=True)
        cmdout+=s
        s = proc.stderr.read(bufsize).decode('utf8')
        print(s, end='', flush=True)
        cmdout+=s
        ret = proc.poll()
        if ret is not None:
            break
    s = proc.stdout.read(bufsize).decode('utf8')
    print(s, end='', flush=True)
    cmdout+=s
    s = proc.stderr.read(bufsize).decode('utf8')
    print(s, end='', flush=True)
    cmdout+=s

    if ret!=0:
        print('''\'%s\' returns %d'''%(cmd,ret), file=sys.stderr)

    return ret, cmdout

