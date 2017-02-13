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

set -u

ARCHEND=%(ARCHEND)s
IID=%(IID)i

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

%(START_NET)s

function cleanup {
    pkill -P $$
    %(STOP_NET)s
}

trap cleanup EXIT

echo "Starting firmware emulation... use Ctrl-a + x to exit"
sleep 1s

%(QEMU_ENV_VARS)s ${QEMU} -m 256 -M ${QEMU_MACHINE} -kernel ${KERNEL} \\
    %(QEMU_DISK)s -append "root=${QEMU_ROOTFS} console=ttyS0 nandsim.parts=64,64,64,64,64,64,64,64,64,64 rdinit=/firmadyne/preInit.sh rw debug ignore_loglevel print-fatal-signals=1 user_debug=31 firmadyne.syscall=0" \\
    -nographic \\
    %(QEMU_NETWORK)s | tee ${WORK_DIR}/qemu.final.serial.log
"""

def stripTimestamps(data):
    lines = data.split("\n")
    #throw out the timestamps
    lines = [re.sub(r"^\[[^\]]*\] firmadyne: ", "", l) for l in lines]
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
        for p in [r"^br_dev_ioctl\[[^\]]+\]: br:%s dev:(.*)", r"^br_add_if\[[^\]]+\]: br:%s dev:(.*)"]:
            pat = p % brif
            g = re.match(pat, c)
            if g:
                iface = g.group(1)
                #we only add it if the interface is not the bridge itself
                #there are images that call brctl addif br0 br0 (e.g., 5152)
                if iface != brif:
                    result.append(iface.strip())
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
    return int(g.group(1)) if g else -1

def qemuArchNetworkConfig(i, arch, n):
    if not n:
        if arch == "arm":
            return "-device virtio-net-device,netdev=net%(I)i -netdev socket,id=net%(I)i,listen=:200%(I)i" % {'I': i}
        else:
            return "-net nic,vlan=%(VLAN)i -net socket,vlan=%(VLAN)i,listen=:200%(I)i" % {'I': i, 'VLAN' : i}
    else:
        (ip, dev, vlan, mac) = n
         # newer kernels use virtio only
        if arch == "arm":
            return "-device virtio-net-device,netdev=net%(I)i -netdev tap,id=net%(I)i,ifname=${TAPDEV_%(I)i},script=no" % {'I': i}
        else:
            vlan_id = vlan if vlan else i
            mac_str = "" if not mac else ",macaddr=%s" % mac
            return "-net nic,vlan=%(VLAN)i%(MAC)s -net tap,vlan=%(VLAN)i,id=net%(I)i,ifname=${TAPDEV_%(I)i},script=no" % { 'I' : i, 'MAC' : mac_str, 'VLAN' : vlan_id}

def qemuNetworkConfig(arch, network):
    output = []
    assigned = []
    for i in range(0, 4):
        for j, n in enumerate(network):
            # need to connect the jth emulated network interface to the corresponding host interface
            if i == ifaceNo(n[1]):
                output.append(qemuArchNetworkConfig(j, arch, n))
                assigned.append(n)
                break

        # otherwise, put placeholder socket connection
        if len(output) <= i:
            output.append(qemuArchNetworkConfig(i, arch, None))

    # find unassigned interfaces
    for j, n in enumerate(network):
        if n not in assigned:
            # guess assignment
            print("Warning: Unmatched interface: %s" % (n,))
            output[j] = qemuArchNetworkConfig(j, arch, n)
            assigned.append(n)

    return ' '.join(output)

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

def getIP(ip):
    tups = [int(x) for x in ip.split(".")]
    if tups[3] != 1:
        tups[3] -= 1
    else:
        tups[3] = 2
    return ".".join([str(x) for x in tups])

def startNetwork(network):
    template_1 = """
TAPDEV_%(I)i=tap${IID}_%(I)i
HOSTNETDEV_%(I)i=${TAPDEV_%(I)i}
echo "Creating TAP device ${TAPDEV_%(I)i}..."
sudo tunctl -t ${TAPDEV_%(I)i} -u ${USER}
"""

    template_vlan = """
echo "Initializing VLAN..."
HOSTNETDEV_%(I)i=${TAPDEV_%(I)i}.%(VLANID)i
sudo ip link add link ${TAPDEV_%(I)i} name ${HOSTNETDEV_%(I)i} type vlan id %(VLANID)i
sudo ip link set ${HOSTNETDEV_%(I)i} up
"""

    template_2 = """
echo "Bringing up TAP device..."
sudo ip link set ${HOSTNETDEV_%(I)i} up
sudo ip addr add %(HOSTIP)s/24 dev ${HOSTNETDEV_%(I)i}

echo "Adding route to %(GUESTIP)s..."
sudo ip route add %(GUESTIP)s via %(GUESTIP)s dev ${HOSTNETDEV_%(I)i}
"""

    output = []
    for i, (ip, dev, vlan, mac) in enumerate(network):
        output.append(template_1 % {'I' : i})
        if vlan:
            output.append(template_vlan % {'I' : i, 'VLANID' : vlan})
        output.append(template_2 % {'I' : i, 'HOSTIP' : getIP(ip), 'GUESTIP': ip})
    return '\n'.join(output)

def stopNetwork(network):
    template_1 = """
echo "Deleting route..."
sudo ip route flush dev ${HOSTNETDEV_%(I)i}

echo "Bringing down TAP device..."
sudo ip link set ${TAPDEV_%(I)i} down
"""

    template_vlan = """
echo "Removing VLAN..."
sudo ip link delete ${HOSTNETDEV_%(I)i}
"""

    template_2 = """
echo "Deleting TAP device ${TAPDEV_%(I)i}..."
sudo tunctl -d ${TAPDEV_%(I)i}
"""

    output = []
    for i, (ip, dev, vlan, mac) in enumerate(network):
        output.append(template_1 % {'I' : i})
        if vlan:
            output.append(template_vlan % {'I' : i})
        output.append(template_2 % {'I' : i})
    return '\n'.join(output)

def qemuCmd(iid, network, arch, endianness):
    if arch == "mips":
        qemuEnvVars = ""
        qemuDisk = "-drive if=ide,format=raw,file=${IMAGE}"
        if endianness != "eb" and endianness != "el":
            raise Exception("You didn't specify a valid endianness")
    elif arch == "arm":
        qemuDisk = "-drive if=none,file=${IMAGE},format=raw,id=rootfs -device virtio-blk-device,drive=rootfs"
        if endianness == "el":
            qemuEnvVars = "QEMU_AUDIO_DRV=none"
        elif endianness == "eb":
            raise Exception("armeb currently not supported")
        else:
            raise Exception("You didn't specify a valid endianness")
    else:
        raise Exception("Unsupported architecture")

    return QEMUCMDTEMPLATE % {'IID': iid,
                              'ARCHEND' : arch + endianness,
                              'START_NET' : startNetwork(network),
                              'STOP_NET' : stopNetwork(network),
                              'QEMU_DISK' : qemuDisk,
                              'QEMU_NETWORK' : qemuNetworkConfig(arch, network),
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
    pruned_network = []
    for n in network:
        if n[0] not in ips:
            ips.add(n[0])
            pruned_network.append(n)
        else:
            if debug:
                print("duplicate ip address for interface: ", n)

    if makeQemuCmd:
        qemuCommandLine = qemuCmd(iid, pruned_network, arch, endianness)
    if qemuCommandLine:
        success = True
    if outfile:
        with open(outfile, "w") as out:
            out.write(qemuCommandLine)
        os.chmod(outfile, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
    else:
        print(qemuCommandLine)

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
