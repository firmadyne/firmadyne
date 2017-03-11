#!/usr/bin/env python3
import os
from scripts.psql_firmware import psql


def main():
    rows = psql("SELECT file_url, brand FROM image WHERE network_reachable = true and open_ports is  null")
    for row in rows:
        furl, brand = row
        print('scripts/process_firmware_file.py '
              '"%(brand)s" "%(furl)s"' % locals())
        os.system('python3 -u scripts/process_firmware_file.py '
                  '"%(brand)s" "%(furl)s"' % locals())


if __name__ == '__main__':
    main()
