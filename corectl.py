#!/usr/bin/python

import os, sys
import signal
from subprocess import Popen
from sys import stdout

import turkcore.runtime.spawner as spawner
import turkcore.runtime.bridge as bridge
import xbeed

#TODO: These should be optional arguments
xbeed_name = 'xbee0'
serial = '/dev/ttyS0'

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

    try:
        print 'starting spawner...'
        spawner_process = Popen('spawner', executable='./runtime/spawner.py', stdout=stdout, close_fds=True)
        pids.write('%d\n' % spawner_process.pid)

        print 'starting bridge...'
        bridge_process = Popen('bridge', executable='./runtime/bridge.py', stdout=stdout, close_fds=True)
        pids.write('%d\n' % bridge_process.pid)

        print 'starting xbeed...'
        xbeed_process = Popen(['xbeed', xbeed_name, serial], executable='../xbeed/xbeed.py', stdout=stdout, close_fds=True)
        pids.write('%d\n' % xbeed_process.pid)

        pids.close()

    except Exception, e:
        print 'Error starting Turk Core:', e
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
        print 'Failed to kill process %d: %s' % (pid, e)
    

def run():
    """
    Run as a utility for launching Turk Core
    usage: corectl.py start|stop
    """
    try:
        cmd = sys.argv[1]
    except IndexError:
        print 'usage: corectl.py start|stop\n'
        exit(-1)

    {'start':start,
     'stop':stop,
     'clean':clean}[cmd]()


if __name__ == '__main__':
    run()



