#!/usr/bin/env python
import os
import logging
from time import sleep
import dbus


def main(args):
    logging.basicConfig(format='[%(levelname)s] %(name)s: %(message)s')
    log = logging.getLogger('DRIVER')
    log.setLevel(logging.DEBUG)

    log.debug('#' * 20)
    log.debug('started')
    log.debug('running in %s' % os.getcwd())
    log.debug('environment keys: %s' % os.environ.keys())
    log.debug('args: %s' % args)
    log.debug('DBUS Session Bus: %s' % os.environ['DBUS_SESSION_BUS_ADDRESS'])

    bus = dbus.SessionBus()
    log.debug('Connected to SessionBus successfully!')

    while True:
        sleep(10)

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
