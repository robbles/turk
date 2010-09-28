#!/usr/bin/python
"""
Starts and manages drivers and other processes. Assigns a numeric ID to each
process so they can be tracked and controlled via a simple D-BUS API.
"""

import sys
import logging
import subprocess
import os
import gobject
import dbus
import dbus.service
import dbus.mainloop.glib
import yaml
import uuid
import turk
from turk import get_config

log = logging.getLogger('manager')

class Process(object):
    """ Represents a process. Can be started and stopped. """
    def __init__(self, id, path, args, env):
        self.id = id
        self.path = path
        self.args = args
        self.env = env
        self.start_count = 0

    def start(self):
        """ Starts the process in the background """
        command = [self.path] + self.args
        self.process = subprocess.Popen(command, stdout=sys.stdout, env=self.env, close_fds=True)
        self.start_count += 1

    def stop(self):
        """ Terminates the process """
        self.process.terminate()


class ProcessManager(dbus.service.Object):
    
    def __init__(self, bus, driver_dir, autostart=[]):
        self.bus = bus
        bus_name = dbus.service.BusName(turk.TURK_MANAGER_SERVICE, bus)
        dbus.service.Object.__init__(self, bus_name, '/ProcessManager')
        self.managed_processes = {}
        self.driver_dir = driver_dir

        # Start all processes after a delay to ensure all services are running
        for process in autostart:
            gobject.timeout_add(100, self.start_process, process['path'], process['args'], process['env'])

        # Emit signal to show it's ready
        self.ProcessManagerStarted()
        

    def start_process(self, path, args, env):
        """ Starts a process and adds it to the list of managed processes """
        if not os.path.isabs(path):
            # Relative process paths indicate they're installed in the drivers folder
            path = ''.join([self.driver_dir, '/', path])

        process_id = self.get_id()
        
        env['MANAGER_ID'] = process_id
        env['DBUS_SESSION_BUS_ADDRESS'] = os.getenv('DBUS_SESSION_BUS_ADDRESS')

        try:
            self.managed_processes[process_id] = Process(process_id, path, args, env)
            self.managed_processes[process_id].start()
            log.debug('Autostarted driver for device %s' % (process_id))
        except Exception, e:
            log.debug('Failed starting process %s/%s: %s' % (process_id, path, e))
        finally:
            return False

    def get_id(self):
        """ Returns a new unique ID for a managed process """
        return str(uuid.uuid4())

    def shutdown(self):
        log.debug('shutting down...')
        for device_id, process in self.managed_processes.iteritems():
            log.debug('terminating process %s' % device_id)
            process.stop()
        
    @dbus.service.signal(dbus_interface=turk.TURK_MANAGER_INTERFACE, signature='')
    def ProcessManagerStarted(self):
        log.debug('started')

    @dbus.service.signal(dbus_interface=turk.TURK_MANAGER_INTERFACE, signature='s')
    def ProcessStarted(self, process_name):
        log.debug('process "%s" started' % process_name)

    @dbus.service.method(dbus_interface=turk.TURK_MANAGER_INTERFACE, in_signature='tsa(ss)', out_signature='')
    def StartProcessByName(self, id, driver, env):
        """ Starts a process given a command or executable path and manages it.  """
        log.debug('trying to run process "%s" for driver %d' % (driver, id))
        self.start_driver(device_id, driver, dict(env))
        
    @dbus.service.method(dbus_interface=turk.TURK_MANAGER_INTERFACE, in_signature='t', out_signature='')
    def RestartProcessByID(self, device_id):
        """ Restarts a running driver identified by id """
        log.debug('trying to restart driver %d' % (device_id))
        if device_id in self.managed_processes:
            old = self.managed_processes.pop(device_id)
            old.stop()
            self.managed_processes[device_id] = Process(device_id, old.path, old.env)

    @dbus.service.method(dbus_interface=turk.TURK_MANAGER_INTERFACE, in_signature='t', out_signature='')
    def StopProcessByID(self, device_id):
        """ Stops and removes a running driver identified by id """
        log.debug('trying to stop driver %d' % (device_id))
        if device_id in self.managed_processes:
            self.managed_processes.pop(device_id).stop()

    @dbus.service.method(dbus_interface=turk.TURK_MANAGER_INTERFACE, in_signature='', out_signature='a(ts)')
    def GetProcessList(self):
        """ Returns an array of (id, driver executable) pairs for all running processes """
        log.debug('returning list of processes')
        return [(id, os.path.basename(self.managed_processes[id].path)) for id in self.managed_processes.keys()]


def get_manager(bus=None, path='/ProcessManager'):
    """ 
    Returns a D-Bus proxy for the ProcessManager 
    """
    if not bus:
        bus = getattr(dbus, get_config('global.bus'))()

    return bus.get_object(turk.TURK_MANAGER_SERVICE, '/ProcessManager')

    
def run(conf='turk.yaml'):
    """
    Start ProcessManager as a standalone process, using information
    from configuration file (or equivalent dictionary-like object)
    """
    import signal
    try:
        import setproctitle
        setproctitle.setproctitle(__name__)
    except:
        pass

    # Load configuration if given as filename
    if isinstance(conf, basestring):
        try:
            conf = yaml.load(open(conf, 'rU'))
        except Exception:
            log.critical('Failed opening configuration file "%s"' % conf)
            exit(1)

    log = turk.init_logging('manager', conf)

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    try:
        bus = dbus.SessionBus()
    except dbus.DBusException:
        log.critical('Failed to connect to DBus SessionBus')
        log.debug('DBus UNIX socket is at %s' % os.getenv('DBUS_SESSION_BUS_ADDRESS'))
        exit(1)

    driver_dir = get_config('manager.drivers', conf)
    autostart = get_config('manager.autostart', conf)
    
    manager = ProcessManager(bus, driver_dir, autostart)
    signal.signal(signal.SIGTERM, manager.shutdown)
    
    loop = gobject.MainLoop()

    try:
        loop.run()
    except KeyboardInterrupt:
        manager.shutdown()


if __name__ == '__main__':
    run()

