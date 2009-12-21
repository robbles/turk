#!/usr/bin/python

import os, sys
import signal
from subprocess import Popen
from sys import stdout
from optparse import OptionParser

default_name = 'xbee0'

def launch(options):
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
        procs['xbeed'] = Popen(['./xbeed/xbeed.py', '-b', options.baudrate, default_name, options.serial], stdout=stdout, close_fds=True)
        pids.write('%d\n' % procs['xbeed'].pid)

        pids.close()

    except Exception, e:
        print 'Error starting Turk Core:', e
        for proc in procs.values():
            terminate(proc.pid)
        pids.close()
        os.unlink('turkcore.pid')


def start(options):
    """
    Starts the Turk Core as a group of processes controlled by one master
    process
    """
    master = os.fork()
    if not master:
        launch(options)
    else:
        print 'Starting Turk Core...'
        os.wait()

def stop(options):
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

def clean(options):
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
    

def run():
    """
    Run as a utility for launching Turk Core
    usage: corectl.py start|stop
    """
    usage = "usage: %prog [options] <start|stop|restart|clean>"
    parser = OptionParser(usage)
    parser.add_option("-s", "--serial", dest="serial", type="string", default='/dev/ttyS0',
                      help="serial port to use for XBee communication")
    parser.add_option("-b", "--baudrate", dest="baudrate", type="string", default='9600',
                      help="serial baudrate")
    (options, args) = parser.parse_args()

    if len(args) != 1:
            parser.error("incorrect number of arguments")

    {'start':start,
     'stop':stop,
     'restart':lambda opt: (stop(opt), start(opt)),
     'clean':clean}[args[0]](options)


if __name__ == '__main__':
    run()



