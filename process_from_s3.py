import boto
import os
import traceback
import time
from datetime import datetime 

def main():
    try:
        conn = boto.connect_s3()
        buck = conn.get_bucket('grid-iot-firmware-harvest')
        for obj in buck.list('fw_files/netgear/downloadcenter.netgear.com'):
            begin = time.time()
            print('begin=%s' % datetime.fromtimestamp(begin))
            fname = os.path.basename(obj.key)
            print('download "%s"' % fname)
            obj.get_contents_to_filename(fname)
            os.system('./scripts/process_firmware_file.sh "Netgear" "%s"'%fname)
            os.remove(fname)
            end = time.time()
            print('end=%s' % datetime.fromtimestamp(end))
    except BaseException as ex:
        traceback.print_exc()

if __name__=='__main__':
    main()

