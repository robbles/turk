#!/usr/bin/python

import os, sys
import signal
from subprocess import Popen
from sys import stdout
from optparse import OptionParser
import yaml

default_name = 'xbee0'

conf = {}

def launch():
    """
    Starts the Turk Core as a group of processes. Logs each started daemon's PID
    in a file, so that a later call to stop() can shut them all down.
    """
    
    # Make sure we're in the Turk Core directory
    core_dir = os.path.dirname(sys.argv[0])
    os.chdir(core_dir)
    pidfile = 'turkcore.pid'

    if os.path.exists(pidfile):
        print 'File %s exists - Is Turk Core already running?' % pidfile
        exit(-1)

    pids = open('turkcore.pid', 'w')

    procs = {}

    try:
        print 'starting spawner...'
        procs['spawner'] = Popen('./runtime/spawner.py', stdout=stdout, close_fds=True)
        pids.write('%d\n' % procs['spawner'].pid)

        print 'starting bridge...'
        procs['bridge'] = Popen('./runtime/bridge.py', stdout=stdout, close_fds=True)
        pids.write('%d\n' % procs['bridge'].pid)

        print 'starting xbeed...'
        procs['xbeed'] = Popen('./xbeed/xbeed.py', stdout=stdout, close_fds=True)
        pids.write('%d\n' % procs['xbeed'].pid)

        pids.close()

    except Exception, e:
        print 'Error starting Turk Core:', e
        for proc in procs.values():
            terminate(proc.pid)
        pids.close()
        os.unlink('turkcore.pid')


def start():
    """
    Starts the Turk Core as a group of processes controlled by one master
    process
    """
    master = os.fork()
    if not master:
        launch()
    else:
        print 'Starting Turk Core...'
        os.wait()

def stop():
    """
    Reads the PID file left by start() and sends SIGTERM to all of the daemon
    processes that make up the core
    """
    print 'Stopping Turk Core...'
    core_dir = os.path.dirname(sys.argv[0])
    os.chdir(core_dir)
    pidfile = 'turkcore.pid'

    if not os.path.exists(pidfile):
        print 'Couldn\'t find pidfile! Is Turk Core REALLY running?'
        exit(-1)

    # Get pids from file
    pids = open(pidfile, 'rU')

    # Kill all the Turk Core processes (should be one pid per line)
    [terminate(pid) for pid in pids]

    os.unlink(pidfile)
    pids.close()

def clean():
    """Deletes any data associated with improperly stopped Turk Core"""
    if os.path.exists('turkcore.pid'):
        print 'Removing turkcore.pid...'
        os.unlink('turkcore.pid')
    else:
        print 'No turkcore.pid file to remove!'

def terminate(pid):
    try:
        os.kill(int(pid), signal.SIGTERM)
    except Exception, e:
        print 'Failed to kill process %s: %s' % (pid, e)
    

def main():
    global conf
    """
    Run as a utility for launching Turk Core
    usage: corectl.py start|stop
    """
    parser = OptionParser("usage: %prog [options] <start|stop|restart|clean>")
    parser.add_option("-f", "--config-file", dest="config", type="string", default='core.yml',
                      help="default configuration file")
    (options, args) = parser.parse_args()

    if len(args) != 1:
            parser.error("incorrect number of arguments")

    conf = yaml.load(open(options.config, 'rU'))['corectl']
    print conf

    {'start':start,
     'stop':stop,
     'restart':lambda: (stop(), start()),
     'clean':clean}[args[0]]()


if __name__ == '__main__':
    main()



