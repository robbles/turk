#! /usr/bin/python

import dbus
import dbus.service
import dbus.mainloop.glib
import gobject
from optparse import OptionParser

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
DEFAULT_BUS = dbus.SystemBus()

class SignalEmitter(dbus.service.Object):
    def __init__(self, bus=DEFAULT_BUS, service=None, interface=None, path=None, member=None):
        print 'initializing SignalEmitter'
        print 'bus=%s, service=%s, interface=%s, path=%s, member=%s' % (bus,service,interface,path,member)
        self.bus = bus
        self.service = service
        self.interface = interface
        self.path = path
        self.member = member
        if service:
            bus_name = dbus.service.BusName(service, bus)
        else:
            bus_name = bus
        if member:
            # Make a new instance method with the right name
            instancemethod = type(self.EmitSignal)
            def newmethod(self, *args):
                pass
            newmethod.__name__ = member
            newmethod = instancemethod(newmethod, self, SignalEmitter)

            # Apply the decorator function to it
            signal = dbus.service.signal(dbus_interface=interface, signature='')(newmethod)
            # Add the dummy method name and make it point to the original method
            self.__setattr__(member, signal)

        dbus.service.Object.__init__(self, bus_name, path)

    def EmitSignal(self):
        print 'EmitSignal method called'

    @dbus.service.signal(dbus_interface='org.test.interface', signature='')
    def NewSignal(self):
        print 'NewSignal called'

def emit_signal(loop, options):
    f = SignalEmitter(DEFAULT_BUS, options.service, options.interface, options.path, options.member)
    if options.member:
        cmd = 'f.%s(f)' % options.member
        print cmd
        exec cmd
    else:
        f.NewSignal()
    print 'emitted signal successfully'
    loop.quit()


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-u", "--session", action="store_true", dest="session", default=False, help="Use D-BUS Session Bus instead of System Bus")
    parser.add_option("-s", "--service", dest="service", help="D-BUS service name")
    parser.add_option("-i", "--interface", dest="interface", help="D-BUS interface name")
    parser.add_option("-p", "--path", dest="path", help="D-BUS path name")
    parser.add_option("-m", "--member", dest="member", help="D-BUS member name")
    (options, args) = parser.parse_args()

    if options.session:
        DEFAULT_BUS = dbus.SessionBus()

    loop = gobject.MainLoop()
    gobject.timeout_add(0, emit_signal, loop, options)
    loop.run()



