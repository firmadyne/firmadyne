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

backup_file(){
    if [ -f "$1" ]; then
        echo "Backing up $1 to ${1}.bak"
        $BUSYBOX cp "$1" "${1}.bak"
    fi
}

rename_file(){
    if [ -f "$1" ]; then
        echo "Renaming $1 to ${1}.bak"
        $BUSYBOX mv "$1" "${1}.bak"
    fi
}

remove_file(){
    if [ -f "$1" ]; then
        echo "Removing $1"
        $BUSYBOX rm -f "$1"
    fi
}
# make /etc and add some essential files
$BUSYBOX mkdir -p "$(resolve_link /etc)"
if [ ! -s /etc/TZ ]; then
    echo "Creating /etc/TZ!"
    $BUSYBOX mkdir -p "$(dirname $(resolve_link /etc/TZ))"
    echo "EST5EDT" > "$(resolve_link /etc/TZ)"
fi

if [ ! -s /etc/hosts ]; then
    echo "Creating /etc/hosts!"
    $BUSYBOX mkdir -p "$(dirname $(resolve_link /etc/hosts))"
    echo "127.0.0.1 localhost" > "$(resolve_link /etc/hosts)"
fi

PASSWD=$(resolve_link /etc/passwd)
SHADOW=$(resolve_link /etc/shadow)
if [ ! -s "$PASSWD" ]; then
    echo "Creating $PASSWD!"
    $BUSYBOX mkdir -p "$(dirname $PASSWD)"
    echo "root::0:0:root:/root:/bin/sh" > "$PASSWD"
else
    backup_file $PASSWD
    backup_file $SHADOW
    if ! $BUSYBOX grep -sq "^root:" $PASSWD ; then
        echo "No root user found, creating root user with shell '/bin/sh'"
        echo "root::0:0:root:/root:/bin/sh" > "$PASSWD"
        $BUSYBOX [ ! -d '/root' ] && $BUSYBOX mkdir /root
    fi

    if [ -z "$($BUSYBOX grep -Es '^root:' $PASSWD |$BUSYBOX grep -Es ':/bin/sh$')" ] ; then
        echo "Fixing shell for root user"
        $BUSYBOX sed -ir 's/^(root:.*):[^:]+$/\1:\/bin\/sh/' $PASSWD
    fi

    if [ ! -z "$($BUSYBOX grep -Es '^root:[^:]+' $PASSWD)" -o ! -z "$($BUSYBOX grep -Es '^root:[^:]+' $SHADOW)" ]; then
        echo "Unlocking and blanking default root password. (*May not work since some routers reset the password back to default when booting)"
        $BUSYBOX sed -ir 's/^(root:)[^:]+:/\1:/' $PASSWD
        $BUSYBOX sed -ir 's/^(root:)[^:]+:/\1:/' $SHADOW
    fi
fi

