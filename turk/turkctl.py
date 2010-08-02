#!/usr/bin/python

import os, sys
import signal
import yaml
import multiprocessing
import logging
from time import sleep
import subprocess
from argparse import ArgumentParser, FileType, Action

from turk import get_config, init_logging

log = logging.getLogger('turkctl')

class TurkAction(Action):
    """
    Sets up the environment and config for running a turkctl command 
    """
    def __call__(self, parser, namespace, values, option_string=None):
        # Load config
        self.conf = yaml.load(namespace.config)
        os.environ['TURK_CONF'] = namespace.config.name

        # Setup logging 
        global log
        log = init_logging('turkctl', self.conf)

class RunAction(TurkAction):
    """
    Runs one of the Turk daemons in the foreground 
    """
    def __call__(self, parser, namespace, values, option_string=None):
        TurkAction.__call__(self, parser, namespace, values, option_string)
        log.debug('RunAction for %s' % values)

        # Set D-Bus address for child processes
        os.environ['DBUS_SESSION_BUS_ADDRESS'] = get_config('dbus.address', self.conf)

        try:
            getattr(self, '_'.join(['run', values]))(self.conf)
        except KeyboardInterrupt:
            log.debug('Received keyboard interrupt, shutting down')
        except BaseException, e:
            log.debug('Exception caught while running %s: %s' % (values, e))

    def run_dbus(self, conf):
        dbus_daemon = get_config('dbus.daemon', self.conf)
        dbus_conf = get_config('dbus.config', self.conf)
        subprocess.call([dbus_daemon, '--config-file', dbus_conf], close_fds=True)

    def run_supervisord(self, conf):
        sd_daemon = get_config('supervisor.daemon', self.conf)
        sd_conf = get_config('supervisor.config', self.conf)
        subprocess.call([sd_daemon, '--nodaemon', '--configuration', sd_conf], close_fds=True)

    def run_bridge(self, conf):
        from turk.bridge import run
        run(conf)

    def run_spawner(self, conf):
        from turk.spawner import run
        run(conf)

    def run_turk(self, conf):
        pass


class ProjectAction(TurkAction):
    """
    Builds a new Turk project folder
    """
    def __call__(self, parser, namespace, values, option_string=None):
        TurkAction.__call__(self, parser, namespace, values, option_string)



def run_turk(conf):
    """
    Starts Turk as a background process. 
    """
    pidfile_path = get_config('turkctl.pidfile', conf)
    
    if os.path.exists(pidfile_path):
        log.warning('File "%s" exists - Is Turk already running?' % pidfile_path)
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

        except Exception, e:
            log.debug('turkctl: error starting Turk: %s' % e)
            os.unlink(pidfile_path)
            exit(-1)

        def finished(*args):
            log.debug('stopping Turk...')
            spawner.terminate()
            bridge.terminate()
            exit(0)

        signal.signal(signal.SIGTERM, finished)

        while 1:
            # Just do nothing until terminated by turkctl
            sleep(1)

    else:
        # Starter process
        pidfile.write('%d\n' % pid)
        pidfile.close()
        log.info('starting Turk...')


def stop(conf):
    """
    Reads the PID file left by start() and sends SIGTERM to all of the daemon
    processes that make up the framework
    """
    print 'stopping Turk...'

    pidfile_path = get_config('turkctl.pidfile', conf)

    if not os.path.exists(pidfile_path):
        print 'Couldn\'t find pidfile! Is Turk REALLY running?'
        return

    # Get pids from file
    pidfile = open(pidfile_path, 'rU')

    # Kill all Turk processes (should be one pid per line)
    [terminate(pid) for pid in pidfile]

    os.unlink(pidfile_path)
    pidfile.close()

def clean(conf):
    """Deletes any data associated with improperly stopped Turk"""

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
    Run as a utility for launching Turk
    usage: turkctl.py start|stop
    """
    parser = ArgumentParser(description="Launch and control Turk processes")

    # configuration file
    parser.add_argument("-f", "--config-file", dest="config", type=FileType('rU'), default='turk.yaml',
                      help="default configuration file")

    # Process control and launchers
    subparsers = parser.add_subparsers(help='Run/Start Commands')

    # The Turk daemons
    daemons = ['turk', 'dbus', 'bridge', 'spawner', 'supervisord']

    # Argument parsers for launcher commands
    run_parser = subparsers.add_parser('run', help='Run a daemon in the foreground')
    run_parser.add_argument('daemon', choices=daemons, action=RunAction)

    start_parser = subparsers.add_parser('start', help='Start a daemon in the background')
    start_parser.add_argument('daemon', choices=daemons)

    restart_parser = subparsers.add_parser('restart', help='Restart a daemon')
    restart_parser.add_argument('daemon', choices=daemons)

    stop_parser = subparsers.add_parser('stop', help='Stop a daemon')
    stop_parser.add_argument('daemon', choices=daemons)

    clean_parser = subparsers.add_parser('clean', help='Clean up the process files from a crashed daemon')
    clean_parser.add_argument('daemon', choices=daemons)

    # Argument parsers for configuration/project commands
    setup = subparsers.add_parser('start_project', help='Setup a new turk project')
    setup.add_argument('path', default='./', nargs='?', help='The path to setup the project at (defaults to current directory)',
            action=ProjectAction)
    
    args = parser.parse_args()



if __name__ == '__main__':
    main()



