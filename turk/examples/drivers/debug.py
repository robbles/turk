#!/usr/bin/env python
import os
import logging
from time import sleep

def main(args):
    logging.basicConfig(format='[%(levelname)s] %(name)s: %(message)s')
    log = logging.getLogger('DEBUG DRIVER')
    log.setLevel(logging.DEBUG)

    log.debug('started')
    log.debug('environment keys: %s' % os.environ.keys())
    log.debug('args: %s' % args)
    log.debug('DBUS Session Bus is at %s' % os.environ['DBUS_SESSION_BUS_ADDRESS'])

    while True:
        sleep(10)

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
