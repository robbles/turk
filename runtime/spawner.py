#!/usr/bin/python
"""
The driver-spawner creates a new instance of a driver for each device.
The turk server is queried to get the driver for each device.
"""
#TODO: Implement proper management of driver processes
# i.e. keep track of drivers already running by device_id

import sys
import struct
import urllib2
from xml.dom.minidom import parseString
import string
import subprocess
import os
import gobject
import dbus
import dbus.service
import dbus.mainloop.glib
import yaml

from turkcore.namespace import *

class DriverSpawner(dbus.service.Object):
    
    def __init__(self):
        bus_name = dbus.service.BusName(TURK_SPAWNER_SERVICE, dbus.SystemBus())
        dbus.service.Object.__init__(self, bus_name, '/Spawner')
        self.managed_drivers = []
        self.managed_workers = []
        self.known_devices = []
        self.known_apps = []
        self.SpawnerStarted()
        
    def new_packet(self, rf_data, device_addr):
        print 'Spawner: inspecting a packet of %d bytes from 0x%X' % (len(rf_data), device_addr)

        try:
            # Strip off UDP header - TODO: check to make sure it's a valid request
            rf_data = str(rf_data)
            
            if rf_data.startswith('SPAWN') and (len(rf_data) == 13):
                # Unpack data
                commmand, device_id = struct.unpack('>5sQ', rf_data)
                print "Spawner: received a driver request from xbee 0x%X with device_id %d" % (device_addr, device_id)

                # Get the driver from the server and attempt to run it
                if device_id not in self.known_devices:
                    self.run_driver(device_id, device_addr)
                else:
                    print 'driver for device %d already started' % device_id

        except Exception, e:
            print e
        

    def run_driver(self, device_id, device_addr):
        try:
            driver_info = self.fetch_driver(device_id)
            if driver_info:
                drivername, driverargs = driver_info
                print "starting driver %s" % drivername
                env = {'CONTEXT':'SPAWNER',
                       'DEVICE_ADDRESS':'%X' % device_addr,
                       'DEVICE_ID':str(device_id),
                       'ARGUMENTS':driverargs}
                self.managed_drivers.append(subprocess.Popen(drivername, stdout=sys.stdout, env=env))
                self.known_devices.append(device_id)

                # Emit a signal indicating that driver has been started
                # TODO: check for customized driver/device icon
                self.NewDriver(drivername, 'device.png')
        except OSError, e:
            print 'failed starting driver: %s' % e

    def run_worker(self, worker_id, app_id):
        try:
            worker_info = self.fetch_driver(worker_id)
            if worker_info:
                workername, workerargs = worker_info
                print "starting worker %s" % workername
                env = {'CONTEXT':'SPAWNER',
                       'APP_ID':str(app_id),
                       'ARGUMENTS':workerargs}
                self.managed_workers.append(subprocess.Popen(workername, stdout=sys.stdout, env=env))
                self.known_apps.append(worker_id)

                # Emit a signal indicating that worker has been started
                # TODO: check for customized worker/device icon
                self.NewDriver(workername, 'worker.png')
        except OSError, e:
            print 'failed starting worker: %s' % e

    def fetch_driver(self, device_id):
        try:
            addr = TURK_CLOUD_DRIVER_INFO.substitute(id=device_id)
            driver_info = parseString(urllib2.urlopen(addr).read())
            driver = driver_info.getElementsByTagName('driver')[0]
            if not driver:
                print 'No driver for %d' % device_id
                return None
            filename = driver.getAttribute('file')
            title = driver.getAttribute('title')
            if driver.hasAttribute('argument'):
                args = driver.getAttribute('argument')
            else:
                args = ''
            print "fetched driver info, driver's name is %s" % title
            print "fetching: " + TURK_CLOUD_DRIVER_STORAGE.substitute(filename=filename)
            driverdata = urllib2.urlopen(TURK_CLOUD_DRIVER_STORAGE.substitute(filename=filename))
            filename = 'drivers/%s' % filename
            if not os.path.exists(filename):
                driverfile = open(filename, 'wB')
                driverfile.write(driverdata.read())
                driverfile.close()
                os.chmod(filename, 0755)
                print "saved driver data successfully"
            else:
                print "Driver file already exists! Leaving original"
            return (filename, args)
        except urllib2.HTTPError, err:
            print "Couldn't fetch driver resource - HTTP error %d" % err.getcode()
            return None
        except Exception, err:
            print err
            return None

    def shutdown(self):
        print 'Spawner: shutting down...'
        for driver in self.managed_drivers:
            driver.terminate()
        for worker in self.managed_workers:
            worker.terminate()
        
    @dbus.service.signal(dbus_interface=TURK_SPAWNER_INTERFACE, signature='')
    def SpawnerStarted(self):
        pass

    @dbus.service.signal(dbus_interface=TURK_SPAWNER_INTERFACE, signature='ss')
    def NewDriver(self, driver_name, driver_image):
        print 'new driver found: name %s, image file %s' % (driver_name, driver_image)

    @dbus.service.method(dbus_interface=TURK_SPAWNER_INTERFACE, in_signature='stt', out_signature='')
    def requireService(self, type, service, app):
        """
        Starts a worker or driver if necessary, and returns True if the service
        is running
        """
        print 'Spawner: checking for service %s' % service
        if type == 'driver':
            if service in self.known_devices:
                return
            else:
                raise dbus.DBusException("Driver for %d unknown")
        if type == 'worker':
            self.run_worker(service, app)

            
def run(daemon=False):
    """
    Start Spawner as a standalone process.
    if daemon = True, forks into the background first
    """
    import signal

    conf_file = os.getenv('TURK_CORE_CONF', 'core.yml')
    conf = yaml.load(open(conf_file, 'rU'))['spawner']
    print 'Spawner conf:', conf

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    
    spawner = DriverSpawner()
    signal.signal(signal.SIGTERM, spawner.shutdown)
    
    try:
        bus.add_signal_receiver(spawner.new_packet,
                                dbus_interface='org.turkinnovations.xbeed.XBeeInterface',
                                signal_name="RecievedData",
                                byte_arrays=True)
    except dbus.DBusException:
        traceback.print_exc()
        sys.exit(1)

    loop = gobject.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        spawner.shutdown()


if __name__ == '__main__':
    run()

