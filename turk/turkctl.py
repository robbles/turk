#!/usr/bin/python

import os
import sys
import signal
import yaml
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

        # Set D-Bus address for child processes
        os.environ['DBUS_SESSION_BUS_ADDRESS'] = get_config('dbus.address', self.conf)

        # Setup logging
        global log
        log = init_logging('turkctl', self.conf)


class RunAction(TurkAction):
    """
    Runs one of the Turk services in the foreground
    """
    daemons = ['dbus', 'bridge', 'spawner', 'supervisord', 'supervisorctl']

    def __call__(self, parser, namespace, values, option_string=None):
        TurkAction.__call__(self, parser, namespace, values, option_string)
        log.debug('RunAction for %s' % values)

        try:
            getattr(self, '_'.join(['run', values]))()
        except KeyboardInterrupt:
            log.debug('Received keyboard interrupt, shutting down')
        except BaseException, e:
            log.debug('Exception caught while running %s: %s' % (values, e))

    def run_dbus(self):
        dbus_daemon = get_config('dbus.daemon', self.conf)
        dbus_conf = get_config('dbus.config', self.conf)
        subprocess.call([dbus_daemon, '--config-file', dbus_conf], close_fds=True)

    def run_supervisord(self):
        sd_daemon = get_config('supervisor.daemon', self.conf)
        sd_conf = get_config('supervisor.config', self.conf)
        subprocess.call([sd_daemon, '--nodaemon', '--configuration', sd_conf], close_fds=True)

    def run_supervisorctl(self):
        sd_ctl = get_config('supervisor.controller', self.conf)
        sd_conf = get_config('supervisor.config', self.conf)
        subprocess.call([sd_ctl, '--configuration', sd_conf], close_fds=True)

    def run_bridge(self):
        from turk.bridge import run
        run(self.conf)

    def run_spawner(self):
        from turk.spawner import run
        run(self.conf)


class StartAction(TurkAction):
    """
    Starts Turk using the specified process manager.
    """
    process_managers = ['supervisord', 'supervisord_hook', 'simple']

    def __call__(self, parser, namespace, values, option_string=None):
        TurkAction.__call__(self, parser, namespace, values, option_string)
        log.debug('StartAction')

        print namespace
        print values
        print option_string

        try:
            getattr(self, '_'.join(['start', values]))()
        except KeyboardInterrupt:
            log.debug('Received keyboard interrupt, shutting down')
        except BaseException, e:
            log.debug('Exception caught while running %s: %s' % (values, e))

    def start_supervisord(self):
        print 'start_supervisord'
        sd_daemon = get_config('supervisor.daemon', self.conf)
        sd_conf = get_config('supervisor.config', self.conf)
        retval = subprocess.call([sd_daemon, '--configuration', sd_conf], close_fds=True)
        if not retval:
            print 'started supervisord successfully'
        else:
            print 'oh shit - supervisord is fucked'

    def start_supervisord_hook(self):
        self._close_fds(256)
        for fd in range(20):
            try:
                print '%d: %s' % (fd, os.fstat(fd))
            except:
                break
        _close_fds(256)
        print 'all fds done'
        print 'start_supervisord_hook'
        sd_conf = get_config('supervisor.config', self.conf)
        
        from supervisor import supervisord
        supervisord.main(['--configuration', sd_conf])


    def start_simple(self):
        print 'start_simple'


    def _close_fds(self, til):
        if hasattr(os, 'closerange'):
            os.closerange(3, til)
        else:
            for i in xrange(3, til):
                try:
                    os.close(i)
                except:
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
            spawner = multiprocessing.process(target=run_spawner, args=(conf,), name='spawner')
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




def main():
    """
    Run as a utility for launching Turk
    """
    parser = ArgumentParser(description="Launch and control Turk")

    # configuration file
    parser.add_argument("-f", "--config-file", dest="config", type=FileType('rU'), default='turk.yaml',
                      help="default configuration file")

    # Process control and launchers
    subparsers = parser.add_subparsers(help='Run/Start Commands')

    # Argument parsers for launcher commands
    run_parser = subparsers.add_parser('run', help='Run one of the turk services')
    run_parser.add_argument('daemon', choices=RunAction.daemons, action=RunAction)
    run_parser.add_argument('-d', '--daemonize', action='store_true', help='Fork into the background')

    start_parser = subparsers.add_parser('start', help='Start turk ...right now')
    start_parser.add_argument('-d', '--daemonize', action='store_true', help='Fork into the background')
    start_parser.add_argument('process manager', nargs='?', choices=StartAction.process_managers, default='supervisord', action=StartAction)

    restart_parser = subparsers.add_parser('restart', help='Restart a daemon')
    restart_parser.add_argument('daemon', choices=RunAction.daemons)

    stop_parser = subparsers.add_parser('stop', help='Stop a daemon')
    stop_parser.add_argument('daemon', choices=RunAction.daemons)

    clean_parser = subparsers.add_parser('clean', help='Clean up the process files from a crashed daemon')
    clean_parser.add_argument('daemon', choices=RunAction.daemons)

    # Argument parsers for configuration/project commands
    setup = subparsers.add_parser('start_project', help='Setup a new turk project')
    setup.add_argument('path', default='./', nargs='?', help='The path to setup the project at (defaults to current directory)',
            action=ProjectAction)

    args = parser.parse_args()


if __name__ == '__main__':
    main()
