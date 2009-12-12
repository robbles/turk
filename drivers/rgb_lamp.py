#! /usr/bin/python
import gobject
import dbus
import dbus.mainloop.glib
import xbeed
from xml.dom.minidom import parseString

DRIVER_ID = 6

"""
### Sample config ###

"<?xml version="1.0" encoding="UTF-8"?>
<color>
    <red>255</red>
    <green>255</green>
    <blue>255</blue>
</color>"

### Sent to device ###
"[\xFF\xFF\xFF]"

"""

TURK_DRIVER_ERROR = "org.turkinnovations.drivers.Error"
TURK_BRIDGE = "org.turkinnovations.core.Bridge"

class RGBLamp(dbus.service.Object):
    def __init__(self, device_id, device_addr):
        dbus.service.Object.__init__(self, dbus.SessionBus(),
                                     '/Drivers/RGB_Lamp/%X' % device_addr)
        self.device_id = device_id
        self.device_addr = device_addr
        self.bus = dbus.SystemBus()
        self.xbee = xbeed.get_daemon('xbee0', self.bus)

        self.bus.add_signal_receiver(self.receive_data,
                                path='/XBeeModules/%X' % device_addr,
                                dbus_interface=xbeed.XBEED_INTERFACE,
                                signal_name="RecievedData",
                                byte_arrays=True)

        self.bus.add_signal_receiver(self.new_config, path='/Bridge/ConfigFiles/RGB_Lamp%d' % (self.device_id))

        print 'RGB Lamp: listening for %s' % ('/Bridge/ConfigFiles/RGB_Lamp%d' % (self.device_id))

    def receive_data(self, rf_data, hw_addr):
        """ Called when device sends us data. Might happen when device is reset """
        print 'RGB Lamp: Received %d bytes from device' % len(rf_data)
        
    def new_config(self, driver, xml, app):
        print 'new xml config received: %s' % xml
        tree = parseString(xml)
        try:
            red, green, blue = [int(tree.getElementsByTagName(color)[0].firstChild.nodeValue)
                                for color in ['red', 'green', 'blue']]
            print 'setting color to #%02X%02X%02X' % (red, green, blue)

            # Build a message of the form "[RGB]"
            msg = ''.join(['[', chr(red), chr(green), chr(blue), ']'])

            # Send it to the device
            self.xbee.SendData(dbus.ByteArray(msg), dbus.UInt64(self.device_addr), 1)


        except Exception, e:
            # emit an error signal for bridge
            self.error(e.message)
            print e
        
    def run(self):
        loop = gobject.MainLoop()
        loop.run()

    @dbus.service.signal(dbus_interface=TURK_DRIVER_ERROR, signature='s') 
    def error(self, message):
        """ Called when an error/exception occurs. Emits a signal for any relevant
            system management daemons and loggers """
        pass
        

# Run as a standalone driver
if __name__ == '__main__':
    import os
    device_id = int(os.getenv('DEVICE_ID'))
    device_addr = int(os.getenv('DEVICE_ADDRESS'), 16)
    print "RGB Lamp driver started... driver id: %u, target xbee: 0x%X" % (device_id, device_addr)
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    driver = RGBLamp(device_id, device_addr)
    driver.run()

    
