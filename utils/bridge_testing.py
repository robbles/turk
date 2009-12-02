#! /usr/bin/python

import gobject
import dbus
import dbus.service
import dbus.mainloop.glib

TURK_DRIVER_ERROR = "org.turkinnovations.drivers.Error"
TURK_BRIDGE_SERVICE = "org.turkinnovations.core.Bridge"
TURK_BRIDGE_INTERFACE = "org.turkinnovations.core.Bridge"

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
BUS_NAME = dbus.service.BusName(TURK_BRIDGE_SERVICE, dbus.SystemBus())
loop = gobject.MainLoop()

class FakeConfig(dbus.service.Object):
    def __init__(self, driver_id, address):
        print 'initializing FakeConfig'
        path = '/ConfigData/%d/%X' % (driver_id, address)
        dbus.service.Object.__init__(self, BUS_NAME, path)

    dbus.service.signal(dbus_interface=TURK_BRIDGE_INTERFACE, signature='s')
    def NewConfig(self, config):
        print 'NewConfig called'

def fake_config(driver_id, address, config):
    print 'running fake_config'
    f = FakeConfig(driver_id, address)
    f.NewConfig(config)
    loop.quit()



