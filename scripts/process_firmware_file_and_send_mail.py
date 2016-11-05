#!/usr/bin/env python3
import sys
import re
from os.path import basename


def send_mail(recipients, subject, msgbody, attachment):
    from email_credentials import username,password
    from email.mime.application import MIMEApplication
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from os.path import basename
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = username
    msg['To'] = recipients
    msg.attach(MIMEText(msgbody))
    with open(attachment, 'rb') as fin:
        part = MIMEApplication(fin.read(), Name=basename(attachment))
        part['Content-Disposition'] = 'attachment; filename="%s"'%basename(attachment)
        part['Content-Type'] = 'text/plain; charset=utf-8'
        msg.attach(part)
    import smtplib
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login(username, password)
    server.set_debuglevel(1)
    server.send_message(msg)
    server.close()


def main():
    brand=sys.argv[1]
    fname=sys.argv[2]
    recipients=sys.argv[3]
    cwd='/home/mikil/firmadyne/firmadyne'
    from subprocess import Popen
    # with open(cwd + '/process.log', 'w', buffering=1, errors='backslashreplace') as prout:
    # pp = Popen(['./scripts/process_firmware_file.sh', brand, fname],
    #             bufsize=1, cwd=cwd, stderr=prout, stdout=prout, universal_newlines=True)
    pp = Popen('./scripts/process_firmware_file.sh "%(brand)s" "%(fname)s" | tee process.log 2>&1'%locals(),
               shell=True,
               bufsize=1, cwd=cwd, stderr=sys.stdout, stdout=sys.stdout, universal_newlines=True)
    print('pp.pid=', pp.pid)
    pp.wait()
    with open(cwd + '/process.log', 'r', errors='backslashreplace') as fin:
        logcont = fin.read()
    for line in iter(logcont.splitlines()):
        m = re.search(r'Database Image ID: (\d+)', line)
        if m:
            iid = int(m.group(1))
            break
    from psql_firmware import psql
    vulns = psql("SELECT vulns FROM image WHERE id=%(iid)s", locals())
    vulns = vulns[0][0]
    subject = 'FAS result of "%s" "%s"' % (brand, basename(fname))
    from io import StringIO
    buf = StringIO()
    buf.write('Vulnerabilites:\n')
    for vuln in vulns:
        buf.write('  %s\n'%vuln)
    msgbody = buf.getvalue()
    send_mail(recipients, subject, msgbody, cwd + '/process.log')

if __name__=='__main__':
    main()
