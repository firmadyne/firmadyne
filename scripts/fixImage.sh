#!/bin/sh

# use busybox statically-compiled version of all binaries
BUSYBOX="/busybox"

# print input if not symlink, otherwise attempt to resolve symlink
resolve_link() {
    TARGET=$($BUSYBOX readlink $1)
    if [ -z "$TARGET" ]; then
        echo "$1"
    fi
    echo "$TARGET"
}

# make /etc and add some essential files
mkdir -p "$(resolve_link /etc)"
if [ ! -s /etc/TZ ]; then
    echo "Creating /etc/TZ!"
    mkdir -p "$(dirname $(resolve_link /etc/TZ))"
    echo "EST5EDT" > "$(resolve_link /etc/TZ)"
fi

if [ ! -s /etc/hosts ]; then
    echo "Creating /etc/hosts!"
    mkdir -p "$(dirname $(resolve_link /etc/hosts))"
    echo "127.0.0.1 localhost" > "$(resolve_link /etc/hosts)"
fi

if [ ! -s /etc/passwd ]; then
    echo "Creating /etc/passwd!"
    mkdir -p "$(dirname $(resolve_link /etc/passwd))"
    echo "root::0:0:root:/root:/bin/sh" > "$(resolve_link /etc/passwd)"
fi

# make /dev and add default device nodes if current /dev does not have greater
# than 5 device nodes
mkdir -p "$(resolve_link /dev)"
FILECOUNT="$($BUSYBOX find ${WORKDIR}/dev -maxdepth 1 -type b -o -type c -print | $BUSYBOX wc -l)"
if [ $FILECOUNT -lt "5" ]; then
    echo "Warning: Recreating device nodes!"

    mknod -m 660 /dev/mem c 1 1
    mknod -m 640 /dev/kmem c 1 2
    mknod -m 666 /dev/null c 1 3
    mknod -m 666 /dev/zero c 1 5
    mknod -m 444 /dev/random c 1 8
    mknod -m 444 /dev/urandom c 1 9
    mknod -m 666 /dev/armem c 1 13

    mknod -m 666 /dev/tty c 5 0
    mknod -m 622 /dev/console c 5 1
    mknod -m 666 /dev/ptmx c 5 2

    mknod -m 622 /dev/tty0 c 4 0
    mknod -m 660 /dev/ttyS0 c 4 64
    mknod -m 660 /dev/ttyS1 c 4 65
    mknod -m 660 /dev/ttyS2 c 4 66
    mknod -m 660 /dev/ttyS3 c 4 67

    mknod -m 644 /dev/adsl0 c 100 0
    mknod -m 644 /dev/ppp c 108 0
    mknod -m 666 /dev/hidraw0 c 251 0

    mkdir -p /dev/mtd
    mknod -m 644 /dev/mtd/0 c 90 0
    mknod -m 644 /dev/mtd/1 c 90 2
    mknod -m 644 /dev/mtd/2 c 90 4
    mknod -m 644 /dev/mtd/3 c 90 6
    mknod -m 644 /dev/mtd/4 c 90 8
    mknod -m 644 /dev/mtd/5 c 90 10
    mknod -m 644 /dev/mtd/6 c 90 12
    mknod -m 644 /dev/mtd/7 c 90 14
    mknod -m 644 /dev/mtd/8 c 90 16
    mknod -m 644 /dev/mtd/9 c 90 18
    mknod -m 644 /dev/mtd/10 c 90 20

    mknod -m 644 /dev/mtd0 c 90 0
    mknod -m 644 /dev/mtdr0 c 90 1
    mknod -m 644 /dev/mtd1 c 90 2
    mknod -m 644 /dev/mtdr1 c 90 3
    mknod -m 644 /dev/mtd2 c 90 4
    mknod -m 644 /dev/mtdr2 c 90 5
    mknod -m 644 /dev/mtd3 c 90 6
    mknod -m 644 /dev/mtdr3 c 90 7
    mknod -m 644 /dev/mtd4 c 90 8
    mknod -m 644 /dev/mtdr4 c 90 9
    mknod -m 644 /dev/mtd5 c 90 10
    mknod -m 644 /dev/mtdr5 c 90 11
    mknod -m 644 /dev/mtd6 c 90 12
    mknod -m 644 /dev/mtdr6 c 90 13
    mknod -m 644 /dev/mtd7 c 90 14
    mknod -m 644 /dev/mtdr7 c 90 15
    mknod -m 644 /dev/mtd8 c 90 16
    mknod -m 644 /dev/mtdr8 c 90 17
    mknod -m 644 /dev/mtd9 c 90 18
    mknod -m 644 /dev/mtdr9 c 90 19
    mknod -m 644 /dev/mtd10 c 90 20
    mknod -m 644 /dev/mtdr10 c 90 21

    mkdir -p /dev/mtdblock
    mknod -m 644 /dev/mtdblock/0 b 31 0
    mknod -m 644 /dev/mtdblock/1 b 31 1
    mknod -m 644 /dev/mtdblock/2 b 31 2
    mknod -m 644 /dev/mtdblock/3 b 31 3
    mknod -m 644 /dev/mtdblock/4 b 31 4
    mknod -m 644 /dev/mtdblock/5 b 31 5
    mknod -m 644 /dev/mtdblock/6 b 31 6
    mknod -m 644 /dev/mtdblock/7 b 31 7
    mknod -m 644 /dev/mtdblock/8 b 31 8
    mknod -m 644 /dev/mtdblock/9 b 31 9
    mknod -m 644 /dev/mtdblock/10 b 31 10

    mknod -m 644 /dev/mtdblock0 b 31 0
    mknod -m 644 /dev/mtdblock1 b 31 1
    mknod -m 644 /dev/mtdblock2 b 31 2
    mknod -m 644 /dev/mtdblock3 b 31 3
    mknod -m 644 /dev/mtdblock4 b 31 4
    mknod -m 644 /dev/mtdblock5 b 31 5
    mknod -m 644 /dev/mtdblock6 b 31 6
    mknod -m 644 /dev/mtdblock7 b 31 7
    mknod -m 644 /dev/mtdblock8 b 31 8
    mknod -m 644 /dev/mtdblock9 b 31 9
    mknod -m 644 /dev/mtdblock10 b 31 10

    mkdir -p /dev/tts
    mknod -m 660 /dev/tts/0 c 4 64
    mknod -m 660 /dev/tts/1 c 4 65
    mknod -m 660 /dev/tts/2 c 4 66
    mknod -m 660 /dev/tts/3 c 4 67
