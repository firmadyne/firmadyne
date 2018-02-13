#!/usr/bin/env python

#This program will automatically try to extract all firmware image.
#Note that this program only extracts.

import argparse
import os
import subprocess
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from sources.extractor.extractor import *

class AutoExtractor:
    def __init__(self, auto=False, inputImage=None, brand=None):
        self.auto = auto
        self.inputImage = inputImage
        self.brand = brand
        self.firmadynedir = ['analyses','binaries','database','images','paper','scratch','scripts','sources']
        self.cwd = os.getcwd()
    
    @staticmethod        
    def execute(inputImage, brand=None):
        Extractor(inputImage, 'images', True, False,
                  False, "127.0.0.1", brand).extract()
        #extract = Extractor(result.input, result.output, result.rootfs,
        #                result.kernel, result.parallel, result.sql,
        #                result.brand)

    @staticmethod
    def checkLog(fileForCheck):
        try:
            f = open("%s"%fileForCheck, 'r+')
        except:
            return []
        visited = [line[:-1] for line in f]
        f.close()
        return visited

    @staticmethod
    def markImage(fileForCheck, imageName):
        try:
            f = open("./%s"%fileForCheck, "a")
        except:
            print("There is no %s..."%fileForCheck)
            print("Creating %s..."%fileForCheck)
            try:
                f = open("./%s"%fileForCheck, "w")
            except:
                print("Cannot make %s..."%fileForCheck)
                return False
        f.write("%s\n"%imageName)
        f.close()
        return True

    def extract(self):
        if self.auto == True:
            visited = AutoExtractor.checkLog("./visited.txt")
            dirlist = [dir for dir in os.listdir('.') if os.path.isdir(dir) and not dir in self.firmadynedir and not dir.startswith('.')]
            dirlist.sort()
            for d in dirlist:
                files = os.listdir('./%s'%d)
                files = [f for f in files if not f in visited]
                files.sort()
                for f in files:
                    AutoExtractor.execute(inputImage='%s/%s'%(d,f), brand=d)
                    os.chdir(self.cwd)
                    AutoExtractor.markImage("./visited.txt",f)
        elif not self.auto and self.inputImage:
            AutoExtractor.execute(self.inputImage, self.brand)
            os.chdir(self.cwd)
            AutoExtractor.markImage("./visited.txt", self.inputImage)
        else:
            print
            print ("Wrong option was given...")
            print ("use -h option for help")
            print

if __name__ == "__main__":
    os.nice(-20)
    parser = argparse.ArgumentParser(description="Automatically Detect Vendors and Firmware Image and Execute All process\n\nThis Option Require All Firmware Images in the Directory")
    parser.add_argument('-na', action='store_false', dest='auto', default=True, help="This option require inputImage(relpath) and brand(optional)")
    parser.add_argument('-b', action='store', dest='brand', help="Firmware's Vendor name")
    parser.add_argument('-i', action='store', dest='inputImage',help="Firmware's Image name")
    args = parser.parse_args()
    if not args.auto and not args.inputImage:
        print
        print("use -h option for help")
        print("not enough arguments given")
        print
        exit() 
    AutoExtractor(args.auto, args.inputImage, args.brand).extract()