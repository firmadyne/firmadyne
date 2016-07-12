#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
from os import path
import sys

def shell(cmd):
    cmd = path.expandvars(cmd)
    proc= subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ret = proc.wait()
    cmdout = proc.stdout.read().decode('utf8')
    print(cmdout, end='', flush=True)
    if ret!=0:
        print('\'%s\' returns %d'%(cmd,ret), file=sys.stderr)
    return ret, cmdout

