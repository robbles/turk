#!/usr/bin/env python

import os
import sys
import signal
import yaml
import logging
from time import sleep
import subprocess
from argparse import ArgumentParser, FileType, Action

from turk import load_config, get_config, init_logging, DEFAULT_CONF_FILE


class ProcessAction(Action):
    """
    Sets up the environment and config for running a turkctl command
    """
    def __call__(self, parser, namespace, values, option_string=None):
        self.prepare(namespace)

        # Delegate to a method of this Action
        self.log.debug('%s -> %s' % (type(self).__name__, values))
        try:
            getattr(self, '_'.join(['do', values]))()
        except KeyboardInterrupt:
            self.log.debug('Received keyboard interrupt, shutting down')
        except BaseException, e:
            self.log.error('Exception caught while running %s: %s' % (values, e))


    def prepare(self, namespace):
        # Load config
        self.conf = load_config(namespace.config)

        os.environ['TURK_CONF'] = namespace.config.name

        # Set D-Bus address for child processes
        os.environ['DBUS_SESSION_BUS_ADDRESS'] = get_config('dbus.address', self.conf)

        # Setup logging
        self.log = init_logging('turkctl', self.conf)


class NotImplementedAction(Action):
    """ 
    Temporary class for sketching out options that haven't been implemented yet
    """
    def __call__(self, parser, namespace, values, option_string=None):
        raise NotImplementedError('Command not implemented')


class RunAction(ProcessAction):
    """
    Runs one of the Turk services in the foreground
    """
    daemons = ['dbus', 'bridge', 'spawner', 'supervisord']

    def do_dbus(self):
        dbus_daemon = get_config('dbus.daemon', self.conf)
        dbus_conf = get_config('dbus.config', self.conf)
        subprocess.call([dbus_daemon, '--config-file', dbus_conf], close_fds=True)

    def do_supervisord(self):
        sd_daemon = get_config('supervisor.daemon', self.conf)
        sd_conf = get_config('supervisor.config', self.conf)
        subprocess.call([sd_daemon, '--nodaemon', '--configuration', sd_conf], close_fds=True)

    def do_bridge(self):
        from turk.bridge import run
        run(self.conf)

    def do_spawner(self):
        from turk.spawner import run
        run(self.conf)


class StartAction(ProcessAction):
    """
    Starts Turk using the specified process manager.
    """
    managers = ['supervisord', 'simple']

    def do_supervisord(self):
        sd_daemon = get_config('supervisor.daemon', self.conf)
        sd_conf = get_config('supervisor.config', self.conf)
        retval = subprocess.call([sd_daemon, '--configuration', sd_conf], close_fds=True)
        if not retval:
            self.log.debug('started supervisord successfully')
        else:
            self.log.error('oh shit - supervisord is fucked')

    def do_simple(self):
        raise NotImplementedError('Command not implemented')

    def _close_fds(self, til):
        if hasattr(os, 'closerange'):
            os.closerange(3, til)
        else:
            for i in xrange(3, til):
                try:
                    os.close(i)
                except:
                    pass


class StopAction(ProcessAction):
    """
    Stops the process manager.
    """
    def do_supervisord(self):
        sd_ctl = get_config('supervisor.controller', self.conf)
        sd_conf = get_config('supervisor.config', self.conf)
        subprocess.call([sd_ctl, '--configuration', sd_conf, 'shutdown'], close_fds=True)

    def do_simple(self):
        raise NotImplementedError('Command not implemented')


class RestartAction(ProcessAction):
    """
    Restarts the process manager, one of the turk services, or a driver process.
    """
    def __call__(self, parser, namespace, name, option_string=None):
        self.prepare(namespace)
        sd_ctl = get_config('supervisor.controller', self.conf)
        sd_conf = get_config('supervisor.config', self.conf)
        if namespace.driver:
            self.log.debug('Restarting driver %s' % name)
            #TODO: do this with spawner instead of supervisord?
            subprocess.call([sd_ctl, '--configuration', sd_conf, 'restart', name], close_fds=True)
        else:
            self.log.debug('Restarting service %s' % name)
            if name in ('turk', 'supervisord'):
                # Restart main manager process
                subprocess.call([sd_ctl, '--configuration', sd_conf, 'reload'], close_fds=True)
            elif name in RunAction.daemons:
                # Restart the service by name
                subprocess.call([sd_ctl, '--configuration', sd_conf, 'restart', name], close_fds=True)
            else:
                self.log.error('Service %s is unknown (try using --driver)')
                exit(3)



class ShellAction(ProcessAction):
    """
    Starts a supervisorctl shell or runs a command.
    """
    def __call__(self, parser, namespace, command, option_string=None):
        self.prepare(namespace)
        sd_ctl = get_config('supervisor.controller', self.conf)
        sd_conf = get_config('supervisor.config', self.conf)
        cmd_line = [sd_ctl, '--configuration', sd_conf]
        if command:
            cmd_line.append(command)
        try:
            subprocess.call(cmd_line, close_fds=True)
        except KeyboardInterrupt:
            print '^C'
        except BaseException, e:
            self.log.error('Exception caught: %s' % e)


class ProjectAction(Action):
    """
    Builds a new Turk project folder
    """
    def __call__(self, parser, namespace, values, option_string=None):
        pass


def main(config_file=DEFAULT_CONF_FILE):
    """
    Run as a utility for launching Turk
    """
    parser = ArgumentParser(description="Launch and control Turk")

    # configuration file
    parser.add_argument("-f", "--config-file", dest="config", type=FileType('rU'), 
            default=config_file, help="default configuration file")

    # Process control and launchers
    subparsers = parser.add_subparsers(help='Run/Start Commands')

    # Argument parsers for launcher commands
    # NOTE: these don't take options for the subcommands, because it's too hard
    # to get right, and all configuration can be done in the config files anyways

    run_parser = subparsers.add_parser('run', help='Run one of the turk services')
    run_parser.add_argument('daemon', nargs='?', default='supervisord', choices=RunAction.daemons, action=RunAction)
    run_parser.add_argument('-d', '--daemonize', action='store_true', help='Fork into the background')

    start_parser = subparsers.add_parser('start', help='Start turk ...right now')
    start_parser.add_argument('-d', '--daemonize', action='store_true', help='Fork into the background')
    start_parser.add_argument('manager', nargs='?', choices=StartAction.managers, default=StartAction.managers[0], action=StartAction)

    stop_parser = subparsers.add_parser('stop', help='Stop turk')
    stop_parser.add_argument('manager', nargs='?', choices=StartAction.managers, action=StopAction, default=StartAction.managers[0])

    restart_parser = subparsers.add_parser('restart', help='Restart a daemon, driver, or turk itself')
    restart_parser.add_argument('--driver', action='store_true', help='Look in known drivers for process to restart')
    restart_parser.add_argument('process', nargs='?', action=RestartAction, default='turk')

    shell_parser = subparsers.add_parser('shell', help='Start a supervisorctl shell or run a command')
    shell_parser.add_argument('command', nargs='?', action=ShellAction, default='', help='Run this command instead of starting an interactive shell')

    # Argument parsers for configuration/project commands
    setup = subparsers.add_parser('start_project', help='Setup a new turk project')
    setup.add_argument('path', default='./', nargs='?', help='The path to setup the project at (defaults to current directory)',
            action=ProjectAction)

    args = parser.parse_args()


if __name__ == '__main__':
    main()
