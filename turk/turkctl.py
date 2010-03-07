#!/usr/bin/python

import os, sys
import signal
from sys import stdout
from optparse import OptionParser
import yaml
import multiprocessing
import logging
from time import sleep

from turk.runtime.spawner import run as run_spawner
from turk.runtime.bridge import run as run_bridge
from turk.xbeed.xbeed import run as run_xbeed
from turk import get_config

default_name = 'xbee0'

conf = {}

def start(conf):
    """
    Starts the Turk Core as a background process. 
    """
    pidfile_path = get_config(conf, 'turkctl.pidfile')
    
    if os.path.exists(pidfile_path):
        print 'File "%s" exists - Is Turk Core already running?' % pidfile_path
        exit(-1)

    pidfile = open(pidfile_path, 'w')

    pid = os.fork()

    if not pid:
        # Controller process
        try:
            print 'starting spawner...'
            spawner = multiprocessing.Process(target=run_spawner, args=(conf,), name='spawner')
            spawner.start()

            print 'starting bridge...'
            bridge = multiprocessing.Process(target=run_bridge, args=(conf,))
            bridge.start()

            if hasattr(conf, 'xbeed'):
                print 'starting xbeed...'
                xbeed = multiprocessing.Process(target=run_xbeed, args=(conf,))
                xbeed.start()

        except Exception, e:
            print 'turkctl: error starting Turk:', e
            os.unlink(pidfile_path)
            exit(-1)

        def finished(*args):
            print 'Turk is shutting down...'
            spawner.terminate()
            bridge.terminate()
            if hasattr(conf, 'xbeed'):
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
        print 'turkctl: started Turk'


def stop(conf):
    """
    Reads the PID file left by start() and sends SIGTERM to all of the daemon
    processes that make up the runtime
    """
    print 'Stopping Turk'

    pidfile_path = get_config(conf, 'turkctl.pidfile')

    if not os.path.exists(pidfile_path):
        print 'Couldn\'t find pidfile! Is Turk Core REALLY running?'
        return

    # Get pids from file
    pidfile = open(pidfile_path, 'rU')

    # Kill all the Turk processes (should be one pid per line)
    [terminate(pid) for pid in pidfile]

    os.unlink(pidfile_path)
    pidfile.close()

def clean(conf):
    """Deletes any data associated with improperly stopped Turk Core"""

    pidfile_path = get_config(conf, 'turkctl.pidfile')

    if os.path.exists(pidfile_path):
        print 'Removing old pidfile...'
        os.unlink(pidfile_path)
    else:
        print 'No pidfile to remove!'

def terminate(pid):
    try:
        os.kill(int(pid), signal.SIGTERM)
    except Exception, e:
        print 'Failed to kill process %s: %s' % (pid, e)
    

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
    os.environ['TURK_CORE_CONF'] = options.config

    print 'conf:', conf

    {'start':start,
     'stop':stop,
     'restart':lambda conf: (stop(conf), start(conf)),
     'clean':clean}[args[0]](conf)


if __name__ == '__main__':
    main()



