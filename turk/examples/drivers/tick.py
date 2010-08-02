#! /usr/bin/env python
import gobject
import dbus
import dbus.service
import dbus.mainloop.glib
import turk

DRIVER_ID = 2

"""
Sends an update with the current date/time every one second. Useful for waking
up web-based Tapps.
"""

class Tick(dbus.service.Object):
    def __init__(self, bus):
        dbus.service.Object.__init__(self, bus, '/Drivers/Tick')
        self.bus = bus
        gobject.timeout_add(1000, self.tick)
        print 'Tick: running'
        
    def run(self):
        loop = gobject.MainLoop()
        loop.run()

    def tick(self):
        try:
            update = '<tick />'
            bridge = self.bus.get_object(turk.TURK_BRIDGE_SERVICE, '/Bridge')
            bridge.PublishUpdate('app', update, unicode(DRIVER_ID),
                    reply_handler=self.handle_reply, error_handler=self.handle_error)
        except dbus.DBusException, e:
            print 'Tick: error posting data to app', e
        except Exception, e:
            print e
        finally:
            # Just keep ticking
            return True

    def handle_reply(*args): pass
    def handle_error(*args): pass

    @dbus.service.signal(dbus_interface=turk.TURK_DRIVER_ERROR, signature='s') 
    def Error(self, message):
        """ Called when an error/exception occurs. Emits a signal for any relevant
            system management daemons and loggers """
        pass
        

if __name__ == '__main__':
    import os
    bus = os.getenv('BUS', turk.get_config('global.bus'))
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    driver = Tick(getattr(dbus, bus)())
    driver.run()

    

