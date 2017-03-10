#!/usr/bin/env python3
import os
import sys
import time
import re
from psql_firmware import psql


def psql0(query, var):
    return psql(query, var)[0][0]


def telnet_login1(host, username):
    import telnetlib
    try:
        tn = telnetlib.Telnet(host)
        while True:
            s = tn.read_eager().decode().lower()
            if s != '':
                print(s)
                break
        tn.write(username.encode() + b"\n")
        while True:
            s = tn.read_eager().decode().lower().strip()
            if s != '':
                print(s)
                if s != username:
                    break
        return 'password:' in s
    finally:
        if 'tn' in locals().keys():
            tn.close()


def telnet_login(host, username, password): #noqa
    import telnetlib
    try:
        tn = telnetlib.Telnet(host)
        while True:
            s = tn.read_eager().decode().lower()
            if s != '':
                print(s)
                break
        tn.write(username.encode() + b"\n")
        while True:
            s = tn.read_eager().decode().lower()
            if s != '':
                print(s)
                if s.strip() != username:
                    break
        if 'password' not in s:
            return False
        tn.write(password.encode() + b"\b")
        print('password=%s' % password)
        while True:
            s = tn.read_eager().decode().lower()
            if s != '':
                print(s)
                break
        if 'failed' in s:
            return False
        elif 'error' in s:
            return False
        elif 'incorrect' in s:
            return False
        else:
            return True
    except ConnectionRefusedError as ex:
        print(ex)
        return False
    except BaseException as ex:
        print(ex)
        return False
    finally:
        if 'tn' in locals().keys():
            tn.close()


def ping_until_OK(host, timeOut=60.0):
    begin = time.time()
    while (time.time() - begin) < timeOut:
        ret = os.system("ping %(host)s -c 1 -w 2" % locals())
        if ret == 0:
            return True
        else:
            time.sleep(2)
    return False


def all_combinations(unames, pwords):
    for uname in unames:
        for pword in pwords:
            yield (uname, pword)


def main():
    target = sys.argv[1]
    if re.match(r'\d+\.\d+\.\d+\.\d+', target):
        host = target
    elif re.match(r'\d+', target):
        iid = int(target)
        host = psql0(
            "SELECT guest_ip FROM image WHERE id=%(iid)s",
            locals())
        if not host:
            print("guest_ip is empty for id=%(iid)s" % locals())
            return

    with open('scripts/Mirai_credentials.txt', 'r') as fin:
        creds = fin.read().splitlines()
        creds = [_.strip().split(':') for _ in creds if _.strip()]

    unames = sorted(list(set(_[0] for _ in creds)))
    pwords = sorted(list(set(_[1] for _ in creds)))

    if not ping_until_OK(host, 60.0):
        return

    tested_creds = []
    success_uname = None
    try:
        for uname in unames:
            if telnet_login1(host, uname):
                print('login succesful for "%s"' % (uname))
                success_uname = uname
                tested_creds += [(success_uname, None)]
                break
            else:
                tested_creds += [(uname, None)]
    except ConnectionRefusedError as ex:
        print(ex)
        tested_creds = None

    success_cred = (None, None)
    if success_uname:
        for pword in pwords:
            if telnet_login(host, success_uname, pword):
                print('login succesful for "%s" "%s" ' % (uname, pword))
                success_cred = (uname, pword)
                tested_creds += [success_cred]
                break
            else:
                tested_creds += [(uname, pword)]
    tested_creds += [success_cred]
    print('tested_creds=', tested_creds)
    psql("UPDATE image SET mirai_credentials_tested=%s WHERE id=%s",
         (tested_creds, iid))


if __name__ == '__main__':
    main()
