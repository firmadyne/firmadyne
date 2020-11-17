# Table of Contents

- [Table of Contents](#table-of-contents)
- [Introduction](#introduction)
- [Setup](#setup)
  - [Extractor](#extractor)
  - [Database](#database)
  - [Binaries](#binaries)
  - [QEMU](#qemu)
- [Usage](#usage)
- [FAQ](#faq)
  - [QEMU outputs empty log for ARM device](#qemu-outputs-empty-log-for-arm-device)
  - [run.sh is not generated](#runsh-is-not-generated)
  - [Log ends with "Kernel panic - not syncing: No working init found"](#log-ends-with-kernel-panic---not-syncing-no-working-init-found)
  - [A process crashed, e.g. do_page_fault() #2: sending SIGSEGV for invalid read access from 00000000](#a-process-crashed-eg-do_page_fault-2-sending-sigsegv-for-invalid-read-access-from-00000000)
  - [How do I debug the emulated firmware?](#how-do-i-debug-the-emulated-firmware)
- [Compiling from Source](#compiling-from-source)
  - [Toolchain](#toolchain)
  - [console](#console)
  - [libnvram](#libnvram)
  - [Kernel](#kernel)
    - [ARM](#arm)
    - [MIPS](#mips)
- [Database](#database-1)
  - [Data](#data)
  - [Schema](#schema)
- [Paper](#paper)

# Introduction

FIRMADYNE is an automated and scalable system for performing emulation and
dynamic analysis of Linux-based embedded firmware. It includes the following
components:

* modified kernels (MIPS: [v2.6](https://github.com/firmadyne/kernel-v2.6),
ARM: [v4.1](https://github.com/firmadyne/kernel-v4.1),
[v3.10](https://github.com/firmadyne/kernel-v3.10)) for instrumentation of
firmware execution;
* a userspace [NVRAM library](https://github.com/firmadyne/libnvram) to emulate
a hardware NVRAM peripheral;
* an [extractor](https://github.com/firmadyne/extractor) to extract a
filesystem and kernel from downloaded firmware;
* a small [console](https://github.com/firmadyne/console) application to spawn
an additional shell for debugging;
* and a [scraper](https://github.com/firmadyne/scraper) to download firmware from
42+ different vendors.

We have also written the following three basic automated analyses
using the FIRMADYNE system.

* Accessible Webpages: This script iterates through each file
within the filesystem of a firmware image that appears to be served by a
webserver, and aggregates the results based on whether they appear to required
authentication.
* SNMP Information: This script dumps the contents of the
`public` and `private` SNMP v2c communities to disk using no credentials.
* Vulnerability Check: This script tests for the presence
of 60 known vulnerabilities using exploits from Metasploit. In addition, it
also checks for 14 previously-unknown vulnerbailities that we discovered.
For more information, including affected products and CVE's, refer to
[analyses/README.md](https://github.com/firmadyne/firmadyne/blob/master/analyses/README.md).

In our 2016 [Network and Distributed System Security Symposium (NDSS)](http://www.internetsociety.org/events/ndss-symposium)
paper, titled [Towards Automated Dynamic Analysis for Linux-based Embedded Firmware](https://github.com/firmadyne/firmadyne/blob/master/paper/paper.pdf), we evaluated the FIRMADYNE
system over a dataset of 23,035 firmware images, of which we were able to
extract 9,486. Using 60 exploits from the [Metasploit Framework](https://github.com/rapid7/metasploit-framework),
and 14 previously-unknown vulnerabilities that we discovered, we showed that
846 out of 1,971 (43%) firmware images were vulnerable to at least one exploit,
which we estimate to affect 89+ different products. For more details, refer to
our paper linked above.

**Note**: This project is a research tool, and is currently not production ready.
In particular, some components are quite immature and rough. We suggest
running the system within a virtual machine. No support is offered, but pull
requests are greatly appreciated, whether for documentation, tests, or code!

# Setup

First, clone this repository recursively and install its dependencies.

1. `sudo apt-get install busybox-static fakeroot git dmsetup kpartx netcat-openbsd nmap python-psycopg2 python3-psycopg2 snmp uml-utilities util-linux vlan`
2. `git clone --recursive https://github.com/firmadyne/firmadyne.git`

## Extractor

The extractor depends on the [binwalk](https://github.com/ReFirmLabs/binwalk)
tool, so we need to install that and its dependencies.

1. `git clone https://github.com/ReFirmLabs/binwalk.git`
2. `cd binwalk`
2. `sudo ./deps.sh`
3. `sudo python ./setup.py install`
  * For Python 2.x, `sudo apt-get install python-lzma`
4. `sudo -H pip install git+https://github.com/ahupp/python-magic`
5. `sudo -H pip install git+https://github.com/sviehb/jefferson`.
6. Optionally, instead of [upstream sasquatch](https://github.com/devttys0/sasquatch),
our [sasquatch fork](https://github.com/firmadyne/sasquatch) can be used to
prevent false positives by making errors fatal.

## Database

Next, install, set up, and configure the database.

1. `sudo apt-get install postgresql`
2. `sudo -u postgres createuser -P firmadyne`, with password `firmadyne`
3. `sudo -u postgres createdb -O firmadyne firmware`
4. `sudo -u postgres psql -d firmware < ./firmadyne/database/schema`

## Binaries

To download our pre-built binaries for all components, run the following script:

* `cd ./firmadyne; ./download.sh`

Alternatively, refer to the instructions [below](#compiling-from-source) to compile from source.

## QEMU

To use [QEMU](http://wiki.qemu.org/Main_Page) provided by your distribution:

* `sudo apt-get install qemu-system-arm qemu-system-mips qemu-system-x86 qemu-utils`

Note that emulation of x86-based firmware is not currently supported, but installing
`qemu-system-x86` resolves a packaging issue on certain Debian-based distributions.

Alternatively, use our [modified version](https://github.com/firmadyne/qemu-linaro)
of [qemu-linaro](https://git.linaro.org/?p=qemu/qemu-linaro.git) for certain
firmware with an `alphafs` webserver that assumes a fixed memory mapping (not
recommended), or [upstream qemu](https://github.com/qemu/qemu).

# Usage

1. Set `FIRMWARE_DIR` in `firmadyne.config` to point to the root of this repository.
2. Download a firmware image, e.g. [v2.0.3](http://www.downloads.netgear.com/files/GDC/WNAP320/WNAP320%20Firmware%20Version%202.0.3.zip) for [Netgear WNAP320](https://www.netgear.com/support/product/WNAP320.aspx).
   * `wget http://www.downloads.netgear.com/files/GDC/WNAP320/WNAP320%20Firmware%20Version%202.0.3.zip`
3. Use the extractor to recover only the filesystem, no kernel (`-nk`), no parallel operation (`-np`), populating the `image` table in the SQL server at `127.0.0.1` (`-sql`) with the `Netgear` brand (`-b`), and storing the tarball in `images`.
   * `./sources/extractor/extractor.py -b Netgear -sql 127.0.0.1 -np -nk "WNAP320 Firmware Version 2.0.3.zip" images`
4. Identify the architecture of firmware `1` and store the result in the `image` table of the database.
   * `./scripts/getArch.sh ./images/1.tar.gz`
5. Load the contents of the filesystem for firmware `1` into the database, populating the `object` and `object_to_image` tables.
   * `./scripts/tar2db.py -i 1 -f ./images/1.tar.gz`
6. Create the QEMU disk image for firmware `1`.
   * `sudo ./scripts/makeImage.sh 1`
7. Infer the network configuration for firmware `1`. Kernel messages are logged to `./scratch/1/qemu.initial.serial.log`.
   * `./scripts/inferNetwork.sh 1`
8. Emulate firmware `1` with the inferred network configuration. This will modify the configuration of the host system by creating a TAP device and adding a route.
   * `./scratch/1/run.sh`
9. The system should be available over the network, and is ready for analysis. Kernel messages are mirrored to `./scratch/1/qemu.final.serial.log`. The filesystem for firmware `1` can be mounted to and unmounted from `scratch/1/image` with `./scripts/mount.sh 1` and `./scripts/umount.sh 1`.
   * `./analyses/snmpwalk.sh 192.168.0.100`
   * `./analyses/webAccess.py 1 192.168.0.100 log.txt`
   * `mkdir exploits; ./analyses/runExploits.py -t 192.168.0.100 -o exploits/exploit -e x` (requires Metasploit Framework)
   * `sudo nmap -O -sV 192.168.0.100`
10. The default console should be automatically connected to the terminal. You may also login with `root` and `password`. Note that `Ctrl-c` is sent to the guest; use the QEMU monitor command `Ctrl-a + x` to terminate emulation.

# FAQ
## QEMU outputs empty log for ARM device
Emulation of `armel` devices appears to be broken with our kernel and QEMU >= 2.7.0 for an unknown reason. Use QEMU 2.6.2.

## `run.sh` is not generated
This is a common error that is encountered when the network configuration is unable to be inferred. Follow the checklist below to figure out the cause.

1. `inferNetwork.sh`: Did this script find any network interfaces (e.g. `Interfaces: [br0, 192.168.0.1]`)? If so, this is a bug; please report it. Otherwise, continue below.
2. `qemu.initial.serial.log`: Does this file end with `Unable to mount root fs on unknown-block(8,1)`? If so, the initial filesystem image was not generated correctly using `kpartx`. Try deleting the scratch directory corresponding to this firmware image, and restart at `makeImage.sh`. Otherwise, the initial emulation didn't produce any useful instrumentation. Try increasing the timeout in `inferNetwork.sh` from `60` to `120` and restarting at `inferNetwork.sh`.
3. `qemu.initial.serial.log`: Did the `init` process crash, and is this preceded by a failed NVRAM operation (e.g. `nvram_get_buf: Unable to open key <foo>`)? If so, see the FAQ entries below.

## Log ends with "Kernel panic - not syncing: No working init found"
The firmware uses an initialization process with an unusual name. You'll need to manually inspect the filesystem to identify the correct one, then modify the script to specify its full path by appending a kernel boot parameter `init=<path>` to QEMU.

## A process crashed, e.g. `do_page_fault() #2: sending SIGSEGV for invalid read access from 00000000`
It is likely that the process requested a NVRAM entry that FIRMADYNE does not have a default value for. This can be fixed by manually adding a source for NVRAM entries to `NVRAM_DEFAULTS_PATH`, an entry to `NVRAM_DEFAULTS`, or a file to `OVERRIDE_POINT` in `libnvram`. For more details, see the [documentation for libnvram](https://github.com/firmadyne/libnvram). Note that the first two options involve modifying `config.h`, which will require recompilation of `libnvram`.

## How do I debug the emulated firmware?
1. With full-system QEMU emulation, compile a statically-linked `gdbserver` for the target architecture, copy it into the filesystem, attach it to the process of interest, and connect remotely using `gdb-multiarch`. You'll need a cross-compile toolchain; either use the `crossbuild-essential-*` packages supplied by Debian/Ubuntu, build it from scratch using e.g. `buildroot`, or look for GPL sources and/or pre-compiled binaries online. If you have IDA Pro, you can use IDA's pre-compiled debug servers (located in the `dbgsrv` subdirectory of the install), though they are not GDB-compatible.
2. With full-system QEMU emulation, pass the `-s -S` parameters to QEMU and connect to the stub using `target remote localhost:1234` from `gdb-multiarch`. However, the debugger won't automatically know where kernel and userspace is in memory, so you may need to manually do `add-symbol-file` in `gdb` and break around `try_to_run_init_process()` in the kernel.
2. With user-mode QEMU emulation, `chroot` into the firmware image (optional), set `LD_LIBRARY_PATH` to contain the FIRMADYNE libnvram, and pass both the `-L` parameter with the correct path to the firmware `/lib` directory, and the binary of interest to QEMU. This is easiest to debug, because you can attach directly to the process using `gdb-multiarch`, and interact directly with the process, but the system state may not be accurate since the host kernel is being used. It is also somewhat insecure, because the emulated firmware can access the host filesystem and interact with the host kernel.

# Compiling from Source

If you would like to compile the entire FIRMADYNE system from scratch
without using our pre-built binaries, please follow the steps below.

## [Toolchain](https://github.com/GregorR/musl-cross)

In order to build any of the binaries used by FIRMADYNE, you will need three
cross-compilation toolchains for the following architecture triples. Use only
[musl libc](http://www.musl-libc.org) as the C runtime library for the
toolchain; others have not been tested.

* arm-linux-musleabi
* mipseb-linux-musl
* mipsel-linux-musl

To simplify the process of building cross-compilation toolchains with musl, we
recommend using the [musl-cross](https://github.com/GregorR/musl-cross) project.
Follow the below steps to build these toolchains from source, or alternatively
click [here](https://cmu.boxcn.net/s/hnpvf1n72uccnhyfe307rc2nb9rfxmjp) to
download our pre-built toolchains.

1. `git clone https://github.com/GregorR/musl-cross.git`

2. Modify or set the following variables in `defs.sh`
   * `BINUTILS_URL=http://ftp.gnu.org/gnu/binutils/binutils-2.25.1.tar.bz2`
   * `GCC_VERSION=5.3.0`
   * `GMP_VERSION=6.0.0a`
   * `MPC_VERSION=1.0.2`
   * `MPFR_VERSION=3.1.3`
   * `LIBELF_VERSION=master`
   * `MUSL_DEFAULT_VERSION=1.1.12`
   * `MUSL_GIT_VERSION=615629bd6fcd6ddb69ad762e679f088c7bd878e2`
   * `LANG_CXX=no`
   * `GCC_BUILTIN_PREREQS=yes`

3. Modify or set the following variables in `config.sh`
   * `CFLAGS="-fPIC"`

4. For little-endian MIPS, perform the following:
   * set `TRIPLE=mipsel-linux-musl` in `config.sh`
   * set `LINUX_HEADERS_URL=https://mirrors.edge.kernel.org/pub/linux/kernel/v2.6/linux-2.6.39.4.tar.xz` in `defs.sh`
   * run `./clean.sh` to clean out any previous builds
   * run `./build.sh` to build and install the toolchain into `/opt/cross`

5. For big-endian MIPS, perform the following:
   * set `TRIPLE=mipseb-linux-musl` in `config.sh`
   * set `LINUX_HEADERS_URL=https://mirrors.edge.kernel.org/pub/linux/kernel/v2.6/linux-2.6.39.4.tar.xz` in `defs.sh`
   * run `./clean.sh` to clean out any previous builds
   * run `./build.sh` to build and install the toolchain into `/opt/cross`

6. For little-endian ARM, perform the following:
   * set `TRIPLE=arm-linux-musleabi`, `GCC_BOOTSTRAP_CONFFLAGS="--with-arch=armv6 --with-float=softfp"`, and `GCC_CONFFLAGS="--with-arch=armv6 --with-float=softfp"` in `config.sh`
   * set `LINUX_HEADERS_URL=https://kernel.org/pub/linux/kernel/v4.x/linux-4.1.17.tar.xz` in `defs.sh`
   * run `./clean.sh` to clean out any previous builds
   * run `./build.sh` to build and install the toolchain into `/opt/cross`

7. You should have the following directories, or wherever you installed the toolchains:
   * `/opt/cross/arm-linux-musleabi`
   * `/opt/cross/mipseb-linux-musl`
   * `/opt/cross/mipsel-linux-musl`

## [console](https://github.com/firmadyne/console)

1. `cd ./firmadyne/sources/console`
2. `make clean && CC=/opt/cross/arm-linux-musleabi/bin/arm-linux-musleabi-gcc make && mv console ../../binaries/console.armel`
3. `make clean && CC=/opt/cross/mipseb-linux-musl/bin/mipseb-linux-musl-gcc make && mv console ../../binaries/console.mipseb`
4. `make clean && CC=/opt/cross/mipsel-linux-musl/bin/mipsel-linux-musl-gcc make && mv console ../../binaries/console.mipsel`

## [libnvram](https://github.com/firmadyne/libnvram)

1. `cd ./firmadyne/sources/libnvram`
2. `make clean && CC=/opt/cross/arm-linux-musleabi/bin/arm-linux-musleabi-gcc make && mv libnvram.so ../../binaries/libnvram.so.armel`
3. `make clean && CC=/opt/cross/mipseb-linux-musl/bin/mipseb-linux-musl-gcc make && mv libnvram.so ../../binaries/libnvram.so.mipseb`
4. `make clean && CC=/opt/cross/mipsel-linux-musl/bin/mipsel-linux-musl-gcc make && mv libnvram.so ../../binaries/libnvram.so.mipsel`

## Kernel

### [ARM](https://github.com/firmadyne/kernel-v4.1)

1. `git clone https://github.com/firmadyne/kernel-v4.1.git && cd kernel-v4.1`
2. `mkdir -p build/armel`
3. `cp config.armel build/armel/.config`
4. `make ARCH=arm CROSS_COMPILE=/opt/cross/arm-linux-musleabi/bin/arm-linux-musleabi- O=./build/armel zImage -j8`
5. `cp build/armel/arch/arm/boot/zImage ../firmadyne/binaries/zImage.armel`

### [MIPS](https://github.com/firmadyne/kernel-v2.6)

1. `git clone https://github.com/firmadyne/kernel-v2.6.git && cd kernel-v2.6`
2. For big-endian MIPS, perform the following:
    1. `mkdir -p build/mipseb`
    2. `cp config.mipseb build/mipseb/.config`
    3. `make ARCH=mips CROSS_COMPILE=/opt/cross/mipseb-linux-musl/bin/mipseb-linux-musl- O=./build/mipseb -j8`
    4. `cp build/mipseb/vmlinux ../firmadyne/binaries/vmlinux.mipseb`

3. For little-endian MIPS, perform the following:
    1. `mkdir -p build/mipsel`
    2. `cp config.mipsel build/mipsel/.config`
    3. `make ARCH=mips CROSS_COMPILE=/opt/cross/mipsel-linux-musl/bin/mipsel-linux-musl- O=./build/mipsel -j8`
    4. `cp build/mipsel/vmlinux ../firmadyne/binaries/vmlinux.mipsel`

# Database

During development, the database was stored on a PostgreSQL server.

## Data

Although we cannot redistribute binary firmware, the data used for our
experiments is available [here](https://cmu.boxcn.net/s/hnpvf1n72uccnhyfe307rc2nb9rfxmjp).

## [Schema](https://github.com/firmadyne/firmadyne/blob/master/database/schema)

Below are descriptions of tables in the schema.

* `brand`: Stores brand names for each vendor.

| Column | Description |
| ------ | ----------- |
| id     | Primary key |
| name   | Brand name  |

* `image`: Stores information about each firmware image.

| Column           | Description                                  |
| ---------------- | -------------------------------------------- |
| id               | Primary key                                  |
| filename         | File name                                    |
| brand_id         | Foreign key to `brand`                       |
| hash             | MD5                                          |
| rootfs_extracted | Whether the primary filesystem was extracted |
| kernel_extracted | Whether the kernel was extracted             |
| arch             | Hardware architecture                        |
| kernel_version   | Version of the extracted kernel              |

* `object`: Stores information about each file in a filesystem.

| Column           | Description            |
| ---------------- | ---------------------- |
| id               | Primary key            |
| hash             | MD5                    |

* `object_to_image`: Maps unique files to their firmware images.

| Column           | Description                 |
| ---------------- | --------------------------- |
| id               | Primary key                 |
| oid              | Foreign key to `object`     |
| iid              | Foreign key to `image`      |
| filename         | Full path to the file       |
| regular_file     | Whether the file is regular |
| permissions      | File permissions in octal   |
| uid              | Owner's user ID             |
| gid              | Group's group ID            |

* `product`

| Column       | Description                    |
| ------------ | ------------------------------ |
| id           | Primary key                    |
| iid          | Foreign key to `image`         |
| url          | Download URL                   |
| mib_filename | Filename of the SNMP MIB       |
| mib_hash     | MD5 of the SNP MIB             |
| mib_url      | Download URL of the SNMP MIB   |
| sdk_filename | Filename of the source SDK     |
| sdk_hash     | MD5 of the source SDK          |
| sdk_url      | Download URL of the source SDK |
| product      | Product name                   |
| version      | Version string                 |
| build        | Build string                   |
| date         | Release date                   |

# Paper

The results discussed in our [paper](https://github.com/firmadyne/firmadyne/blob/master/paper/paper.pdf) were produced using pre-release versions of the following:

* toolchains:
   * `BINUTILS_URL=http://ftp.gnu.org/gnu/binutils/binutils-2.25.1.tar.bz2`, `GCC_VERSION=4.9.3`, `GMP_VERSION=6.0.0a`, `MPC_VERSION=1.0.2`, `MPFR_VERSION=3.1.3`, `LIBELF_VERSION=71bf774909fd654d8167a475333fa8f37fbbcb5d`, `MUSL_DEFAULT_VERSION=1.1.10`, `MUSL_GIT_VERSION=996d148bf14b477b07fa3691bffeb930c67b2b62`, `LANG_CXX=no`
   * ARM: `LINUX_HEADERS_URL=https://kernel.org/pub/linux/kernel/v3.x/linux-3.10.84.tar.xz`
   * MIPS: `LINUX_HEADERS_URL=https://kernel.org/pub/linux/kernel/v2.6/longterm/v2.6.32/linux-2.6.32.67.tar.xz`
* kernels:
   * ARM: [firmadyne-v3.10.92](https://github.com/firmadyne/kernel-v3.10/tree/firmadyne-v3.10.92)
   * MIPS: [firmadyne-v2.6.32.68](https://github.com/firmadyne/kernel-v2.6.32/tree/firmadyne-v2.6.32.68) without `e2b9f315547ea50a65baad4899a4780078ab273e` and `26bb3636c987fc7e145af73ddea6c10fa93bdae9`
* console: [`c36ae8553fa4e9c82e8a65752906641d81c2360c`](https://github.com/firmadyne/console/commits/c36ae8553fa4e9c82e8a65752906641d81c2360c)
* extractor: [`5520c64bfa8554c5c17ab671aaed0fdeec91bf19`](https://github.com/firmadyne/extractor/commits/5520c64bfa8554c5c17ab671aaed0fdeec91bf19)
* libnvram: [`b60e7d4d576b39dd46107058adb635d43e80e00d`](https://github.com/firmadyne/libnvram/commits/b60e7d4d576b39dd46107058adb635d43e80e00d)
* qemu-linaro: [`4753f5e8126a00cc0a8559bfd9b47d6340903323`](https://github.com/firmadyne/qemu-linaro/commits/4753f5e8126a00cc0a8559bfd9b47d6340903323)
* binwalk: [`f2ce2992695fae5477c46980148c89e9c91a5cce`](https://github.com/ReFirmLabs/binwalk/commits/f2ce2992695fae5477c46980148c89e9c91a5cce)
   * jefferson: [`090a33be0be4aac8eee8d825447c0eb18dc8b51a`](https://github.com/firmadyne/jefferson/commits/090a33be0be4aac8eee8d825447c0eb18dc8b51a)
   * sasquatch: [`287e4a8e059d3ee7a5f643211fcf00c292cd6f4d`](https://github.com/firmadyne/sasquatch/commits/287e4a8e059d3ee7a5f643211fcf00c292cd6f4d)
