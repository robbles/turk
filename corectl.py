#!/usr/bin/python

import os, sys
import signal
import multiprocessing

import turkcore.runtime.spawner as spawner
import turkcore.runtime.bridge as bridge
import xbeed

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
        spawner_process = multiprocessing.Process(target=spawner.run)
        spawner_process.start()
        pids.write('%d\n' % spawner_process.pid)

        bridge_process = multiprocessing.Process(target=bridge.run)
        bridge_process.start()
        pids.write('%d\n' % bridge_process.pid)

        xbeed_process = multiprocessing.Process(target=xbeed.main, 
                                                args=('xbee0', '/dev/ttyS0'))
        xbeed_process.start()
        pids.write('%d\n' % xbeed_process.pid)

        pids.close()

        print 'Turk Core started...\n'
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
    def destroy(pid):
        print 'terminating pid %s' % pid
        terminate(int(pid))
    [destroy(pid) for pid in pids]

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
        os.kill(pid, signal.SIGTERM)
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



