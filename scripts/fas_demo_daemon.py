#!/usr/bin/env python3
import asyncio
import re
from subprocess import Popen
from subprocess import PIPE
import sys


def run_fas(brand, fname, recipients):
    print('brand="%(brand)s", fname="%(fname)s", recipients="%(recipients)s"'%locals())
    pp = Popen(['/usr/bin/python3', '-u', './scripts/process_firmware_file_and_send_mail.py',
                brand, fname, recipients],
               cwd='/home/mikil/firmadyne/firmadyne/',
               bufsize=1,stdout=sys.stdout, stderr=sys.stdout,
               universal_newlines=True)
    print('pp.pid=', pp.pid)
    return


@asyncio.coroutine
def handle_req(reader, writer):
    data = yield from reader.read(100)
    cmdl = data.decode()
    addr = writer.get_extra_info('peername')
    print("Received %r from %r" % (cmdl, addr))
    import shlex
    args = shlex.split(cmdl)
    if args[0] == 'run_fas':
        run_fas(*args[1:])


loop = asyncio.get_event_loop()
coro = asyncio.start_server(handle_req, '127.0.0.1', 55688, loop=loop)
server = loop.run_until_complete(coro)

# Serve requests until Ctrl+C is pressed
print('Serving on {}'.format(server.sockets[0].getsockname()))
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

# Close the server
server.close()
loop.run_until_complete(server.wait_closed())
loop.close()
