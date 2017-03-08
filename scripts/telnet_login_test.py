#!/usr/bin/env python3


def telnet_login(host, username, password):
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
        print('password=%s' %  password)
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
        tn.close()



# def telnet_tester(host, usernames, passwords):
#     tested_credentials=[]
#     import telnetlib
#     try:
#         tn = telnetlib.Telnet(host)
#     except ConnectionRefusedError as ex:
#         print(ex)
#         return
#     login = False
#     while True:
#         while True:
#             if login==True:
#                 break
#             s = tn.read_eager().decode().lower()
#             if s != '':
#                 print(s)
#                 break
#         try:
#             username = usernames[0]
#         except IndexError:
#             print('all usernames tested')
#             return tested_credentials
#         usernames.pop(0)
#         tn.write(username.encode() + b"\n")
#         print('username=%s' % username)
#         while True:
#             s = tn.read_eager().decode().lower()
#             if s != '':
#                 print(s)
#                 if s.strip() != username:
#                     break
#         if 'password' in s:
#             tn.write(password.encode() + b"\b")
#             print('password=%s' %  password)
#             while True:
#                 s = tn.read_eager().decode().lower()
#                 if s != '':
#                     print(s)
#                     break
#             if 'failed' in s:
#                 tested_credentials += [(username, password)]
#                 s = tn.read_until(b'login:', timeout=6).decode().lower()
#                 tn.write(username.encode() + b"\n")
#         else:
#             if 'login incorrect' in s:
#                 tested_credentials += [(username, None)]
#                 if 'login:' in s:
#                     login = True
#                 else:
#                     login = False
#                 continue
#             elif 'timed out' in s:
#                 break
#             else:
#                 s = tn.read_eager()
#     return s


class TimeOutException(Exception):
    pass


def ping_until_network_reachable(host, timeOut=60.0):
    import time, sys, os
    begin = time.time()
    while (time.time() - begin) < 60.0:
        ret = os.system("ping %(host)s -c 1 -w 2" % locals())
        if ret==0:
            return
        else:
            time.sleep(2) 
    print("time out", file=sys.stderr)
    raise TimeOutException("time out")


mirai_credentials = """
root:xc3511
root:vizxv
root:admin
admin:admin
root:888888
root:xmhdipc
root:default
root:juantech
root:123456
root:54321
support:support
root:
admin:password
root:root
root:12345
user:user
admin:
root:pass
admin:admin1234
root:1111
admin:smcadmin
admin:1111
root:666666
root:password
root:1234
root:klv123
Administrator:admin
service:service
supervisor:supervisor
guest:guest
guest:12345
guest:12345
admin1:password
administrator:1234
666666:666666
888888:888888
ubnt:ubnt
root:klv1234
root:Zte521
root:hi3518
root:jvbzd
root:anko
root:zlxx.
root:7ujMko0vizxv
root:7ujMko0admin
root:system
root:ikwb
root:dreambox
root:user
root:realtek
root:00000000
admin:1111111
admin:1234
admin:12345
admin:54321
admin:123456
admin:7ujMko0admin
admin:1234
admin:pass
admin:meinsm
tech:tech
mother:fucker
"""


def all_combinations(unames, pwords):
    for uname in unames:
        for pword in pwords:
            yield (uname, pword)


def main():
    host = '192.168.0.1'
    ping_until_network_reachable(host, 60.0)

    creds = [l.strip().split(':') for l in mirai_credentials.splitlines() if l.strip()]
    unames = sorted(list(set(_[0] for _ in creds)))
    pwords = sorted(list(set(_[1] for _ in creds)))
    creds = list(all_combinations(unames, pwords))
    for cred in creds:
        uname,pword = cred
        print(cred)
        if telnet_login(host, uname, pword):
            print('login succesful for "%s", "%s"' % (uname, pword))
            break


if __name__ == '__main__':
    main()

