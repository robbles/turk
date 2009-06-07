#! /usr/bin/python
import socket
import time
import struct
import threading
from xml.dom.minidom import parseString

ZIGBEE_ADDR = "10.0.0.1"

#HW_ADDR = '\x00\x13\xA2\x00\x40\x52\xDA\x9A'
# This is the hardware address of one of my xbees --rob

device = """<request type="register" protocol="TURK_XML">
    <enddevice device_id="DEVICE_ID" name="DEVICE_NAME">
        <interfaces>
            <input name="input1" protocol="TURK_UNICODE" />
        </interfaces>
    </enddevice>
</request>"""

data = """<request type="data" data="">
    <enddevice device_id="DEVICE_ID">
        <input name="input1" data="DRIVER_DATA" />
    </enddevice>
</request>"""


class Sender():
    def __init__(self, device_id, device_addr, message):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.device_id = device_id
        self.device_addr = device_addr
        self.device = device.replace('DEVICE_ID', str(device_id)).replace('DEVICE_NAME', 'sender')
        self.data = data.replace('DRIVER_DATA', message).replace('DEVICE_ID', str(device_id))

    def run(self):
        # Register device with mapper
        self.s.sendto(self.device, ('localhost', 44001))
        while 1:
            time.sleep(10)
            # Send data packet to mapper
            self.s.sendto(self.data, ('localhost', 44000))

# Run as a standalone driver

if __name__ == '__main__':
    import sys
    import os

    if len(sys.argv) < 3:
        print 'usage: sender.py [driver decimal id] 0x[xbee hex address] [message]'
    else:
        device_id = int(sys.argv[1], 10)
        device_addr = int(sys.argv[2], 16)
        message = sys.argv[3]
        if os.fork() == 0:
            print "sender started... driver id: %u, target xbee: 0x%X" % (device_id, device_addr)
            sender = Sender(device_id, device_addr, message)
            sender.run()


    
