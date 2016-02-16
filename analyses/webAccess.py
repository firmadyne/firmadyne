#!/usr/bin/env python3

import argparse
import traceback
import urllib.request
import http.client
import socket

import psycopg2

def main():
    parser = argparse.ArgumentParser(
        description="Test accesses of files over HTTP versus filesystem")
    parser.add_argument("id", action="store", type=int, help="Input image id")
    parser.add_argument("ip", action="store",
                        help="IP address of emulated image")
    parser.add_argument("log", action="store",
                        help="Output list of accessible URLs")
    parser.add_argument("sql", action="store", default="127.0.0.1", nargs="?",
                        help="Hostname of SQL server")
    parser.add_argument("-p", action="store", dest="pattern", default="/www/",
                        help="Filename pattern of files to access")
    cmd = parser.parse_args()

    db = psycopg2.connect(database="firmware", user="firmadyne",
                          password="firmadyne", host=cmd.sql)

    files = []
    try:
        cur = db.cursor()
        cur.execute(
            "SELECT filename FROM object_to_image WHERE iid=%s AND filename LIKE %s",
            (cmd.id, '%' + cmd.pattern + '%'))
        files = cur.fetchall()
    except BaseException:
        traceback.print_exc()
    finally:
        if cur:
            cur.close()
        if db:
            db.close()

    accessible = []
    for file in files:
        head, sep, tail = file[0].partition(cmd.pattern)
        if tail and ('.' not in tail or any(tail.endswith(ext) \
            for ext in [".htm", ".html", ".cgi", ".asp", ".php",
                        ".bin", ".xml", ".rg"])):
            try:
                url = urllib.parse.urlunsplit(
                    ("http", cmd.ip, tail, None, None))
                print("Accessing: %s..." % url)
                req = urllib.request.urlopen(url, timeout=5)
                data = req.read()
                if b"location.href" in data or b"window.location" in data:
                    print("-> Redirect")
                    accessible.append(tail + " (REDIR)")
                else:
                    accessible.append(tail)
            except socket.timeout as exc:
                print("-> Socket Timeout: %s" % exc)
            except http.client.IncompleteRead as exc:
                data = exc.partial
            except urllib.error.HTTPError as exc:
                print("-> HTTPError: %d" % exc.code)
            except urllib.error.URLError as exc:
                print("-> URLError: %s" % exc.reason)
        elif tail:
            print("Skipping: %s..." % tail)

    with open(cmd.log, "w") as file:
        for url in accessible:
            file.write(url + "\n")

if __name__ == "__main__":
    main()
