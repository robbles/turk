#!/usr/bin/python
"""
The driver-spawner creates a new instance of a driver by request.
Driver instances can be specified in the configuration file or through the
D-Bus API. The turk server is queried to get the driver for any unknown devices.
"""

import sys
import logging
import urllib2
from xml.dom.minidom import parseString
import subprocess
import os
import gobject
import dbus
import dbus.service
import dbus.mainloop.glib
import yaml
import turk
from turk import get_config

log = turk.init_logging('spawner')

class DriverSpawner(dbus.service.Object):
    
    def __init__(self, bus, drivers, autostart=[]):
        self.bus = bus
        bus_name = dbus.service.BusName(turk.TURK_SPAWNER_SERVICE, bus)
        dbus.service.Object.__init__(self, bus_name, '/Spawner')
        self.managed_drivers = {}
        self.drivers = drivers

        # Start each driver after a delay to ensure all services are running
        for driver in autostart:
            gobject.timeout_add(2000, self.start_driver, driver['device_id'], driver['filename'], driver['env'])

        # Emit signal to show it's ready
        self.SpawnerStarted()
        

    def start_driver(self, device_id, filename, env):
        """ Starts a driver and adds it to the list of managed drivers """
        if filename.startswith('/'):
            # Absolute driver names
            path = filename
        else:
            # Relative driver names indicate they're installed in the drivers folder
            path = ''.join([self.drivers, '/', filename])

        env['CONTEXT'] = 'SPAWNER'
        env['BUS'] = type(self.bus).__name__
        env['DEVICE_ID'] = str(device_id)

        try:
            self.managed_drivers[device_id] = subprocess.Popen(path, stdout=sys.stdout, env=env)
            log.debug('Autostarted driver for device %s' % (env['DEVICE_ID']))
        except Exception, e:
            log.debug('failed starting driver "%s": %s' % (filename, e))
        finally:
            return False


    def fetch_driver(self, url, driver_id):
        """ 
        Fetches a driver file from a web server, using driver_id to
        identify the location.
        """
        try:
            driver_info = parseString(urllib2.urlopen(url).read())
        except urllib2.HTTPError, err:
            log.debug("Couldn't fetch driver metadata - HTTP error %d" % err.getcode())
            return None

        driver = driver_info.getElementsByTagName('driver')[0]
        if not driver:
            log.debug('Driver %d not found' % driver_id)
            return None
        filename = driver.getAttribute('file')
        log.debug("fetching: " + turk.TURK_CLOUD_DRIVER_STORAGE.substitute(filename=filename))

        try:
            driverdata = urllib2.urlopen(turk.TURK_CLOUD_DRIVER_STORAGE.substitute(filename=filename))
        except urllib2.HTTPError, err:
            log.debug("Couldn't fetch driver files - HTTP error %d" % err.getcode())
            return None

        path = ''.join([self.drivers, '/', filename])

        if not os.path.exists(filename):
            driverfile = open(filename, 'wB')
            driverfile.write(driverdata.read())
            driverfile.close()
            os.chmod(filename, 0755)
            log.debug("saved driver data successfully")
        else:
            log.debug("Driver file already exists! Leaving original")
        return filename


    def shutdown(self):
        log.debug('shutting down...')
        for device_id, driver in self.managed_drivers.iteritems():
            log.debug('terminating driver %d' % device_id)
            driver.terminate()
        
    @dbus.service.signal(dbus_interface=turk.TURK_SPAWNER_INTERFACE, signature='')
    def SpawnerStarted(self):
        log.debug('started')

    @dbus.service.signal(dbus_interface=turk.TURK_SPAWNER_INTERFACE, signature='s')
    def DriverStarted(self, driver_name):
        log.debug('driver "%s" started' % (driver_name, driver_image))

    @dbus.service.method(dbus_interface=turk.TURK_SPAWNER_INTERFACE, in_signature='tsa(ss)', out_signature='')
    def StartDriverByName(self, device_id, driver, env):
        """ Starts a driver and manages it.  """
        log.debug('trying to run driver "%s" for device %d' % (driver, device_id))

        self.start_driver(device_id, driver, dict(env))
        
    @dbus.service.method(dbus_interface=turk.TURK_SPAWNER_INTERFACE, in_signature='tta(ss)', out_signature='')
    def StartDriverByID(self, device_id, driver_id, env):
        """ Starts a driver and manages it.  """
        log.debug('trying to run driver %d for device %d' % (driver, device_id))
        raise NotImplementedError


def get_spawner(bus=None, path='/Spawner'):
    """ 
    Returns a D-Bus proxy for the Spawner 
    """
    if not bus:
        bus = getattr(dbus, get_config('global.bus'))()

    return bus.get_object(turk.TURK_SPAWNER_SERVICE, '/Spawner')

    
            
def run(conf='/etc/turk/turk.yml'):
    """
    Start Spawner as a standalone process, using information
    from configuration file (or equivalent dictionary-like object)
    """
    import signal

    # Load configuration if given as filename
    if isinstance(conf, basestring):
        try:
            conf = yaml.load(open(conf, 'rU'))['spawner']
        except Exception:
            log.debug('Failed opening configuration file "%s"' % (conf))
            exit(1)

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus_label = get_config('global.bus', conf)
    try:
        bus = getattr(dbus, bus_label)()
    except:
        default_bus = get_config('global.bus')
        log.warning("Failed to access bus named %s, using default: %s" % (bus_label, default_bus))
        bus = getattr(dbus, default_bus)()

    if not get_config('spawner.debug', conf):
        log.setLevel(logging.WARNING)

    drivers = get_config('spawner.drivers', conf)
    autostart = get_config('spawner.autostart', conf)
    
    spawner = DriverSpawner(bus, drivers, autostart)
    signal.signal(signal.SIGTERM, spawner.shutdown)
    
    loop = gobject.MainLoop()

    try:
        loop.run()
    except KeyboardInterrupt:
        spawner.shutdown()


if __name__ == '__main__':
    run()

