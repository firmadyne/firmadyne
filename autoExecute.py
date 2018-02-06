#!/usr/bin/env python

import argparse
import os
import subprocess
from sources.extractor import extractor

script={'extractor':'./sources/extractor/extractor.py',
        'getArch':'./scripts/getArch.sh',
        'tar2db':'./scripts/tar2db.py',
        'makeImage':'sudo ./scripts/makeImage.sh',
        'inferNetwork':'sudo ./scripts/inferNetwork.sh'
}
def run(fileToRun, Args, expectOn):
    subprocess.call(['sudo','bash','./expect.sh', '%s'%fileToRun, '%s'%Args])

def getDBResult(query, allOrOne):
    import psycopg2
    database = psycopg2.connect(database="firmware", user="firmadyne", password="firmadyne", host='127.0.0.1')
    cur = database.cursor()
    cur.execute(query)
    result = None
    if allOrOne == 'one':
        result = cur.fetchone()
    elif allOrOne == 'all':
        result = [(int(x),y) for (x,y) in cur.fetchall()]
    cur.close()
    return result


def getImage_ID(extract):
    query = "SELECT id FROM image WHERE hash=\'%s\'"
    return getDBResult(query% extract.io_md5('%s'%(extract._input)), 'one')

def Tar2db(image_ID, image_path):
    from scripts import tar2db
    try:
        args = '-i %d -f ./images/%d.tar.gz'%(image_ID,image_ID)
        os.system('%s %s'%(script['tar2db'],args))
        #run(script['tar2db'],args,False)
    except:
        print("Already registered tar file")
        raise Exception

def execute(brand, inputImage):
    print "\nPreparing for analyzing firmware name "+'\"'+inputImage+'\"'

    print ("Getting Image ID from DB...")
    image_ID = getImage_ID(extractor.Extractor(inputImage))
    if image_ID is None or not '%d.tar.gz'%image_ID in os.listdir('./images'):
        print("executing extractor...")
        try:
            check = subprocess.check_call(['sudo','%s'%script['extractor'],'-b','%s'%brand,'-sql','127.0.0.1','-np','-nk','%s'%inputImage,'images'])
            check.timeout=600
        except:
            print("There is somekind of worng in file %s"%inputImage)
            return
        #os.system('sudo %s -b %s -sql %s -np -nk %s %s'%(script['extractor'],brand, '127.0.0.1', inputImage, 'images'))
        #run('sudo %s'%script['extractor'],'-b %s -sql %s -np -nk %s %s'%(brand, '127.0.0.1', inputImage, 'images'),False)
        image_ID = getImage_ID(extractor.Extractor(inputImage))
        image_ID = image_ID[0]
        print "=============image_ID is============"
        print image_ID
        import time
        time.sleep(5)
        if not '%d.tar.gz'%image_ID in os.listdir('./images'):
            print("extraction failed...")
            return
    print ("Image ID is %d"%image_ID)
    
    print("executing getArch...")
    run('%s'%script['getArch'],'./images/%d.tar.gz'%(image_ID),True)

    print("executing tar2db...")
    try:
        Tar2db(image_ID, './images/%d.tar.gz'%(image_ID))
    except:
        print ""
    
    print("executing makeImage...")
    run(script['makeImage'], ' %d'%(image_ID),True)
    
    print("executing inferNetwork...")
    run(script['inferNetwork'],'%d'%(image_ID),True)
    markVisited(inputImage, "successed.txt")
    
    print("\nDone. Do ./scratch/%d/run.sh\n"%image_ID)
    print("If have any error, do ./scripts/delete.sh \n")

def checkLog(fileForCheck):
    try:
        f = open("%s"%fileForCheck, 'r')
    except:
        return []
    visited = [line[:-1] for line in f]
    f.close()
    return visited

def markVisited(fileName, fileForCheck):
    try:
        f = open("./%s"%fileForCheck, "a")
    except:
        print("Cannot make %s..."%fileForCheck)
        return False
    f.write("%s\n"%fileName)
    f.close()
    return True

def main():
    parser = argparse.ArgumentParser(description="Analyze all firmware in this directory")
    parser.add_argument('-a', action='store_true', dest='auto', default=False, help="Automatically Detect Vendors and Firmware Image and Execute All process\n\nThis Option Require All Firmware Images in the Directory")
    parser.add_argument('-b', action='store', dest='brand', help="Firmware's Vendor name")
    parser.add_argument('-i', action='store', dest='inputImage',help="Firmware's Image name")
    args = parser.parse_args()
    
    if args.auto == True:
        visited = checkLog("visited.txt")
        firmadynedir = ['analyses','binaries','database','images','paper','scratch','scripts','sources','.git']
        dirlist = [dir for dir in os.listdir('.') if os.path.isdir(dir) and not dir in firmadynedir and not dir.startswith('.')]
        dirlist.sort()
        for d in dirlist:
            files = os.listdir('./%s'%d)
            files = [f for f in files if not f in visited]
            files.sort()
            for f in files:
                execute(d,'%s/%s'%(d,f))
                markVisited(f,"visited.txt")
                
    elif args.auto == False and args.inputImage and args.brand is not None:
        execute(args.brand,args.inputImage)
    else:
        print
        print ("use -h option for help")
        print
        

if __name__ == '__main__':
    main()
