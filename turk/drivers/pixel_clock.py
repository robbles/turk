#! /usr/bin/python
import gobject
import dbus
import dbus.mainloop.glib
from turk.xbeed.xbeed import get_daemon
from xml.dom.minidom import parseString
from ntplib import NTPClient
from datetime import datetime
import turk

DRIVER_ID = 8
SYNC_TIME = 1000 * 60 * 10 # Every 10 minutes (in ms)
TIME_SERVER = 'pool.ntp.org'

"""
### Sample config ###

<command type="time">1264027305.8130212</command>

<command type="timezone">-8</command>

### Sent to device every SYNC_TIME seconds ###
'[' + H + M + S + AM/PM + '@'

"""

from turk import *

SET_TIME_COMMAND = '[%s%s%s%s@'
SET_TEXT_COMMAND = '[%s#'
SET_COLOR_COMMAND = '[%s%s%s%s$'


class PixelClock(dbus.service.Object):
    def __init__(self, device_id, device_addr, bus):
        """
        Registers handlers with the Turk DBus API to receive messages from both
        the Turk server (through XMPP) and the clock (through Zigbee)
        """
        dbus.service.Object.__init__(self, bus,
                                     '/Drivers/PixelClock/%X' % device_addr)
        self.device_id = device_id
        self.device_addr = device_addr
        self.bus = bus
        self.xbee = get_daemon('xbee0', self.bus)

        listen = '/Bridge/ConfigFiles/Drivers/%d' % (self.device_id)
        self.bus.add_signal_receiver(self.update, path=listen)
        print 'Pixel Clock: listening for %s' % listen

        # Timezone is currently not used, but can be set anyways
        self.timezone = 0

        # Make sure sync handler is called every SYNC_TIME milliseconds
        gobject.timeout_add(SYNC_TIME, self.sync)

    def sync(self):
        """ Periodically resets the clock with NTP """
        try:
            self.set_time()
        except Exception, e:
            # emit an error signal for bridge
            self.Error(str(e))
            print e
        finally:
            return True

    def set_time(self, time=None):
        """
        Sets the time on the clock with a simple Zigbee message. Uses NTP to find
        the current time if time argument is not given.
        """
        if not time:
            req = NTPClient().request(TIME_SERVER)
            time = datetime.fromtimestamp(req.tx_time)
            hour = 12 if ((time.hour % 12) == 0) else (time.hour % 12)
            minute, second, pm = time.minute, time.second, (time.hour > 11)
        else:
            hour, minute, second, pm = time

        msg = SET_TIME_COMMAND % (chr(hour), chr(minute), chr(second), chr(pm)) 
        self.xbee.SendData(dbus.ByteArray(msg), dbus.UInt64(self.device_addr), 1)


    def set_text(self, text='    '):
        """
        Sets the text on the clock with a simple Zigbee message. Only four symbols can
        be displayed at once, so it's a bit limited.
        """
        msg = SET_TEXT_COMMAND % (text) 
        self.xbee.SendData(dbus.ByteArray(msg), dbus.UInt64(self.device_addr), 1)


    def update(self, driver, xml):
        """
        Handler called when an update is received from the Turk server through XMPP.
        """
        print 'new update received:'
        print xml
        try:
            tree = parseString(xml)

            command = tree.getElementsByTagName('command')[0]
            ctype = command.getAttribute('type') 

            if ctype == 'time':
                # Parse time value
                timestamp = int(command.childNodes[0].nodeValue)
                time = datetime.fromtimestamp(timestamp)

                # Set the time
                self.set_time(time)

            elif ctype == 'timezone':
                # Parse time value
                self.timezone = int(command.childNodes[0].nodeValue)

            elif ctype == 'text':
                # Parse time value
                text = command.childNodes[0].nodeValue[:4]
                self.set_text(text)

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
    try:
        device_id = int(os.getenv('DEVICE_ID'))
    except:
        print 'PixelClock: DEVICE_ID not provided or invalid'
        exit(-1)
    try:
        device_addr = int(os.getenv('DEVICE_ADDRESS'), 16)
    except:
        print 'PixelClock: DEVICE_ADDRESS not provided or invalid'
        exit(-1)

    bus = os.getenv('BUS', turk.get_config('global.bus'))

    print "Pixel Clock driver started... driver id: %u, target xbee: 0x%X" % (device_id, device_addr)
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    driver = PixelClock(device_id, device_addr, getattr(dbus, bus)())
    driver.run()

    
