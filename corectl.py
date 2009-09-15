#!/usr/bin/python

def start():
    """
    Starts the Turk Core as a group of processes. Logs each started daemon's PID
    in a file, so that a later call to stop() can shut them all down.
    """
    import sys, os
    import subprocess

    # Make sure we're in the Turk Core directory
    core_dir = os.path.dirname(sys.argv[0])
    os.chdir(core_dir)
    pidfile = 'turkcore.pid'

    if os.path.exists(pidfile):
        print 'File %s exists - Is Turk Core already running?' % pidfile
        exit(-1)

    pids = open('turkcore.pid', 'w')

    mapper = subprocess.Popen(['runtime/mapper.py'],
                              shell=False,
                              stdout=sys.stdout,
                              close_fds=True)
    pids.write('%d\n' % mapper.pid)

    spawner = subprocess.Popen(['runtime/spawner.py'],
                               shell=False,
                               stdout=sys.stdout,
                               close_fds=True)
    pids.write('%d\n' % spawner.pid)
    pids.close()

    print 'Turk Core started...\n'



def stop():
    """
    Reads the PID file left by start() and sends SIGTERM to all of the daemon
    processes that make up the core
    """
    import os, sys
    import signal

    core_dir = os.path.dirname(sys.argv[0])
    os.chdir(core_dir)
    pidfile = 'turkcore.pid'

    if not os.path.exists(pidfile):
        print 'Couldn\'t find pidfile! Is Turk Core REALLY running?'
        exit(-1)

    # Get pids from file
    pids = open(pidfile, 'rU')

    # Kill all the Turk Core processes
    [os.kill(int(pid), signal.SIGTERM) for pid in pids]

    os.unlink(pidfile)
    pids.close()

    
    

def run():
    """
    Run as a utility for launching Turk Core
    usage: corectl.py start|stop
    """
    import sys
    try:
        cmd = sys.argv[1]
    except IndexError:
        print 'usage: corectl.py start|stop\n'
        exit(-1)

    {'start':start,
     'stop':stop}[cmd]()


if __name__ == '__main__':
    run()



