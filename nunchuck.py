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
        <input name="z button" protocol="TURK_BOOLEAN" />
    </interfaces>
</enddevice>
</request>""")

data = string.Template("""<request type="data">
<enddevice device_id="$device_id">
    <input name="z button" data="$data" />
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
        msg = struct.pack('>QH', self.device_addr, DRIVER_ID)
        self.s.sendto(msg, (ZIGBEE_ADDR, int(self.s.getsockname()[1])))

        while 1:
            buffer, addr = self.s.recvfrom(1024)
            print "NunchuckDriver%d received '%s' from device on port %u" % (self.device_id, ' '.join([c for hex(ord(c)) in buffer]), addr[1])
            # Send data to Mapper
            # Just sending the status of nunchuck's Z button for now
            msg = data.substitute(device_id=self.device_id, data=ord(buffer[-2]))
            self.s.sendto(self.data, ('localhost', 44000))


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

    

