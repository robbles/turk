#!/usr/bin/env python
# encoding: utf-8
"""
xbeed.py

Communicates with an XBee Series 2.5 module thorough a serial port.
Allows access to the Zigbee PAN through DBUS or XML-RPC.

Created by Rob O'Dwyer on 2009-10-21.
Copyright (c) 2009 Turk Innovations. All rights reserved.
"""
import pdb

import os
import sys
from time import sleep
from optparse import OptionParser
from serial import Serial, SerialException
from struct import pack, unpack
from StringIO import StringIO
import yaml
import logging

import gobject
import dbus
import dbus.service
import dbus.mainloop.glib

from turk import get_config, get_configs
import turk

XBEED_SERVICE = 'org.turkinnovations.xbeed'
XBEED_INTERFACE = 'org.turkinnovations.xbeed.XBeeInterface'
XBEED_DAEMON_OBJECT = '/XBeeInterfaces/%s'
XBEED_MODULE_OBJECT = '/XBeeModules/%X'

log = turk.init_logging('xbeed')

class XBeeDaemon(dbus.service.Object):
    """
    Main class which connects dbus API and serial communication
    name: Unique DBUS object name for this instance
    All other arguments are passed off to the underlying pySerial implementation
    """
    def __init__(self, name, port, escaping=True, baudrate=9600):
        self.port, self.baudrate = port, baudrate
        self.serial_type = EscapingSerial if escaping else Serial

        self.object_path = XBEED_DAEMON_OBJECT % name
        self.partial = PartialFrame()
        dbus.service.Object.__init__(self, BUS_NAME, self.object_path)

        self.connected = False
        self.monitored = False
        
        log.debug( 'trying to open serial port %s:%s' % (self.port, self.baudrate))
        if self.connect(False):
            gobject.timeout_add(2000, self.connect, False)
        
    def serial_read(self, fd, condition, *args):
        """ Called when there is data available from the serial port """
        try:
            buffer = self.serial.read(256)
        except OSError:
            self.connect()
            return True
        try:
            if(self.partial.add(buffer)):
                packet = XBeeModuleFrame.parse(*self.partial.get_data())
                self.handle_packet(packet)
        except ChecksumFail, e:
            log.debug(e)
        except UnknownFrameType, e:
            log.debug(e)
        return True # Keep calling this function when data is available
    
    def handle_packet(self, packet):
        log.debug(packet)
        if isinstance(packet, ReceivePacket):
            XBeeModule.get(packet.hw_addr).RecievedData(packet.rf_data, packet.hw_addr)

    def connect(self, disable_first=True):
        """ Disconnects the current serial port and continually attempts to reconnect """
        if disable_first:
            log.debug('Disconnecting serial port...')
            self.serial.close()
            self.serial.write = lambda *args: None

        try:
            self.serial = self.serial_type(self.port, self.baudrate, timeout=0)
            if not self.monitored:
                gobject.io_add_watch(self.serial.fileno(), gobject.IO_IN, self.serial_read)
                self.monitored = True
            log.debug( 'serial connected')
            log.debug('Serial successfully connected!')

            self.connected = True
            # Stop trying to reconnect
            return False
        except SerialException, e:
            # Re-schedule another attempt to connect
            return True
            
    @dbus.service.method(XBEED_INTERFACE, in_signature='ayty', out_signature='', byte_arrays=True)  
    def SendData(self, rf_data, hw_addr, frame_id):
        """ Sends an RF data packet to the specified XBee module """
        log.debug('SendData called, sending %d bytes to address 0x%X' % (len(rf_data), hw_addr))
        packet = TransmitRequest(hw_addr=hw_addr, rf_data=str(rf_data), frame_id=frame_id)
        try:
            if self.connected:
                packet.write_frame(self.serial)
        except OSError:
            self.connect()
    
    @dbus.service.method(XBEED_INTERFACE, in_signature='s', out_signature='s')    
    def GetInfo(self, arg):
        """ Returns some marginally useful info about the current xbeed instance """
        log.debug('GetInfo called')
        return self.object_path
        
    @dbus.service.method(XBEED_INTERFACE, in_signature='tay', out_signature='', byte_arrays=True)
    def FakeReceivedData(self, rf_data, hw_addr):
        log.debug('Faking receive of packet from 0x%X, %d bytes' % (hw_addr, len(rf_data)) )
        XBeeModule.get(hw_addr).RecievedData(rf_data, hw_addr)
        
