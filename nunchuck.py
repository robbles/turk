#! /usr/bin/python
import socket
import time
import struct
from xml.dom.minidom import parseString
import string
import xmlrpclib

DRIVER_ID = 5

ZIGBEE_ADDR = "10.0.0.1"
MAPPER_ADDR = 'http://localhost:44000'

description="""
<interfaces>
<input name="joy_x_axis" protocol="TURK_BYTE" />
<input name="joy_y_axis" protocol="TURK_BYTE" />
<input name="z_button" protocol="TURK_BOOLEAN" />
</interfaces>
"""

class NunchuckDriver():
    def __init__(self, device_id, device_addr):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.device_id = device_id
        self.device_addr = device_addr
        self.mapper = xmlrpclib.ServerProxy(MAPPER_ADDR)

    def run(self):
        # Let the kernel pick a port number
        self.s.bind(('', 0))
        # Send a device registration request to Mapper
        self.mapper.register_device(self.device_id,
                                    'nunchuck',
                                    description,
                                    self.s.getsockname())
        # Send an initialization message to device
        # Contains xbee address (which is removed by driver), and driver id
        msg = struct.pack('>QI', self.device_addr, DRIVER_ID)
        try:
            self.s.sendto(msg, (ZIGBEE_ADDR, 1))
            print "nunchuck driver: sent driver initialization message to device"
        except Exception, err:
            print "nunchuck driver: warning, failed sending init to device"
            print err

        while 1:
            print "nunchuck driver: listening on port %d" % int(self.s.getsockname()[1])
            buffer, addr = self.s.recvfrom(1024)
            print "NunchuckDriver%d received '%s' from device on port %u" % (self.device_id, ' '.join([hex(ord(c)) for c in buffer]), addr[1])
            (joy_x_axis, joy_y_axis,
             accel_x_axis, accel_y_axis, accel_z_axis,
             z_button, c_button) = struct.unpack('>BBHHHBB', buffer)
            # Send data to Mapper
            self.mapper.route_data(self.device_id,
                                   {'joy_x_axis':joy_x_axis,
                                    'joy_y_axis':joy_y_axis,
                                    'z_button':z_button})


# Run as a standalone driver

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print 'usage: nunchuck.py [driver decimal id] 0x[xbee hex address] '
    else:
        device_id = int(sys.argv[1], 10)
        device_addr = int(sys.argv[2], 16)
        print "nunchuck driver started... driver id: %u, target xbee: 0x%X" % (device_id, device_addr)
        driver = NunchuckDriver(device_id, device_addr)
        driver.run()

    

