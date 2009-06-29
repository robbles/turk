#! /usr/bin/python

import socket
import Queue
import time
from xml.dom import minidom
from sqlite3 import dbapi2 as sqlite
import threading
import signal


###################### Mapper Classes ##########################################

# Important note: device ID's (output_device, input_device) are INTEGERS,
# input/output names (output_name, input_name) are STRINGS
# DON'T mix them up, or angry rogue unicorns will eat your computer

class Mapper():
    """
    Keeps track of all devices, and handles mapping
    of DeviceOutputs and DeviceInputs.
    Also keeps all the data in a SQLite database and restores previous 
    data on relaunch
    """
    def __init__(self, dcport=44000, ccport=44001):
        self.devices = {}
        self.data_comm = DataComm(self, dcport)
        self.command_comm = CommandComm(self, ccport)
        self.data_comm.start()
        self.command_comm.start()
        self.dataqueue = Queue.Queue(50)

    # interfaces is an xml dom node, not a string
    def add_device(self, device_id, name, interfaces, addr):
        print "Mapper: adding device id:%d, name:%s" % (device_id, name)
        if (self.db.execute('select * from devices where device_id=\'%d\'' % device_id).fetchall()):
            print "Mapper: WARNING - device already registered - removing old device..."
            # Remove the old device
            self.db.execute('delete from devices where device_id=\'%s\'' % device_id)
            self.db.commit()

        new_device = EndDevice(name, addr, self)
        inputs = interfaces.getElementsByTagName('input')
        outputs = interfaces.getElementsByTagName('output')
        for input in inputs:
            new_device.add_input(input.getAttribute('name'), input.getAttribute('protocol'))
        for output in outputs:
            new_device.add_output(output.getAttribute('name'), output.getAttribute('protocol'))
        # Add to the database while Mapper is running
        self.db.execute('insert into devices values (\'%s\', \'%s\', \'%s\')' % (device_id, name, interfaces.toxml()))
        self.db.commit()
        # Add the new device to the list of devices
        self.devices[device_id] = new_device

        # Try to use any old mappings that haven't been applied yet
        self.apply_mappings()

    def apply_mappings(self):
        maplist=[mapping for mapping in self.old_mappings if((mapping[0] in self.devices) and (mapping[2] in self.devices))]
        for mapping in maplist:
                print "Applying mapping: %s:%s -> %s:%s" % (mapping[0], mapping[1], mapping[2], mapping[3])
                self.attach(mapping[0], mapping[1], mapping[2], mapping[3])
                #self.old_mappings.remove(mapping)


    # Attaches an output to an input source. Doesn't affect database, just implements a mapping
    def attach(self, output_device, output_name, input_device, input_name):
        print "Mapper: trying to attach %d.%s to %d.%s" % (output_device, output_name, input_device, input_name)
        try:
            output = self.devices[output_device].outputs[output_name]
            input = self.devices[input_device].inputs[input_name]
            input.register(output)

        except KeyError:
            print "Error while trying to map inputs/outputs - make sure they both exist..."
            print "Input devices's inputs:", self.devices[input_device].inputs
            print "Output device's outputs:", self.devices[output_device].outputs
            return
        print "Mapper: mapping success"
        

    # Creates a new mapping between two devices (input to output), then attaches them
    def associate(self, output_device, output_name, input_device, input_name):
        print "Mapper: trying to associate %d.%s with %d.%s" % (output_device, output_name, input_device, input_name)
        # Silently delete any old mappings for this output, then add it
        # TODO: Should similar mappings be deleted? or just overridden later?
        self.db.execute('delete from mappings where output_device=%d and output_name=\'%s\'' % (output_device, output_name))
        self.db.execute('insert into mappings values(%d, \'%s\', %d, \'%s\')' % (output_device, output_name, input_device, input_name))
        self.db.commit()
        self.attach(output_device, output_name, input_device, input_name)



    # Main Loop

    def run(self):
        # Start database connection - can only be accessed in this thread!
        self.db = sqlite.connect('mappings.db')

        # Delete any remaining devices from failed shutdown
        self.db.execute('delete from devices')
        self.db.commit()

        # Get all the old mappings, and try to use them later as devices are registered
        self.old_mappings = self.db.execute('select * from mappings').fetchall()
        print 'old_mappings: ', self.old_mappings

        while 1:
            # Receive messages from Command/DataComm through dataqueue
            # Note: queue timeout is necessary to be able to catch signals while blocking
            try:
                message = self.dataqueue.get(block=True, timeout=60)
            except Queue.Empty:
                continue

            # New data from a device
            if message['type'] == "data":
                device = message['device']
                id = int(device.getAttribute('device_id'))
                for input in device.getElementsByTagName('input'):
                    try:
                        name = input.getAttribute('name')
                        data = input.getAttribute('data')
                        self.devices[id].inputs[name].notify_outputs(data)
                    except Exception:
                        print "Error accessing data from message or device/input"

            # Shut down the entire mapping system
            elif message['type'] == 'shutdown':
                print "Mapper: shutting down"
                self.data_comm.shutdown()
                self.command_comm.shutdown()
                self.db.execute('delete from devices')
                self.db.commit()
                self.db.close()
                break

            # Register a new device
            elif message['type'] == 'register':
                for enddevice in message['request'].getElementsByTagName('enddevice'):
                    print "found an end device"
                    device_id = int(enddevice.getAttribute('device_id'))
                    name = enddevice.getAttribute('name')
                    interfaces = enddevice.getElementsByTagName('interfaces')[0]
                    addr = message['addr']
                    self.add_device(device_id, name, interfaces, addr)

            # Make a new mapping between an input and output(s)
            elif message['type'] == 'mapping':
                for mapping in message['request'].getElementsByTagName('mapping'):
                    print "found a mapping"
                    # Get the first input (there should only be one)
                    input = mapping.getElementsByTagName('input')[0]
                    input_data = (int(input.getAttribute('device_id')), input.getAttribute('name'))
                    print "found input: name %s" % input_data[0]
                    # Get all the outputs to be mapped to it
                    outputs = mapping.getElementsByTagName('output')
                    for output in outputs:
                        output_data = (int(output.getAttribute('device_id')), output.getAttribute('name'))
                        print "found output: name %s" % output_data[0]
                        self.associate(output_device=int(output_data[0]),
                                              output_name=output_data[1],
                                              input_device=int(input_data[0]),
                                              input_name=input_data[1])
                

    def shutdown(self, signum, frame):
        print "Mapper: received a shutdown request"
        self.dataqueue.put({'type':'shutdown'})


