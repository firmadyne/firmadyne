#!/usr/bin/env python3
import re
import sys
import glob
import io
from psql_firmware import psql


MSF_SUCCESS_MSG = {
    # 0~34
    0: "Command shell session \d+ opened",
    35 : "Success!",
    36 : "confirmed as vulnerable",
    37 : "successfully",
    38 : "successfully",
    39 : "successfully",
    40 : "successfully",
    41 : "successful",
    42 : "Successful",
    43 : "Successful",
    44 : "SUCCESSFUL",
    45 : "Model .* found",
    46 : "Password for user .* is",
    47 : "device found",
    48 : "Found username",
    49 : "Password for this",
    50 : "target device should now .* accept",
    51 : "Dumped .* bytes",
    52 : "Done",
    53 : "Sending .* packet",
    54 : "Sending .* request",
    55 : "Sending a model 7 packet",
    56 : "UPnP unresponsive",
    57 : "Found vulnerable privilege level",
    58 : "Request .*? may have succeeded on",
    59 : "Vulnerable for authentication bypass",
    60 : "Successful login",
    61 : "File saved in",
    62 : "File successfully saved",
    63 : "Successful login",
    64 : "probably vulnerable",
    65 : "Heartbeat response with leak",
    66 : "HTTP code .*? response contained canary cookie ",
    67 : "Scanned 2 of 2 hosts",
    68 : "Command successfully executed",
    69 : "Connected",
    70 : "Password:",
}
for i in range(1, 35):
    MSF_SUCCESS_MSG[i] = MSF_SUCCESS_MSG[0]


def read_block_from_metasploit_log(iid):
    expdir = 'scratch/%d/exploits' % iid
    fout = io.StringIO()
    eid = None
    with open(expdir+'/metasploit.log', 'r') as fin:
        for line in fin:
            m = re.match(r'resource \(.*?\)\> spool .*?(\d+)\.log',line.strip(), re.I)
            if m:
                yield eid,fout.getvalue()
                fout = io.StringIO()
                eid = int(m.group(1))
                # print('eid=%d'%eid)
            m = re.match(r"Result: ", line.strip(), re.I)
            if m:
                yield eid,fout.getvalue()
                fout = io.StringIO()
                eid=None
            fout.write(line)
        yield eid, fout.getvalue()


def merge_metasploit_logs(iid):
    expdir='scratch/%d/exploits'%iid
    logfiles = glob.glob1(expdir, '*.log')
    logfiles = [_ for _ in logfiles if _[0].isdigit()]
    logfiles.sort(key=lambda s: int(s.split('.')[0]))
    with open(expdir+'/merged_metasploit.log', 'w') as fout:
        for eid,msfblock in read_block_from_metasploit_log(iid):
            if eid is not None:
                # print('eid=%d'%eid)
                with open(expdir+'/%d.log'%eid, 'r') as fin2:
                    cont2 = fin2.read()
                logfiles.remove('%d.log'%eid)
                fout.write('\n\n')
                fout.write('<< eid= %(eid)d >>\n'%locals())
                fout.write(msfblock+'\n')
                fout.write(cont2+'\n')
                if eid in MSF_SUCCESS_MSG:
                    m = re.search(MSF_SUCCESS_MSG[eid], msfblock+cont2, re.MULTILINE|re.I)
                    if m:
                        print('vulnerable to exploit %d'%eid)
                        # print(MSF_SUCCESS_MSG[eid])
                        psql("""UPDATE image SET vulns = set_union(vulns::TEXT[], '{"%(eid)s"}'::TEXT[]) where id=%(iid)s;""", locals())
            else:
                fout.write(msfblock+'\n')
        for logfile in logfiles:
            eid = int(logfile.split('.')[0])
            # print('eid=%d'%eid)
            fout.write('\n\n')
            fout.write('<< eid= %(eid)d >>\n'%locals())
            with open(expdir+'/'+logfile, 'r', errors='ignore') as fin2:
                cont2 = fin2.read()
                fout.write(cont2 + '\n')

def main():
    iid = int(sys.argv[1])
    # iid=1097
    psql("UPDATE image SET vulns = '{}'::TEXT[] where id=%(iid)s;", locals())
    merge_metasploit_logs(iid)

if __name__=="__main__":
    main()
