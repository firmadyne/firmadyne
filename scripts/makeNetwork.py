#!/usr/bin/env python

import sys
import getopt
import re
import struct
import socket
import stat
import os

debug = 0

QEMUCMDTEMPLATE = """#!/bin/bash

set -e
set -u

ARCHEND=%(ARCHEND)s
IID=%(IID)i
GUESTIP=%(GUESTIP)s
NETDEVIP=%(NETDEVIP)s
HASVLAN=%(HASVLAN)i
VLANID=%(VLANID)i

TAPDEV=tap${IID}
HOSTNETDEV=${TAPDEV}

if [ -e ./firmadyne.config ]; then
    source ./firmadyne.config
elif [ -e ../firmadyne.config ]; then
    source ../firmadyne.config
elif [ -e ../../firmadyne.config ]; then
    source ../../firmadyne.config
else
    echo "Error: Could not find 'firmadyne.config'!"
    exit 1
fi

IMAGE=`get_fs ${IID}`
KERNEL=`get_kernel ${ARCHEND}`
QEMU=`get_qemu ${ARCHEND}`
QEMU_MACHINE=`get_qemu_machine ${ARCHEND}`
QEMU_ROOTFS=`get_qemu_disk ${ARCHEND}`
WORK_DIR=`get_scratch ${IID}`

echo "Creating TAP device ${TAPDEV}..."
sudo tunctl -t ${TAPDEV} -u ${USER}

if [ ${HASVLAN} -ne 0 ]; then
    echo "Initializing VLAN..."
    sudo vconfig add ${TAPDEV} ${VLANID}
    sudo ifconfig ${TAPDEV} 0.0.0.0 up
    HOSTNETDEV=${TAPDEV}.${VLANID}
fi

echo "Bringing up TAP device..."
sudo ifconfig ${HOSTNETDEV} ${NETDEVIP}/24 up

echo "Adding route to ${GUESTIP}..."
sudo route add -host ${GUESTIP} gw ${GUESTIP} ${HOSTNETDEV}

echo -n "Starting emulation of firmware... "
%(QEMU_ENV_VARS)s${QEMU} -m 256 -M ${QEMU_MACHINE} -kernel ${KERNEL} \\
    %(QEMU_DISK)s -append "root=${QEMU_ROOTFS} console=ttyS0 nandsim.parts=64,64,64,64,64,64,64,64,64,64 rdinit=/preInit.sh rw debug ignore_loglevel print-fatal-signals=1 user_debug=31 firmadyne.syscall=8" \\
    -serial file:${WORK_DIR}/qemu.final.serial.log \\
    -serial unix:/tmp/qemu.${IID}.S1,server,nowait \\
    -monitor unix:/tmp/qemu.${IID},server,nowait \\
    -display none \\
    -daemonize \\
    %(QEMU_NETWORK)s

echo "Done!"

echo "The emulated firmware may not be accessible while booting."

echo "Press any key to destroy the network and shutdown emulation."

read -n 1

killall ${QEMU}

echo "Deleting route..."
sudo route del -host ${GUESTIP} gw ${GUESTIP} ${HOSTNETDEV}

echo "Bringing down TAP device..."
sudo ifconfig ${TAPDEV} down

if [ ${HASVLAN} -ne 0 ]
then
    echo "Removing VLAN..."
    sudo vconfig rem ${HOSTNETDEV}
fi

echo -n "Deleting TAP device ${TAPDEV}... "
sudo tunctl -d ${TAPDEV}

echo "Done!"
"""

def stripTimestamps(data):
    lines = data.split("\r\n")
    #throw out the timestamps
    lines = [re.sub(r"^\[[^]]*] firmadyne: ", "", l) for l in lines]
    return lines

def findMacChanges(data, endianness):
    lines = stripTimestamps(data)
    candidates = filter(lambda l: l.startswith("ioctl_SIOCSIFHWADDR"), lines)
    if debug:
        print("Mac Changes %r" % candidates)

    result = []
    if endianness == "eb":
        fmt = ">I"
    elif endianness == "el":
        fmt = "<I"
    for c in candidates:
        g = re.match(r"^ioctl_SIOCSIFHWADDR\[[^\]]+\]: dev:([^ ]+) mac:0x([0-9a-f]+) 0x([0-9a-f]+)", c)
        if g:
            (iface, mac0, mac1) = g.groups()
            m0 = struct.pack(fmt, int(mac0, 16))[2:]
            m1 = struct.pack(fmt, int(mac1, 16))
            mac = "%02x:%02x:%02x:%02x:%02x:%02x" % struct.unpack("BBBBBB", m0+m1)
            result.append((iface, mac))
    return result

