#!/usr/bin/env python

import os
import sys
import signal
import yaml
import logging
from time import sleep
import subprocess
import shutil
from argparse import ArgumentParser, FileType, Action

import turk
from turk import load_config, get_config, init_logging, DEFAULT_CONF_FILE


class LaunchAction(Action):
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
        try:
            self.conf = load_config(namespace.config)
        except Exception, e:
            print 'Error loading configuration file "%s":' % namespace.config
            print e
            exit()

        os.environ['TURK_CONF'] = namespace.config

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


class RunAction(LaunchAction):
    """
    Runs one of the Turk services in the foreground
    """
    daemons = ['dbus', 'bridge', 'manager', 'supervisord']

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

    def do_manager(self):
        from turk.manager import run
        run(self.conf)


class StartAction(LaunchAction):
    """
    Starts Turk using the specified process manager.
    """
    managers = ['supervisord', 'simple']

    def do_supervisord(self):
        sd_conf = get_config('supervisor.config', self.conf)
        try:
            from supervisor import supervisord
            args = ['--configuration', sd_conf, '--nodaemon']
            supervisord.main(args)
        except BaseException, e:
            self.log.error('Error starting supervisord: %s' % e)
            exit(1)

    def do_simple(self):
        raise NotImplementedError('Command not implemented')


class StopAction(LaunchAction):
    """
    Stops the process manager.
    """
    def do_supervisord(self):
        sd_ctl = get_config('supervisor.controller', self.conf)
        sd_conf = get_config('supervisor.config', self.conf)
        subprocess.call([sd_ctl, '--configuration', sd_conf, 'shutdown'], close_fds=True)

    def do_simple(self):
        raise NotImplementedError('Command not implemented')


class RestartAction(LaunchAction):
    """
    Restarts the process manager, one of the turk services, or a driver process.
    """
    def __call__(self, parser, namespace, name, option_string=None):
        self.prepare(namespace)
        sd_ctl = get_config('supervisor.controller', self.conf)
        sd_conf = get_config('supervisor.config', self.conf)
        if namespace.driver:
            self.log.debug('Restarting driver %s' % name)
            #TODO: do this with manager instead of supervisord?
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



class ShellAction(LaunchAction):
    """
    Starts a supervisorctl shell or runs a command.
    """
    def __call__(self, parser, namespace, command, option_string=None):
        self.prepare(namespace)
        sd_conf = get_config('supervisor.config', self.conf)
        cmd_line = ['--configuration', sd_conf]
        if command:
            cmd_line.append(command)
        try:
            from supervisor import supervisorctl
            supervisorctl.main(cmd_line)
        except KeyboardInterrupt:
            print '^C'
        except BaseException, e:
            import traceback;traceback.print_exc() 
            self.log.error('Exception caught: %s' % e)


class ProjectAction(Action):
    """
    Builds a new Turk project folder
    """
    def __call__(self, parser, namespace, value, option_string=None):
        project_dir = value
        skel_dir = os.path.join(turk.INSTALL_DIR, 'skel')
        print 'copying from %s to %s' % (skel_dir, project_dir)

        try:
            if not os.path.exists(project_dir):
                print 'Creating %s' % project_dir
                os.mkdir(project_dir)
            else:
                print 'Error: %s already exists!' % project_dir
                return
                    
            for path, subdirs, files in os.walk(skel_dir):

                for i, subdir in enumerate(subdirs):
                    # Skip hidden dirs
                    if subdir.startswith('.'):
                        del subdirs[i]
                        continue

                    # Skip contents of these dirs
                    if subdir in ['var', 'log']:
                        del subdirs[i]

                    newdir = os.path.join(project_dir, path[len(skel_dir)+1:], subdir)
                    print 'creating directory %s' % os.path.abspath(newdir)
                    os.mkdir(newdir)

                for f in files:
                    if f.endswith('.pyc'):
                        continue
                    skel = os.path.join(path, f)
                    newfile = os.path.join(project_dir, path[len(skel_dir)+1:], f)
                    print 'copying %s to %s' % (os.path.basename(skel), os.path.abspath(newfile))
                    shutil.copy2(os.path.join(path, f), newfile)

        except OSError, e:
            print e
            return
        

def main(config_file='./turk.yaml'):
    """
    Run as a utility for launching Turk
    """
    parser = ArgumentParser(description="Launch and control Turk")

    # configuration file
    parser.add_argument("-f", "--config-file", dest="config", metavar='FILENAME',
        default=config_file, help="default configuration file")

    # Process control and launchers
    subparsers = parser.add_subparsers()

    # Argument parsers for launcher commands
    # NOTE: these don't take options for the subcommands, because it's too hard
    # to get right, and all configuration can be done in the config files anyways

    start_parser = subparsers.add_parser('start', help='Start turk')
    start_parser.add_argument('-d', '--daemonize', action='store_true', help='Fork into the background')
    start_parser.add_argument('manager', nargs='?', choices=StartAction.managers, default=StartAction.managers[0], action=StartAction)

    stop_parser = subparsers.add_parser('stop', help='Stop turk')
    stop_parser.add_argument('manager', nargs='?', choices=StartAction.managers, action=StopAction, default=StartAction.managers[0])

    restart_parser = subparsers.add_parser('restart', help='Restart a daemon, driver, or turk itself')
    restart_parser.add_argument('--driver', action='store_true', help='Look in known drivers for process to restart')
    restart_parser.add_argument('process', nargs='?', action=RestartAction, default='turk')

    run_parser = subparsers.add_parser('run', help='Run one of the turk services')
    run_parser.add_argument('daemon', choices=RunAction.daemons, action=RunAction)
    run_parser.add_argument('-d', '--daemonize', action='store_true', help='Fork into the background')

    shell_parser = subparsers.add_parser('shell', help='Start a supervisorctl shell or run a command')
    shell_parser.add_argument('command', nargs='?', action=ShellAction, default='', help='Run this command instead of starting an interactive shell')

    # Argument parsers for configuration/project commands
    project = subparsers.add_parser('newproject', help='Setup a new turk project')
    project.add_argument('path', help='The path to setup the project at (defaults to current directory)',
            action=ProjectAction)

    args = parser.parse_args()


if __name__ == '__main__':
    main()
