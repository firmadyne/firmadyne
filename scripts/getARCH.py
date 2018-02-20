#!usr/bin/env python
import os
import re
import binwalk
import argparse
import psycopg2
from scripts.autoExtract import *
class getArch:
    
    @staticmethod
    def getArch(inputImage):
        CPU = re.compile(r"CPU: [a-zA-Z0-9\- ]*,")
        ENDIAN = re.compile(r"[a-zA-Z]* endian")
        
        cpu = None
        endian = None
        path = inputImage#os.path.abspath(os.path.join(brandname,filename))
        f = open('Arch.txt', 'a+')
        if os.path.isfile(path):
            for module in binwalk.scan(path, signature=True, quiet=True):
                for entry in module.results:
                    if "CPU" in entry.description:
                        cpu = CPU.search(entry.description).group().split(' ')[1][:-1].lower()
                        if cpu == 'powerpc':
                            cpu = 'ppc'
                    if "endian" in entry.description:
                        endian = ENDIAN.search(entry.description).group().split(' ')[0].lower()
                        if endian == 'big':
                            endian = 'eb'
                        else:
                            endian = 'el'
            if cpu or endian:
                f.writelines('%s: '%inputImage+ cpu+endian+'\n')
            else:
                print("ERROR: There is no architecture data...")
                print("%s"%inputImage)
                f.writelines('%s: '%inputImage+'None\n')
        else:
            print("ERROR!!!")
            print("There is no file named %s"%path)
        f.close()
        
    def autoLog(self):
        dirs = [d for d in os.listdir('.') if not d.startswith('.') and not d in AutoExtractor.firmadynedir and os.path.isdir(d)]
        for d in dirs:
            files = os.listdir(d)
            files.sort()
            for f in files:
                getArch.getArch(os.path.join(d,f))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automatically Detect Firmware's Architecture")
    parser.add_argument('-i', action='store', dest='inputImage',help="Firmware's Image name")
    args = parser.parse_args()
    getArch.getArch(args.inputImage)