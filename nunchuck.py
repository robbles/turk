#! /usr/bin/python
import socket
import time
import struct
from xml.dom.minidom import parseString
import string

DRIVER_ID = 5

ZIGBEE_ADDR = "10.0.0.1"

device = string.Template("""<request type="register" protocol="TURK_XML">
<enddevice device_id="$device_id" name="nunchuck">
    <interfaces>
        <input name="z_button" protocol="TURK_BOOLEAN" />
    </interfaces>
</enddevice>
</request>""")

data_template = string.Template("""<request type="data">
<enddevice device_id="$device_id">
    <input name="z_button" data="$data" />
</enddevice>
</request>""")

class NunchuckDriver():
    def __init__(self, device_id, device_addr):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.device_id = device_id
        self.device_addr = device_addr
        self.device = device.substitute(device_id=self.device_id)

    def run(self):
        # Send a device registration request to Mapper
        self.s.sendto(self.device, ('localhost', 44001))
        # Send an initialization message to device
        # Contains xbee address (which is removed by driver), and driver id
        msg = struct.pack('>QI', self.device_addr, DRIVER_ID)
        self.s.sendto(msg, (ZIGBEE_ADDR, int(self.s.getsockname()[1])))
        print "nunchuck driver: sent driver initialization message to device"

        while 1:
            print "nunchuck driver: listening on port %d" % int(self.s.getsockname()[1])
            buffer, addr = self.s.recvfrom(1024)
            print "NunchuckDriver%d received '%s' from device on port %u" % (self.device_id, ' '.join([hex(ord(c)) for c in buffer]), addr[1])
            # Send data to Mapper
            # Just send the raw data for now
            if buffer == 1:
                data = 'TRUE'
            else:
                data = 'FALSE'
            msg = data_template.substitute(device_id=self.device_id, data=data)
            self.s.sendto(msg, ('localhost', 44000))


# Run as a standalone driver

if __name__ == '__main__':
    import sys
    import os

    if len(sys.argv) < 3:
        print 'usage: nunchuck.py [driver decimal id] 0x[xbee hex address] '
    else:
        device_id = int(sys.argv[1], 10)
        device_addr = int(sys.argv[2], 16)
        if os.fork() == 0:
            print "nunchuck driver started... driver id: %u, target xbee: 0x%X" % (device_id, device_addr)
            driver = NunchuckDriver(device_id, device_addr)
            driver.run()

    