class EscapingSerial(Serial):
    """
    Handles escaping and un-escaping of framing bytes
    Bytes 0x7E, 0x7D, 0x11, 0x13 are escaped as [0x7D, byte^0x20]
    """ 
    def __init__(self, *args, **kwargs):
        Serial.__init__(self, *args, **kwargs)
        self.escape_flag = False
        
    def write(self, data):
        Serial.write(self, ''.join(escape(data)))
       
    def read(self, size=1):
        data = Serial.read(self, size)
        out = StringIO()
        for byte in data:
            if self.escape_flag:
                out.write(chr(ord(byte) ^ 0x20))
                self.escape_flag = False
            elif byte == '\x7D':
                self.escape_flag = True
            else:
                out.write(byte)
        return out.getvalue()
                     

class PartialFrame(object):
    """ Stores up serial data until a full frame is received """
    def __init__(self):
        self.buffer = ''
        self.last = None
     
    def add(self, data):
        packets = ''.join([self.buffer, data]).split('\x7E')
        packets = packets[1:] if packets[0] == '' else packets
        if(len(packets[0]) > 6):
            frame_len, api_id = unpack('>HB', packets[0][0:3])
            if len(packets[0]) >= (frame_len + 3):
                self.last = (packets[0][:frame_len+3], api_id, frame_len)
                self.buffer = ''.join(packets[1:])
                return True
        self.buffer = ''.join(packets)
        return False
    
    def get_data(self):
        """ Returns all the buffered data """
        return self.last


class XBeeModuleFrame(object):
    """Abstract class for parsing serial API packets"""
    # Used for mapping frame data to packet types based on api_id field
    api_ids = {}
    # Used to format frame signatures based on variable-length fields
    length_mod = None
    
    @classmethod
    def parse(cls, data, api_id, length):
        # Raise exception containing real / expected value if checksum fails
        if not validate_checksum(data, offset=2):
            raise ChecksumFail(ord(data[-1]), generate_checksum(data, offset=2))
        
        # Parse and return specific packet structure
        if api_id not in API_IDS:
            raise UnknownFrameType("Received unknown frame, api_id=0x%X" % api_id)
        ptype = API_IDS[api_id]
        if ptype.length_mod:
            signature = ptype.signature % (length - ptype.length_mod)
        else:
            signature = ptype.signature
        fields = unpack(signature, data)
        return ptype(*fields)
      
class TransmitStatus(XBeeModuleFrame):
    """ When a TX Request is completed, the module sends a TX Status message. This message
        will indicate if the packet was transmitted successfully or if there was a failure."""
    signature = '>3xBHBBBx'
    api_id = 0x8B
    statuses = {0x00:'Success', 0x02:'CCA Failure', 0x15:'Invalid Destination', 0x21:'ACK Failure',
                0x22:'Not Joined', 0x23:'Self-Addressed', 0x24:'Address Not Found', 0x25:'Route Not Found'}
    def __init__(self, frame_id, net_addr, retries, status, discovery):
        self.frame_id = frame_id
        self.net_addr = net_addr
        self.retries = retries
        self.status = (status, self.statuses.get(status, 'Unknown Status'))
        self.discovery = discovery
    
    def __str__(self):
        return '[TransmitStatus for frame %d: %s]' % (self.frame_id, self.status)

class ReceivePacket(XBeeModuleFrame):
    """ When the module receives an RF packet, it is sent out the UART using this message type. """
    signature = '>3xQHB%dsx'
    length_mod = 12
    api_id = 0x90
    def __init__(self, hw_addr, net_addr, options, rf_data):
        self.hw_addr = hw_addr
        self.net_addr = net_addr
        self.options = options
        self.rf_data = rf_data
        
    def __str__(self):
        return '[ReceivePacket %d bytes from 0x%X]' % (len(self.rf_data), self.hw_addr)
        
class ModemStatus(XBeeModuleFrame):
    """ RF module status messages are sent from the module in response to specific conditions."""
    signature = '>3xBx'
    api_id = 0x8A
    statuses = {0:'Hardware Reset', 1:'Watchdog Timer Reset', 2:'Associated', 3:'Disassociated', 
                4:'Synchonization Lost', 5:'Coordinator Re-alignment', 6:'Coordinator started'}
    def __init__(self, status):
        self.status = (status, self.statuses.get(status, 'Unknown Status'))
        
    def __str__(self):
        return '[ModemStatus: %s]' % (self.status,)
        
class XBeeClientFrame(object):
    """Abstract class for constructing new packets to send to XBee module"""
    def get_frame(self):
        """ Returns the binary frame representation of the packet """
        s = StringIO()
        self.write_frame(s)
        return s.getvalue()
        
    def write_frame(self, fd):
        """ Writes the binary representation of the packet to a file-like object """
        fd.write(pack('>BH', 0x7E, self.length))
        frame_data = pack(self.signature, *self.fields)
        checksum = generate_checksum(frame_data)
        fd.write(frame_data)
        fd.write(chr(checksum))
        
