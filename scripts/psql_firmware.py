#!/usr/bin/env python
# -*- coding: utf-8 -*-
import psycopg2
import sys
import traceback
import pdb

def psql(sql_cmd, params=None):
    try:
        conn = psycopg2.connect(database="firmware", user="firmadyne", 
                password="firmadyne", host="127.0.0.1")
        cur = conn.cursor()
        cur.execute(sql_cmd, params)
        sql_act = sql_cmd.split()[0]
        if sql_act=='SELECT':
            row = cur.fetchone()
            return row[0]
        elif sql_act in ['UPDATE','DELETE']:
            conn.commit()
    except Exception as ex:
        traceback.print_exc()
    finally:
        conn.close()

def main():
    if len(sys.argv) < 1 :
        return
    sql_cmd = sys.argv[1]
    ret = psql(sql_cmd)
    if ret:
        print(ret)

if __name__=="__main__":
    main()
