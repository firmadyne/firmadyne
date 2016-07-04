#!/usr/bin/env python
# -*- encoding:utf-8 -*-
import psycopg2
import sys
import traceback
import pdb

def main():
    try:
        conn = psycopg2.connect(database="firmware", user="firmadyne", 
                password="firmadyne", host="127.0.0.1")
        cur = conn.cursor()
        if len(sys.argv) < 1 :
            return
        sql_cmd = sys.argv[1]
        rows = cur.execute(sql_cmd)
        sql_act = sql_cmd.split()[0]
        if sql_act=='SELECT':
            rows = cur.fetchone()
            print(rows[0])
        elif sql_act in ['UPDATE','DELETE']:
            conn.commit()

    except Exception as ex:
        traceback.print_exc()
    finally:
        conn.close()

if __name__=="__main__":
    main()
