#!usr/bin/env python

#This program will automatically generate run.sh file each firmware image.
#If you want to manually extract, follow directions on README.md

import os
import subprocess
import pexpect
from autoExtract import *

class autoRunGenerator:
    script={'extractor':'./sources/extractor/extractor.py',
        'getArch':'./scripts/getArch.sh ./images/%d.tar.gz',
        'tar2db':'./scripts/tar2db.py -i %d -f ./images/%d.tar.gz',
        'makeImage':'./scripts/makeImage.sh %d',
        'inferNetwork':'./scripts/inferNetwork.sh %d'
    }
    def getImagenameFromDB(self,image_ID):
        import psycopg2
        query = 'SELECT filename FROM image WHERE id=%d'%image_ID
        database = psycopg2.connect(database="firmware", user="firmadyne", password="firmadyne", host='127.0.0.1')
        cur = database.cursor()
        cur.execute(query)
        result = cur.fetchone()
        cur.close()
        database.close()
        return result

    def run(self, fileToRun, inferOn, sudoOn):
        Args = [
            '',#sudo
            '',#inferOn
            '%s'%fileToRun,#fileToRun
        ]
        if sudoOn:
            Args[0] = 'sudo '
        if inferOn:
            Args[1] = 'bash ./scripts/expect.sh '
        subprocess.check_call(''.join(Args).split(' '))
        return

    def genRun(self):
        cwd = os.getcwd()
        #first, Try to extract all firmware images
        AutoExtractor(True).extract()
        os.chdir(cwd)
        extracted = os.listdir('./images')
        extracted = [int(i[:-7]) for i in extracted if '.tar.gz' in i]
        
        for image_ID in extracted:
            try:
                self.run(self.script['getArch']%image_ID, True, False)
                self.run(self.script['tar2db']%(image_ID, image_ID), False, False)
                self.run(self.script['makeImage']%image_ID, True, True)
                self.run(self.script['inferNetwork']%image_ID, True, False)
            except:
                print("There is some problem in image_ID : %d"%image_ID)
                continue
            AutoExtractor.markImage("success.txt", self.getImagenameFromDB(image_ID))
        print("\n Done. ")
        print("If have any error on image, use ./scripts/delete.sh \n")

if __name__ == "__main__":
    print("Generate run.sh all of firmware in this directory")
    print("Make sure that 'expect' library pre-installed")
    autoRunGenerator().genRun()