#!/usr/bin/python
"""
Base class for service processes.
"""

import signal
import os
import gobject
import dbus
import dbus.service
import dbus.mainloop.glib
import yaml
import turk
from turk.config import TurkConfig

class ServiceStartException(Exception):
    pass

class Service(dbus.service.Object):

    def __init__(self, conf='turk.yaml', service_name=__name__):
        """
        Start service using information from configuration file (or equivalent dictionary-like object)
        """
        try:
            # Make an attempt to set the process name
            import setproctitle
            setproctitle.setproctitle(service_name)
        except:
            pass

        # Load configuration
        self.conf = TurkConfig(conf)

        # Initialize logging
        self.log = turk.init_logging(service_name, conf)

        # Connect to D-Bus
        self.bus = self.get_bus_connection()


    def run(self):
        """ Run the main loop (GLib) """

        signal.signal(signal.SIGTERM, self.shutdown)
        loop = gobject.MainLoop()

        try:
            loop.run()
        except BaseException, e:
            self.log.critical("Caught exception in main loop: %s" % e)
            self.shutdown()

    def initialize(self):
        pass

    def shutdown(self):
        """ Perform actions required for shutting down the service """
        self.log.debug('shutting down')
    
    
    def get_bus_connection(self):
        """ Return a connection to the D-Bus Session Bus, using the GLib main loop """
        try:
            # Get reference to Session Bus
            mainloop = dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            bus = dbus.SessionBus(mainloop=mainloop)
            return bus
        except dbus.DBusException, e:
            self.log.critical('Failed to connect to DBus Session Bus')
            self.log.debug('DBus socket is at %s' % os.getenv('DBUS_SESSION_BUS_ADDRESS'))
            raise ServiceStartException(e)


