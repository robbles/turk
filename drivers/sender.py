#! /usr/bin/python
import socket
import time
import struct
import threading
from xml.dom.minidom import parseString
import xmlrpclib

DRIVER_ID = 2

MAPPER_ADDR = 'http://localhost:44000'

description = """
<interfaces>
<input name="input1" protocol="TURK_UNICODE" />
</interfaces>
"""

class Sender():
    def __init__(self, device_id, device_addr, message):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.device_id = device_id
        self.device_addr = device_addr
        self.mapper = xmlrpclib.ServerProxy(MAPPER_ADDR)
        self.message = message
        self.sentcounter = 0

    def run(self):
        # Let the kernel pick a port number
        self.s.bind(('', 0))
        # Send a device registration request to Mapper
        self.mapper.register_device(self.device_id,
                                    'sender',
                                    description,
                                    self.s.getsockname())

        while 1:
            time.sleep(10)
            # Send data packet to mapper
            self.sentcounter = self.sentcounter + 1
            tempmessage = self.message + str(self.sentcounter)
            self.mapper.route_data(self.device_id, {'input1':tempmessage})

# Run as a standalone driver

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print 'usage: sender.py [driver decimal id] 0x[xbee hex address] [message]'
    else:
        device_id = int(sys.argv[1], 10)
        device_addr = int(sys.argv[2], 16)
        message = sys.argv[3]
        print "sender started... driver id: %u, target xbee: 0x%X" % (device_id, device_addr)
        sender = Sender(device_id, device_addr, message)
        sender.run()


    