# make /dev and add default device nodes if current /dev does not have greater
# than 5 device nodes
$BUSYBOX mkdir -p "$(resolve_link /dev)"
FILECOUNT="$($BUSYBOX find ${WORKDIR}/dev -maxdepth 1 -type b -o -type c -print | $BUSYBOX wc -l)"
if [ $FILECOUNT -lt "5" ]; then
    echo "Warning: Recreating device nodes!"

    $BUSYBOX mknod -m 660 /dev/mem c 1 1
    $BUSYBOX mknod -m 640 /dev/kmem c 1 2
    $BUSYBOX mknod -m 666 /dev/null c 1 3
    $BUSYBOX mknod -m 666 /dev/zero c 1 5
    $BUSYBOX mknod -m 444 /dev/random c 1 8
    $BUSYBOX mknod -m 444 /dev/urandom c 1 9
    $BUSYBOX mknod -m 666 /dev/armem c 1 13

    $BUSYBOX mknod -m 666 /dev/tty c 5 0
    $BUSYBOX mknod -m 622 /dev/console c 5 1
    $BUSYBOX mknod -m 666 /dev/ptmx c 5 2

    $BUSYBOX mknod -m 622 /dev/tty0 c 4 0
    $BUSYBOX mknod -m 660 /dev/ttyS0 c 4 64
    $BUSYBOX mknod -m 660 /dev/ttyS1 c 4 65
    $BUSYBOX mknod -m 660 /dev/ttyS2 c 4 66
    $BUSYBOX mknod -m 660 /dev/ttyS3 c 4 67

    $BUSYBOX mknod -m 644 /dev/adsl0 c 100 0
    $BUSYBOX mknod -m 644 /dev/ppp c 108 0
    $BUSYBOX mknod -m 666 /dev/hidraw0 c 251 0

    $BUSYBOX mkdir -p /dev/mtd
    $BUSYBOX mknod -m 644 /dev/mtd/0 c 90 0
    $BUSYBOX mknod -m 644 /dev/mtd/1 c 90 2
    $BUSYBOX mknod -m 644 /dev/mtd/2 c 90 4
    $BUSYBOX mknod -m 644 /dev/mtd/3 c 90 6
    $BUSYBOX mknod -m 644 /dev/mtd/4 c 90 8
    $BUSYBOX mknod -m 644 /dev/mtd/5 c 90 10
    $BUSYBOX mknod -m 644 /dev/mtd/6 c 90 12
    $BUSYBOX mknod -m 644 /dev/mtd/7 c 90 14
    $BUSYBOX mknod -m 644 /dev/mtd/8 c 90 16
    $BUSYBOX mknod -m 644 /dev/mtd/9 c 90 18
    $BUSYBOX mknod -m 644 /dev/mtd/10 c 90 20

    $BUSYBOX mknod -m 644 /dev/mtd0 c 90 0
    $BUSYBOX mknod -m 644 /dev/mtdr0 c 90 1
    $BUSYBOX mknod -m 644 /dev/mtd1 c 90 2
    $BUSYBOX mknod -m 644 /dev/mtdr1 c 90 3
    $BUSYBOX mknod -m 644 /dev/mtd2 c 90 4
    $BUSYBOX mknod -m 644 /dev/mtdr2 c 90 5
    $BUSYBOX mknod -m 644 /dev/mtd3 c 90 6
    $BUSYBOX mknod -m 644 /dev/mtdr3 c 90 7
    $BUSYBOX mknod -m 644 /dev/mtd4 c 90 8
    $BUSYBOX mknod -m 644 /dev/mtdr4 c 90 9
    $BUSYBOX mknod -m 644 /dev/mtd5 c 90 10
    $BUSYBOX mknod -m 644 /dev/mtdr5 c 90 11
    $BUSYBOX mknod -m 644 /dev/mtd6 c 90 12
    $BUSYBOX mknod -m 644 /dev/mtdr6 c 90 13
    $BUSYBOX mknod -m 644 /dev/mtd7 c 90 14
    $BUSYBOX mknod -m 644 /dev/mtdr7 c 90 15
    $BUSYBOX mknod -m 644 /dev/mtd8 c 90 16
    $BUSYBOX mknod -m 644 /dev/mtdr8 c 90 17
    $BUSYBOX mknod -m 644 /dev/mtd9 c 90 18
    $BUSYBOX mknod -m 644 /dev/mtdr9 c 90 19
    $BUSYBOX mknod -m 644 /dev/mtd10 c 90 20
    $BUSYBOX mknod -m 644 /dev/mtdr10 c 90 21

    $BUSYBOX mkdir -p /dev/mtdblock
    $BUSYBOX mknod -m 644 /dev/mtdblock/0 b 31 0
    $BUSYBOX mknod -m 644 /dev/mtdblock/1 b 31 1
    $BUSYBOX mknod -m 644 /dev/mtdblock/2 b 31 2
    $BUSYBOX mknod -m 644 /dev/mtdblock/3 b 31 3
    $BUSYBOX mknod -m 644 /dev/mtdblock/4 b 31 4
    $BUSYBOX mknod -m 644 /dev/mtdblock/5 b 31 5
    $BUSYBOX mknod -m 644 /dev/mtdblock/6 b 31 6
    $BUSYBOX mknod -m 644 /dev/mtdblock/7 b 31 7
    $BUSYBOX mknod -m 644 /dev/mtdblock/8 b 31 8
    $BUSYBOX mknod -m 644 /dev/mtdblock/9 b 31 9
    $BUSYBOX mknod -m 644 /dev/mtdblock/10 b 31 10

    $BUSYBOX mknod -m 644 /dev/mtdblock0 b 31 0
    $BUSYBOX mknod -m 644 /dev/mtdblock1 b 31 1
    $BUSYBOX mknod -m 644 /dev/mtdblock2 b 31 2
    $BUSYBOX mknod -m 644 /dev/mtdblock3 b 31 3
    $BUSYBOX mknod -m 644 /dev/mtdblock4 b 31 4
    $BUSYBOX mknod -m 644 /dev/mtdblock5 b 31 5
    $BUSYBOX mknod -m 644 /dev/mtdblock6 b 31 6
    $BUSYBOX mknod -m 644 /dev/mtdblock7 b 31 7
    $BUSYBOX mknod -m 644 /dev/mtdblock8 b 31 8
    $BUSYBOX mknod -m 644 /dev/mtdblock9 b 31 9
    $BUSYBOX mknod -m 644 /dev/mtdblock10 b 31 10

    $BUSYBOX mkdir -p /dev/tts
    $BUSYBOX mknod -m 660 /dev/tts/0 c 4 64
    $BUSYBOX mknod -m 660 /dev/tts/1 c 4 65
    $BUSYBOX mknod -m 660 /dev/tts/2 c 4 66
    $BUSYBOX mknod -m 660 /dev/tts/3 c 4 67
fi

# create a gpio file required for linksys to make the watchdog happy
if ($BUSYBOX grep -sq "/dev/gpio/in" /bin/gpio) ||
  ($BUSYBOX grep -sq "/dev/gpio/in" /usr/lib/libcm.so) ||
  ($BUSYBOX grep -sq "/dev/gpio/in" /usr/lib/libshared.so); then
    echo "Creating /dev/gpio/in!"
    $BUSYBOX mkdir -p /dev/gpio
    echo -ne "\xff\xff\xff\xff" > /dev/gpio/in
fi

# prevent system from rebooting
#echo "Removing /sbin/reboot!"
#rm -f /sbin/reboot
remove_file /etc/scripts/sys_resetbutton

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

rename_file /etc/securetty
