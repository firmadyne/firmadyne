#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from os import path
import sys
import pdb
import traceback
import psycopg2

conn = psycopg2.connect(database="firmware", user="firmadyne", 
        password="firmadyne", host="127.0.0.1")
cur = conn.cursor()

firmadyne_root = path.dirname(path.dirname(path.realpath(__file__)))
FIRMWARE_DIR='/home/mikil/firmadyne/firmadyne/'
BINARY_DIR='{FIRMWARE_DIR}/binaries/'.format(**globals())
TARBALL_DIR='{FIRMWARE_DIR}/images/'.format(**globals())
SCRATCH_DIR='{FIRMWARE_DIR}/scratch/'.format(**globals())
SCRIPT_DIR='{FIRMWARE_DIR}/scripts/'.format(**globals())

def gl(localvars):
    d=globals()
    d.update(localvars)
    return d

def shell(cmd):
    import subprocess
    cmd = path.expandvars(cmd)
    proc= subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE)
    returncode = proc.wait()
    cmdout = proc.stdout.read().decode('utf8')
    print(cmdout, end='', flush=True)
    return returncode, cmdout

def get_kernel(archend):
    if archend=='mipsel':
        return "{BINARY_DIR}/vmlinux.{archend}".format(**gl(locals()))
def get_qemu_machine(archend):
    if archend=='armel':
        return 'virt'
    elif archend=='mipseb' or archend=='mipsel':
        return 'malta'
def get_qemu_disk(archend):
    if archend=='armel':
        return '/dev/vda1'
    elif archend=='mipseb' or archend=='mipsel':
        return '/dev/sda1'
def get_qemu(archend):
    if archend=='armel':
        return 'qemu-system-arm'
    elif archend=='mipseb':
        return 'qemu-system-mips'
    elif archend=='mipsel':
        return 'qemu-system-mipsel'
def get_scratch(iid):
    return ('{SCRATCH_DIR}/{iid}'.format(**gl(locals())))
def get_fs(iid):
    return (get_scratch(iid)+'/image.raw')

if len(sys.argv)<2:
    print("usage: \n\
            %s {IID}"%(sys.argv[0]))
    sys.exit()
IID = int(sys.argv[1])
cur.execute("SELECT arch FROM image WHERE id=%s"%IID)
ARCHEND = cur.fetchone()[0]
# ARCHEND='mipsel'
# IID=774
GUESTIP='192.168.1.220'
NETDEVIP='192.168.1.219'
TAPDEV='tap%s'%IID
HOSTNETDEV=TAPDEV

IMAGE=get_fs(IID)
KERNEL=get_kernel(ARCHEND)
QEMU=get_qemu(ARCHEND)
QEMU_MACHINE=get_qemu_machine(ARCHEND)
QEMU_ROOTFS=get_qemu_disk(ARCHEND)
WORK_DIR=get_scratch(IID)

print("Creating TAP device {TAPDEV}...".format(**gl(locals())))
shell('sudo tunctl -t {TAPDEV} -u $USER'.format(**gl(locals())))
print("Bringing up TAP device...")
shell('sudo ifconfig {HOSTNETDEV} {NETDEVIP}/24 up'.format(**gl(locals())))
print("Adding route to {GUESTIP}...".format(**gl(locals())))
shell('sudo route add -host {GUESTIP} gw {GUESTIP} {HOSTNETDEV}'.format(**gl(locals())))

print("Starting emulation of firmware... ")
shell('''{QEMU} -m 256 -M {QEMU_MACHINE} -kernel {KERNEL} \
        -drive if=ide,format=raw,file={IMAGE} -append "root={QEMU_ROOTFS} console=ttyS0 nandsim.parts=64,64,64,64,64,64,64,64,64,64 rdinit=/preInit.sh rw debug ignore_loglevel print-fatal-signals=1 user_debug=31 firmadyne.syscall=8" \
    -serial file:{WORK_DIR}/qemu.final.serial.log \
    -serial unix:/tmp/qemu.{IID}.S1,server,nowait \
    -monitor unix:/tmp/qemu.{IID},server,nowait \
    -display none \
    -daemonize \
    -net nic,vlan=0 -net socket,vlan=0,listen=:2000 -net nic,vlan=1 -net tap,vlan=1,ifname={TAPDEV},script=no -net nic,vlan=2 -net socket,vlan=2,listen=:2002 -net nic,vlan=3 -net socket,vlan=3,listen=:2003  \
    '''.format(**gl(locals())))

import time
time.sleep(10)
from urllib import request
network_reachable=False
try:
    with request.urlopen('http://{GUESTIP}/'.format(**gl(locals())), timeout=10) as fin:
        htmlsrc = fin.readall().decode('utf8')
        if len(htmlsrc)>0:
            print('network_reachable')
            network_reachable=True
        else:
            print('network not reachable')
except Exception as ex:
    print('network not reachable')
    # traceback.print_exc()
cur.execute("UPDATE image SET network_reachable=%s WHERE id=%s", 
        (network_reachable, IID))
conn.commit()


print("Done!")
print("The emulated firmware may not be accessible while booting.")
print("Press any key to destroy the network and shutdown emulation.")
input()
shell('killall {QEMU}'.format(**gl(locals())))

print( "Deleting route...")
shell('sudo route del -host {GUESTIP} gw {GUESTIP} ${HOSTNETDEV}'.format(**gl(locals())))

print( "Bringing down TAP device...")
shell('sudo ifconfig {TAPDEV} down'.format(**gl(locals())))


print("Deleting TAP device {TAPDEV}... ".format(**gl(locals())))
shell('sudo tunctl -d {TAPDEV}'.format(**gl(locals())))

print("Done!")
