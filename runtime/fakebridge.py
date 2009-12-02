#! /usr/bin/python

import gobject
import dbus
import dbus.service
import dbus.mainloop.glib

TURK_DRIVER_ERROR = "org.turkinnovations.drivers.Error"
TURK_BRIDGE_SERVICE = "org.turkinnovations.core.Bridge"
TURK_BRIDGE_INTERFACE = "org.turkinnovations.core.Bridge"


class FakeConfig(dbus.service.Object):
    def __init__(self, driver_id, address):
        print 'initializing FakeConfig'
        path = '/ConfigData/%d' % (driver_id)
        bus_name = dbus.service.BusName(TURK_BRIDGE_SERVICE, dbus.SystemBus())
        dbus.service.Object.__init__(self, bus_name, path)

    dbus.service.signal(dbus_interface=TURK_BRIDGE_INTERFACE, signature='s')
    def NewConfig(self, config):
        print 'NewConfig called'

def emit_signal(driver_id, address, message, loop):
    f = FakeConfig(driver_id, address)
    f.NewConfig(message)
    print 'emitted a signal: ' + '/ConfigData/%d.NewConfig' % (driver_id)
    loop.quit()


if __name__ == '__main__':
    from sys import argv
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    loop = gobject.MainLoop()
    gobject.timeout_add(0, emit_signal, int(argv[1]), int(argv[2], 16), argv[3], loop)
    loop.run()