# Get the netwokr interfaces in the router, except 127.0.0.1
def findNonLoInterfaces(data, endianness):
    #lines = data.split("\r\n")
    lines = stripTimestamps(data)
    candidates = filter(lambda l: l.startswith("__inet_insert_ifa"), lines) # logs for the inconfig process
    if debug:
        print("Candidate ifaces: %r" % candidates)
    result = []
    if endianness == "eb":
        fmt = ">I"
    elif endianness == "el":
        fmt = "<I"
    for c in candidates:
        g = re.match(r"^__inet_insert_ifa\[[^\]]+\]: device:([^ ]+) ifa:0x([0-9a-f]+)", c)
        if g:
            (iface, addr) = g.groups()
            addr = socket.inet_ntoa(struct.pack(fmt, int(addr, 16)))
            if addr != "127.0.0.1" and addr != "0.0.0.0":
                result.append((iface, addr))
    return result

def findIfacesForBridge(data, brif):
    #lines = data.split("\r\n")
    lines = stripTimestamps(data)
    result = []
    candidates = filter(lambda l: l.startswith("br_dev_ioctl") or l.startswith("br_add_if"), lines)
    for c in candidates:
        pat = r"^br_dev_ioctl\[[^\]]+\]: br:%s dev:(.*)" % brif
        g = re.match(pat, c)
        if g:
            iface = g.group(1)
            #we only add it if the interface is not the bridge itself
            #there are images that call brctl addif br0 br0 (e.g., 5152)
            if iface != brif:
                result.append(g.group(1))
        pat = r"^br_add_if\[[^\]]+\]: br:%s dev:(.*)" % brif
        g = re.match(pat, c)
        if g:
            iface = g.group(1)
            if iface != brif:
                result.append(g.group(1))
    return result

def findVlanInfoForDev(data, dev):
    #lines = data.split("\r\n")
    lines = stripTimestamps(data)
    results = []
    candidates = filter(lambda l: l.startswith("register_vlan_dev"), lines)
    for c in candidates:
        g = re.match(r"register_vlan_dev\[[^\]]+\]: dev:%s vlan_id:([0-9]+)" % dev, c)
        if g:
            results.append(int(g.group(1)))
    return results

def ifaceNo(dev):
    g = re.match(r"[^0-9]+([0-9]+)", dev)
    return int(g.group(1))

def qemuNetworkConfig(dev, mac):
    result = ""
    mac_str = ""
    if mac:
        mac_str = ",macaddr=%s" % mac
    template = """-net nic,vlan=%i -net socket,vlan=%i,listen=:200%i """
    for i in range(0, 4):
        if i == ifaceNo(dev):
            result += "-net nic,vlan=%i%s -net tap,vlan=%i,ifname=${TAPDEV},script=no " % (i, mac_str, i)
        else:
            result += template % (i, i, i)

    return result

def buildConfig(brif, iface, vlans, macs):
    #there should be only one ip
    ip = brif[1]
    br = brif[0]

    #strip vlanid from interface name (e.g., eth2.2 -> eth2)
    dev = iface.split(".")[0]

    #check whether there is a different mac set
    mac = None
    d = dict(macs)
    if br in d:
        mac = d[br]
    elif dev in d:
        mac = d[dev]

    vlan_id = None
    if len(vlans):
        vlan_id = vlans[0]

    return (ip, dev, vlan_id, mac)

def closeIp(ip):
    tups = [int(x) for x in ip.split(".")]
    if tups[3] != 1:
        tups[3] -= 1
    else:
        tups[3] = 2
    return ".".join([str(x) for x in tups])

