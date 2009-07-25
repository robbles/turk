#! /usr/bin/python
import socket
import time
import struct
from xml.dom.minidom import parseString
import xmlrpclib

DRIVER_ID = 1
ZIGBEE_ADDR = "10.0.0.1"
MAPPER_ADDR = 'http://localhost:44000'

description = """
<interfaces>
<output name="output1" protocol="TURK_UNICODE" />
</interfaces>
"""

class Receiver():
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
                                    'receiver',
                                    description,
                                    self.s.getsockname())
        # Send an initialization message to device
        # Contains xbee address (which is removed by driver), and driver id
        msg = struct.pack('>QI', self.device_addr, DRIVER_ID)
        self.s.sendto(msg, (ZIGBEE_ADDR, int(self.s.getsockname()[1])))
        print "receiver driver: sent driver initialization message to device"

        while 1:
            buffer, addr = self.s.recvfrom(1024)
            print "Receiver%s received '%s' from Mapper on port %u" % (self.device_addr, buffer, addr[1])
            print "--> sending to device address of 0x%X" % self.device_addr
            time.sleep(1)
            # Send data to device. Note: getsockname() only works for unbound sockets once they've sent something already
            self.s.sendto(struct.pack('>Q', self.device_addr) + buffer, (ZIGBEE_ADDR, int(self.s.getsockname()[1])))




# Run as a standalone driver
#FIXME: This SHOULDN'T fork, because otherwise the Spawner has
# to clean up the intermediate process (Zombie process!)
if __name__ == '__main__':
    import sys
    import os

    if len(sys.argv) < 3:
        print 'usage: receiver.py [driver decimal id] 0x[xbee hex address] '
    else:
        device_id = int(sys.argv[1], 10)
        device_addr = int(sys.argv[2], 16)
        if os.fork() == 0:
            print "receiver started... driver id: %u, target xbee: 0x%X" % (device_id, device_addr)
            receiver = Receiver(device_id, device_addr)
            receiver.run()

    
