#! /usr/bin/python
import socket
import time
import struct
from xml.dom.minidom import parseString
import xmlrpclib
from turkcore.runtime.mapper import MAPPER_ADDR

DRIVER_ID = 6
# TODO: import this or get from config instead of specifying
ZIGBEE_ADDR = "localhost"

description = """
<interfaces>
<output name="red" protocol="TURK_COLOUR_8" />
<output name="green" protocol="TURK_COLOUR_8" />
<output name="blue" protocol="TURK_COLOUR_8" />
</interfaces>
"""

class RGBLamp():
    def __init__(self, device_id, device_addr):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.device_id = device_id
        self.device_addr = device_addr
        self.mapper = xmlrpclib.ServerProxy(MAPPER_ADDR)
        self.red, self.green, self.blue = (0, 0, 0)

    def run(self):
        # Let the kernel pick a port number
        self.s.bind(('', 0))
        # Send a device registration request to Mapper
        self.mapper.register_driver(self.device_id,
                                    DRIVER_ID,
                                    'rgb_lamp',
                                    description,
                                    self.s.getsockname())
        # Send an initialization message to device
        # Contains xbee address (which is removed by driver), and driver id
        msg = struct.pack('>QI', self.device_addr, DRIVER_ID)
        self.s.sendto(msg, (ZIGBEE_ADDR, 1))
        print "RGBLamp driver: sent driver initialization message to device"

        while 1:
            buffer, addr = self.s.recvfrom(1024)
            print "RGBLamp%s received '%s' from Mapper on port %u" % (self.device_addr, buffer, addr[1])
            try:
                data = parseString(buffer).firstChild
                output = data.getAttribute('output')
                value = int(data.firstChild.nodeValue)
                if output == u'red':
                    self.red = value
                elif output == u'green':
                    self.green = value
                elif output == u'blue':
                    self.blue == value
                else:
                    print "error: output %s not implemented!" % output
                # Send data to device. Note: getsockname() only works for unbound sockets once they've sent something already
                self.s.sendto(struct.pack('>QBBBB', self.device_addr, self.red, self.green, self.blue, 0x00),
                                          (ZIGBEE_ADDR, int(self.s.getsockname()[1])))
            except Exception, err:
                print err
                return




# Run as a standalone driver
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print 'usage: rgb_lamp.py [driver decimal id] 0x[xbee hex address] '
    else:
        device_id = int(sys.argv[1], 10)
        device_addr = int(sys.argv[2], 16)
        print "receiver started... driver id: %u, target xbee: 0x%X" % (device_id, device_addr)
        driver = RGBLamp(device_id, device_addr)
        driver.run()

    