class TransmitRequest(XBeeClientFrame):
    api_id = 0x10
    signature = '>BBQHBB%ds'
    def __init__(self, hw_addr, rf_data, frame_id=0, net_addr=0xFFFE):
        self.frame_id = frame_id
        self.fields = (self.api_id, frame_id, hw_addr, net_addr, 0x00, 0x00, rf_data)
        self.signature = self.signature % len(rf_data)
        self.length = len(rf_data) + 14
   
API_IDS = {0x8B: TransmitStatus, 0x90: ReceivePacket, 0x8A: ModemStatus}


class XBeeModule(dbus.service.Object):
    """ Represents a remote XBee module, and signals when packets are received
        from that module."""
    modules = {}
    def __init__(self, hw_addr):
        dbus.service.Object.__init__(self, BUS_NAME, XBEED_MODULE_OBJECT % (hw_addr))
    
    @classmethod
    def get(cls, hw_addr):
        if hw_addr not in cls.modules:
            cls.modules[hw_addr] = XBeeModule(hw_addr)
        return cls.modules[hw_addr]
        
    @dbus.service.signal(dbus_interface=XBEED_INTERFACE, signature='ayt') 
    def RecievedData(self, rf_data, hw_addr):
        """ Called when data is received from the module """
        pass
       
     
def generate_checksum(frame, offset=0):
    """ Generates the checksum byte for this frame. The algorithm consists of
    adding all bytes in the frame data and subtracting the result from 0xFF.
    NOTE: this assumes the checksum is initially set to zero or not included """
    return 0xFF - (reduce(lambda x, y: x + ord(y), frame[offset:], 0x00) & 0xFF)
    
def validate_checksum(frame, offset=0):
    """ Validates the checksum by adding all bytes and comparing to 0xFF """
    return (reduce(lambda x, y: x + ord(y), frame[offset:], 0x00) & 0xFF) == 0xFF


class ChecksumFail(Exception):
    def __str__(self):
        return '0x%X != 0x%X' % self.args if len(self.args) is 2 else None
        
class InvalidPacketLength(Exception): pass

class UnknownFrameType(Exception):
    def __repr__():
        return 'Unknown frame type'
    
class SendFailure(dbus.DBusException):
    _dbus_error_name = 'org.turkinnovations.xbeed.SendFailure'

class UnknownFrameType(Exception):
    pass


def escape(data):
    yield data[0]
    for byte in data[1:]:
        if byte in ['\x7E', '\x7D', '\x11', '\x13']:
            yield '\x7D'
            yield chr(ord(byte) ^ 0x20)
        else:
            yield byte

def unescape(data):
    escape_flag = False
    for byte in data:
        if byte == '\x7D':
            escape_flag = True
        else:
            yield chr(ord(byte) ^ 0x20) if escape_flag else byte
            escape_flag = False


def get_daemon(name, bus):
    """
    Returns a proxy object corresponding to the XBeeDaemon of the given name.
    on the given bus
    """
    return bus.get_object(XBEED_SERVICE, XBEED_DAEMON_OBJECT % name)
  
def get_module(hw_addr, bus):
    """
    Returns a proxy object representing the XBeeModule with the given hardware address.
    """
    return bus.get_object(XBEED_SERVICE, XBEED_MODULE_OBJECT % hw_addr)
        
def send_data(xbee, rf_data, hw_addr, frame_id):
    """
    An alias for xbee.send_data that converts the arguments to the correct D-Bus types first.
    Sends data to an XBee module on the PAN.
    """
    return xbee.SendData(dbus.ByteArray(rf_data), dbus.UInt64(hw_addr), frame_id)

def fake_data(name, bus, hw_addr, data):
    """
    Fakes an incoming packet from a given XBee module. Useful for debugging drivers.
    """
    daemon = get_daemon(name, bus)
    daemon.FakeReceivedData(dbus.ByteArray(data), dbus.UInt64(hw_addr))


BUS_NAME = None

def run(conf='/etc/turk/turk.yml'):
    global BUS_NAME
    
    if isinstance(conf, basestring):
        try:
            conf = yaml.load(open(conf, 'rU'))['xbeed']
        except Exception:
            log.debug( 'failed opening configuration file "%s"' % (conf))
            exit(1)

    log = turk.init_logging('xbeed', conf, debug=get_config('xbeed.debug'))

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = getattr(dbus, get_config('global.bus', conf))()
    BUS_NAME = dbus.service.BusName(XBEED_SERVICE, bus)
    
    daemon = XBeeDaemon(*get_configs(('name', 'port', 'escaping', 'baudrate'), conf, 'xbeed'))

    mainloop = gobject.MainLoop()
    mainloop.run()     

if __name__ == "__main__":
    sys.exit(run())
