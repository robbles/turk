#! /usr/bin/python
import gobject
import dbus
import dbus.mainloop.glib
from turk.xbeed import xbeed
from xml.dom.minidom import parseString
import turk

DRIVER_ID = 6

"""
### Sample config ###

<command type="color">#63A7E7</command>

### Sent to device ###
"[\x63\xA7\xE7]"

"""

TURK_DRIVER_ERROR = "org.turkinnovations.drivers.Error"
TURK_BRIDGE = "org.turkinnovations.turk.Bridge"

class RGBLamp(dbus.service.Object):
    def __init__(self, device_id, device_addr, bus):
        dbus.service.Object.__init__(self, bus,
                                     '/Drivers/RGBLamp/%X' % device_addr)
        self.device_id = device_id
        self.device_addr = device_addr
        self.bus = bus
        self.xbee = xbeed.get_daemon('xbee0', self.bus)

        self.bus.add_signal_receiver(self.receive_data,
                                path='/XBeeModules/%X' % device_addr,
                                dbus_interface=xbeed.XBEED_INTERFACE,
                                signal_name="RecievedData",
                                byte_arrays=True)
        listen = '/Bridge/ConfigFiles/Drivers/%d' % (self.device_id)
        self.bus.add_signal_receiver(self.new_config, path=listen)

        print 'RGB Lamp: listening for %s' % listen

    def receive_data(self, rf_data, hw_addr):
        """ Called when device sends us data. Might happen when device is reset """
        print 'RGB Lamp: Received %d bytes from device' % len(rf_data)
        
    def new_config(self, driver, xml):
        print 'new xml config received:'
        print xml
        try:
            tree = parseString(xml)

            command = tree.getElementsByTagName('command')[0]
            ctype = command.getAttribute('type') 

            if ctype == 'color':
                # Parse hex color into RGB values
                color = command.childNodes[0].nodeValue.lstrip('# \n\r')
                red, green, blue = [int(color[i:i+2], 16) for i in range(0, 6, 2)]

                # Build a message of the form "[RGB]"
                msg = ''.join(['[', chr(red), chr(green), chr(blue), ']'])

                # Send it to the device
                print 'setting color to #%02X%02X%02X' % (red, green, blue)
                self.xbee.SendData(dbus.ByteArray(msg), dbus.UInt64(self.device_addr), 1)

        except Exception, e:
            # emit an error signal for bridge
            self.Error(e.message)
            print e
        
    def run(self):
        loop = gobject.MainLoop()
        loop.run()

    @dbus.service.signal(dbus_interface=TURK_DRIVER_ERROR, signature='s') 
    def Error(self, message):
        """ Called when an error/exception occurs. Emits a signal for any relevant
            system management daemons and loggers """
        pass
        

# Run as a standalone driver
if __name__ == '__main__':
    import os
    device_id = int(os.getenv('DEVICE_ID'))
    device_addr = int(os.getenv('DEVICE_ADDRESS'), 16)
    bus = os.getenv('BUS', turk.get_config('global.bus'))
    print "RGB Lamp driver started... driver id: %u, target xbee: 0x%X" % (device_id, device_addr)
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    driver = RGBLamp(device_id, device_addr, getattr(dbus, bus)())
    driver.run()

    