###################### Observer Pattern Classes ################################

class DeviceOutput:
    """ 
    Corresponds to an output on an end device - attaches to a DeviceInput
    and watches for new data
    """
    def __init__(self, name, protocol, parent):
        self.name = name
        self.protocol = protocol
        self.parent = parent

    def notify(self, event):
        print "%s.%s: received %s" % (self.parent.name, self.name, event)
        self.parent.parent.data_comm.socket.sendto(event, self.parent.addr)


# TODO: Make sure an output can't be registered twice with an input...
# Maybe use a dictionary instead of a list...?
class DeviceInput:
    """
    DeviceInput object that corresponds to an input
    from a device. Notifies all registered DeviceOutputs
    when it receives data from the driver
    """
    def __init__(self, name, protocol):
        self.outputs = []
        self.name = name
        self.protocol = protocol
    
    def register(self, output):
        if output not in self.outputs:
            self.outputs.append(output)
        else:
            print "Output %s already registered to Input %s" % (output.name, self.name)
        
    def unregister(self, output):
        self.outputs.remove(output)

    def notify_outputs(self, event):
        for output in self.outputs:
            output.notify(event)


class EndDevice:
    """
    Represents an instance of a device driver and it's
    device - contains dictionaries of all inputs/outputs
    """
    def __init__(self, name, addr, parent):
        self.outputs = {}
        self.inputs = {}
        self.name = name
        self.addr = addr
        self.parent=parent

    def add_output(self, name, protocol):
        self.outputs[name] = DeviceOutput(name, protocol, self)

    def add_input(self, name, protocol):
        self.inputs[name] = DeviceInput(name, protocol)


##################### Socket Communication Classes #####################################

class AbstractComm(threading.Thread):
    """
    An abstract class that handles communication with other
    processes and threads
    """
    def __init__(self, parent, port):
        threading.Thread.__init__(self)
        self.parent = parent
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('localhost', port))
        self.setDaemon(1)
        self.socket.settimeout(20)
        self.running = 1
       
    def run(self):
        while self.running==1:
            try:
                buffer, addr = self.socket.recvfrom(1024)
            except socket.timeout:
                continue
            except Exception:
                continue
            t = threading.Thread(target = self.handle, args = (buffer, addr))
            t.start()
        self.socket.close()

    def handle(self, buffer, args):
        raise NotImplementedError("AbstractComm handle not implemented")

    def shutdown(self):
        self.running = 0


#TODO: Convert both of these to use XML-RPC instead of our own random protocol

class CommandComm(AbstractComm):
    """
    Handles mapping and device registration requests
    """
    def handle(self, buffer, addr):
        request = minidom.parseString(buffer).firstChild
        
        if request.tagName == 'request':

            # Device Registration requests
            if request.getAttribute('type') == 'register':
                print "CommandComm: Device registration request received"
                msg = {'type':'register', 'request':request, 'addr':addr }
                self.parent.dataqueue.put(msg)

            # Mapping Requests
            elif request.getAttribute('type') == 'mapping':
                print "CommandComm: Mapping request received"
                msg = {'type':'mapping', 'request':request}
                self.parent.dataqueue.put(msg)

            else:
                print "CommandComm: Unrecognized request type!"


class DataComm(AbstractComm):
    """
    Handles data to and from drivers
    """
    def handle(self, buffer, addr):
        #print "DataComm: received a message from port %u" % (addr[1])
        request = minidom.parseString(buffer).firstChild

        # New data from device
        if request.tagName == 'request' and request.getAttribute('type') == 'data':
            print "DataComm: new data received"

            # Separate the request into several devices, if applicable
            for device in request.getElementsByTagName('enddevice'):
                print "-->data from device %d" % (int(device.getAttribute('device_id')))
                msg = {'type':'data', 'device':device}
                self.parent.dataqueue.put(msg)
        else:
            print "DataComm: Unrecognized request type!"




if __name__ == '__main__':
    import os
    pid = os.fork()
    if pid == 0:
        # This is the forked-off process
        mapper = Mapper()
        # Shut down the mapper properly if we receive a TERM signal
        signal.signal(signal.SIGTERM, mapper.shutdown)
        mapper.run()
    else:
    	print "Mapping daemon started"

    







