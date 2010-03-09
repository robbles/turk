#!/usr/bin/python

import os, sys
import signal
from optparse import OptionParser
import yaml
import multiprocessing
import logging
from time import sleep

from turk.runtime.spawner import run as run_spawner
from turk.runtime.bridge import run as run_bridge
from turk.xbeed.xbeed import run as run_xbeed
from turk import get_config, init_logging

log = init_logging('turkctl')

def start(conf):
    """
    Starts the Turk Core as a background process. 
    """
    pidfile_path = get_config('turkctl.pidfile', conf)
    
    if os.path.exists(pidfile_path):
        print 'File "%s" exists - Is Turk Core already running?' % pidfile_path
        exit(-1)

    pidfile = open(pidfile_path, 'w')

    pid = os.fork()

    if not pid:
        # Controller process
        try:
            log.debug('starting spawner...')
            spawner = multiprocessing.Process(target=run_spawner, args=(conf,), name='spawner')
            spawner.start()

            log.debug('starting bridge...')
            bridge = multiprocessing.Process(target=run_bridge, args=(conf,))
            bridge.start()

            if conf.has_key('xbeed'):
                log.debug('starting xbeed...')
                xbeed = multiprocessing.Process(target=run_xbeed, args=(conf,))
                xbeed.start()

        except Exception, e:
            log.debug('turkctl: error starting Turk: %s' % e)
            os.unlink(pidfile_path)
            exit(-1)

        def finished(*args):
            log.debug('stopping Turk...')
            spawner.terminate()
            bridge.terminate()
            if conf.has_key('xbeed'):
                xbeed.terminate()
            exit(0)

        signal.signal(signal.SIGTERM, finished)

        while 1:
            # Just do nothing until terminated by turkctl
            sleep(1)

    else:
        # Starter process
        pidfile.write('%d\n' % pid)
        pidfile.close()
        print 'starting Turk...'


def stop(conf):
    """
    Reads the PID file left by start() and sends SIGTERM to all of the daemon
    processes that make up the runtime
    """
    print 'stopping Turk...'

    pidfile_path = get_config('turkctl.pidfile', conf)

    if not os.path.exists(pidfile_path):
        print 'Couldn\'t find pidfile! Is Turk REALLY running?'
        return

    # Get pids from file
    pidfile = open(pidfile_path, 'rU')

    # Kill all the Turk processes (should be one pid per line)
    [terminate(pid) for pid in pidfile]

    os.unlink(pidfile_path)
    pidfile.close()

def clean(conf):
    """Deletes any data associated with improperly stopped Turk Core"""

    pidfile_path = get_config('turkctl.pidfile', conf)

    if os.path.exists(pidfile_path):
        log.debug('Removing old pidfile...')
        os.unlink(pidfile_path)
    else:
        log.debug('No pidfile to remove!')

def terminate(pid):
    try:
        os.kill(int(pid), signal.SIGTERM)
    except Exception, e:
        log.debug('Failed to kill process %s: %s' % (pid, e))
    

def main():
    """
    Run as a utility for launching Turk Core
    usage: turkctl.py start|stop
    """
    parser = OptionParser("usage: %prog [options] <start|stop|restart|clean>")
    parser.add_option("-f", "--config-file", dest="config", type="string", default='/etc/turk/turk.yml',
                      help="default configuration file")
    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.error("incorrect number of arguments")

    conf = yaml.load(open(options.config, 'rU'))
    os.environ['TURK_CONF'] = options.config

    if not get_config('turkctl.debug', conf):
        log.setLevel(logging.WARNING)

    {'start':start,
     'stop':stop,
     'restart':lambda conf: (stop(conf), start(conf)),
     'clean':clean}[args[0]](conf)


if __name__ == '__main__':
    main()