fi

# create a gpio file required for linksys to make the watchdog happy
if ($BUSYBOX grep -sq "/dev/gpio/in" /bin/gpio) ||
  ($BUSYBOX grep -sq "/dev/gpio/in" /usr/lib/libcm.so) ||
  ($BUSYBOX grep -sq "/dev/gpio/in" /usr/lib/libshared.so); then
    echo "Creating /dev/gpio/in!"
    mkdir -p /dev/gpio
    echo -ne "\xff\xff\xff\xff" > /dev/gpio/in
fi

# prevent system from rebooting
#echo "Removing /sbin/reboot!"
#rm -f /sbin/reboot
echo "Removing /etc/scripts/sys_resetbutton!"
rm -f /etc/scripts/sys_resetbutton

# add some default nvram entries
if $BUSYBOX grep -sq "ipv6_6to4_lan_ip" /sbin/rc; then
    echo "Creating default ipv6_6to4_lan_ip!"
    echo -n "2002:7f00:0001::" > /firmadyne/libnvram.override/ipv6_6to4_lan_ip
fi

if $BUSYBOX grep -sq "time_zone_x" /lib/libacos_shared.so; then
    echo "Creating default time_zone_x!"
    echo -n "0" > /firmadyne/libnvram.override/time_zone_x
fi

if $BUSYBOX grep -sq "rip_multicast" /usr/sbin/httpd; then
    echo "Creating default rip_multicast!"
    echo -n "0" > /firmadyne/libnvram.override/rip_multicast
fi

if $BUSYBOX grep -sq "bs_trustedip_enable" /usr/sbin/httpd; then
    echo "Creating default bs_trustedip_enable!"
    echo -n "0" > /firmadyne/libnvram.override/bs_trustedip_enable
fi

if $BUSYBOX grep -sq "filter_rule_tbl" /usr/sbin/httpd; then
    echo "Creating default filter_rule_tbl!"
    echo -n "" > /firmadyne/libnvram.override/filter_rule_tbl
fi

if $BUSYBOX grep -sq "rip_enable" /sbin/acos_service; then
    echo "Creating default rip_enable!"
    echo -n "0" > /firmadyne/libnvram.override/rip_enable
fi
