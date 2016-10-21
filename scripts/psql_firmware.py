#!/usr/bin/env python3
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
        if sql_act.upper()=='SELECT':
            return cur.fetchall()
            return row[0]
        elif sql_act.upper() in ['UPDATE','DELETE']:
            conn.commit()
        return None
    except Exception as ex:
        traceback.print_exc()
    finally:
        conn.close()

def main():
    if len(sys.argv) < 1 :
        return
    sql_cmd = sys.argv[1]
    rows = psql(sql_cmd)
    if rows is not None:
        for row in rows:
            if len(row)==1:
                print(row[0])
            else:
                for c in row:
                    print(c, end=' ')
                print('\n', end='')

if __name__=="__main__":
    main()
