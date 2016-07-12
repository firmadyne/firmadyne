#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from os import path
import sys
import pdb
import traceback
import psycopg2
import re
import time
from urllib import request
import subprocess
from shellutils import shell

conn = psycopg2.connect(database="firmware", user="firmadyne", 
        password="firmadyne", host="127.0.0.1")
cur = conn.cursor()

FIRMWARE_DIR = path.dirname(path.dirname(path.realpath(__file__)))
BINARY_DIR=path.join(FIRMWARE_DIR,'binaries')
TARBALL_DIR=path.join(FIRMWARE_DIR,'images')
SCRATCH_DIR=path.join(FIRMWARE_DIR,'scratch')
SCRIPT_DIR=path.join(FIRMWARE_DIR,'scripts')

def gl(localvars):
    d=globals()
    d.update(localvars)
    return d


def get_kernel(archend):
    if archend=='armel':
        return path.join(BINARY_DIR,'zImage.%s'%archend)
    elif archend=='mipsel' or archend=='mipseb':
        return path.join(BINARY_DIR,'vmlinux.%s'%archend)
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
    return path.join(SCRATCH_DIR, '%d'%iid)
def get_fs(iid):
    return path.join(get_scratch(iid),'image.raw')
def closeIp(ip):
    tups = [int(x) for x in ip.split(".")]
    if tups[3] != 1:
        tups[3] -= 1
    else:
        tups[3] = 2
    return ".".join([str(x) for x in tups])



if len(sys.argv)<2:
    print("usage: \n\
            %s {IID}"%(sys.argv[0]))
    sys.exit()
IID = int(sys.argv[1])
cur.execute("SELECT arch FROM image WHERE id=%s"%IID)
ARCHEND = cur.fetchone()[0]
cur.execute("SELECT guest_ip FROM image WHERE id=%d"%IID)
GUESTIP = cur.fetchone()[0]
NETDEVIP=closeIp(GUESTIP)
TAPDEV='tap%d'%IID
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

def ifaceNo(dev):
    g = re.match(r"[^0-9]+([0-9]+)", dev)
    return int(g.group(1))
def qemuNetworkConfig(dev):
    result = ""
    for i in range(0, 4):
        if i == ifaceNo(dev):
            result += "-net nic,vlan=%i -net tap,vlan=%i,ifname={TAPDEV},script=no ".format(**gl(locals())) \
                    % (i, i)
        else:
            result += "-net nic,vlan=%i -net socket,vlan=%i,listen=:200%i "% (i, i, i)
    return result

print("Starting emulation of firmware... ")
if ARCHEND=='mipsel' or ARCHEND=='mipseb':
    qemuEnvVars=""
    qemuDisk = "-drive if=ide,format=raw,file={IMAGE}".format(**locals())
elif ARCHEND=='armel':
    qemuEnvVars = "QEMU_AUDIO_DRV=none "
    qemuDisk = "-drive if=none,file={IMAGE},format=raw,id=rootfs -device virtio-blk-device,drive=rootfs".format(**locals())
cur.execute("SELECT netdev FROM image WHERE id=%d"%IID)
netdev=cur.fetchone()[0]
qemuNetwork=qemuNetworkConfig(netdev)


shell('''{qemuEnvVars} {QEMU} -m 256 -M {QEMU_MACHINE} -kernel {KERNEL} \
        {qemuDisk} -append "root={QEMU_ROOTFS} console=ttyS0 \
        nandsim.parts=64,64,64,64,64,64,64,64,64,64 rdinit=/preInit.sh rw debug ignore_loglevel \
        print-fatal-signals=1 user_debug=31 firmadyne.syscall=8" \
        -serial file:{WORK_DIR}/qemu.final.serial.log \
        -display none \
        -daemonize \
        {qemuNetwork}'''.format(**gl(locals())))

# the good sleep time depends on the time whether eth1 appear in the serial.log
time.sleep(10)
network_reachable=False
try:
    with request.urlopen('http://{GUESTIP}/'.format(**gl(locals())), timeout=10) as fin:
        htmlsrc = fin.readall().decode('utf8')
        if len(htmlsrc)>0:
            network_reachable=True
except Exception as ex:
    pass
print('network_reachable=%s'%network_reachable)
cur.execute("UPDATE image SET network_reachable=%s WHERE id=%s", 
        (network_reachable, IID))
conn.commit()


shell('killall {QEMU}'.format(**gl(locals())))

print( "Deleting route...")
shell('sudo route del -host {GUESTIP} gw {GUESTIP} {HOSTNETDEV}'.format(**gl(locals())))

print( "Bringing down TAP device...")
shell('sudo ifconfig {TAPDEV} down'.format(**gl(locals())))


print("Deleting TAP device {TAPDEV}... ".format(**gl(locals())))
shell('sudo tunctl -d {TAPDEV}'.format(**gl(locals())))

print("Done!")