def qemuCmd(iid, network, arch, endianness):
    (ip, netdev, vlan_id, mac) = network
    if vlan_id != None:
        hasVlan = 1
    else:
        hasVlan = 0
        vlan_id = -1

    if arch == "mips":
        qemuEnvVars = ""
        qemuDisk = "-drive if=ide,format=raw,file=${IMAGE}"
        if endianness != "eb" and endianness != "el":
            raise Exception("You didn't specify a valid endianness")

    elif arch == "arm":
        qemuDisk = "-drive if=none,file=${IMAGE},format=raw,id=rootfs -device virtio-blk-device,drive=rootfs"
        if endianness == "el":
            qemuEnvVars = "QEMU_AUDIO_DRV=none "
        elif endianness == "eb":
            raise Exception("armeb currently not supported")
        else:
            raise Exception("You didn't specify a valid endianness")
    else:
        raise Exception("Unsupported architecture")

    return QEMUCMDTEMPLATE % {'IID': iid, 'GUESTIP': ip, 'NETDEVIP': closeIp(ip),
                              'HASVLAN' : hasVlan, 'VLANID': vlan_id,
                              'ARCHEND' : arch + endianness,
                              'QEMU_DISK' : qemuDisk,
                              'QEMU_NETWORK' : qemuNetworkConfig(netdev, mac),
                              'QEMU_ENV_VARS' : qemuEnvVars}

def process(infile, iid, arch, endianness=None, makeQemuCmd=False, outfile=None):
    brifs = []
    vlans = []
    data = open(infile).read()
    network = set()
    success = False

    #find interfaces with non loopback ip addresses
    ifacesWithIps = findNonLoInterfaces(data, endianness)

    #find changes of mac addresses for devices
    macChanges = findMacChanges(data, endianness)

    print("Interfaces: %r" % ifacesWithIps)

    deviceHasBridge = False
    for iwi in ifacesWithIps:
        #find all interfaces that are bridged with that interface
        brifs = findIfacesForBridge(data, iwi[0])
        if debug:
            print("brifs for %s %r" % (iwi[0], brifs))
        for dev in brifs:
            #find vlan_ids for all interfaces in the bridge
            vlans = findVlanInfoForDev(data, dev)
            #create a config for each tuple
            network.add((buildConfig(iwi, dev, vlans, macChanges)))
            deviceHasBridge = True

        #if there is no bridge just add the interface
        if not brifs and not deviceHasBridge:
            vlans = findVlanInfoForDev(data, iwi[0])
            network.add((buildConfig(iwi, iwi[0], vlans, macChanges)))

    ips = set()
    for n in network:
        if n[0] not in ips:
            ips.add(n[0])
            #print n
            if makeQemuCmd:
                qemuCommandLine = qemuCmd(iid, n, arch, endianness)
                if qemuCommandLine:
                    success = True
                if outfile:
                    with open(outfile, "w") as out:
                        out.write(qemuCommandLine)
                    os.chmod(outfile, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                else:
                    print(qemuCommandLine)
        else:
            if debug:
                print("duplicate ip address for interface: ", n)
    return success

def archEnd(value):
    arch = None
    end = None

    tmp = value.lower()
    if tmp.startswith("mips"):
        arch = "mips"
    elif tmp.startswith("arm"):
        arch = "arm"
    if tmp.endswith("el"):
        end = "el"
    elif tmp.endswith("eb"):
        end = "eb"
    return (arch, end)

def main():
    infile = None
    makeQemuCmd = False
    iid = None
    outfile = None
    arch = None
    endianness = None
    (opts, argv) = getopt.getopt(sys.argv[1:], 'f:i:S:a:oqd')
    for (k, v) in opts:
        if k == '-f':
            infile = v
        if k == '-d':
            global debug
            debug += 1
        if k == '-q':
            makeQemuCmd = True
        if k == '-i':
            iid = int(v)
        if k == '-S':
            SCRATCHDIR = v
        if k == '-o':
            outfile = True
        if k == '-a':
            (arch, endianness) = archEnd(v)

    if not arch or not endianness:
        raise Exception("Either arch or endianness not found try mipsel/mipseb/armel/armeb")

    if not infile and iid:
        infile = "%s/%i/qemu.initial.serial.log" % (SCRATCHDIR, iid)
    if outfile and iid:
        outfile = """%s/%i/run.sh""" % (SCRATCHDIR, iid)
    if debug:
        print("processing %i" % iid)
    if infile:
        process(infile, iid, arch, endianness, makeQemuCmd, outfile)

if __name__ == "__main__":
    main()
