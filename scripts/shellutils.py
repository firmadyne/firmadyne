#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
from os import path
import sys

def shell(cmd):
    cmd = path.expandvars(cmd)
    proc= subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ret=None
    cmdout=''
    while True:
        s = proc.stdout.read().decode('utf8')
        print(s, end='', flush=True)
        cmdout+=s
        s = proc.stderr.read().decode('utf8')
        print(s, end='', flush=True)
        cmdout+=s
        ret = proc.poll()
        if ret is not None:
            break
    s = proc.stdout.read().decode('utf8')
    print(s, end='', flush=True)
    cmdout+=s
    s = proc.stderr.read().decode('utf8')
    print(s, end='', flush=True)
    cmdout+=s

    if ret!=0:
        print('''\'%s\' returns %d'''%(cmd,ret), file=sys.stderr)

    return ret, cmdout

