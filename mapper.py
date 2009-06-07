#! /usr/bin/python

import socket
import Queue
import time
from xml.dom import minidom
from pysqlite2 import dbapi2 as sqlite
import threading


###################### Mapper Classes ##########################################

#TODO: Make this NOT a thread once fully working
# Fork into background instead..?
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
        print "Mapper: adding device id:%s, name:%s" % (device_id, name)
        if self.sql_exists('devices', 'device_id', device_id):
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
        print 'device_id: ', device_id

        # Try to use any old mappings that haven't been applied yet
        self.apply_mappings()

    def apply_mappings(self):
        maplist=[mapping for mapping in self.old_mappings if((mapping[0] in self.devices) and (mapping[2] in self.devices))]
        for mapping in maplist:
                print "Applying mapping: %s:%s -> %s:%s" % (mapping[0], mapping[1], mapping[2], mapping[3])
                self.attach(mapping[0], mapping[1], mapping[2], mapping[3])
                #self.old_mappings.remove(mapping)


    # Helper method that checks for rows matching one/two conditions,
    # and return them, or an empty list otherwise
    def sql_exists(self, table, main_column, main_value, sec_column=0, sec_value=0):
        if sec_column == 0 :
            results = self.db.execute('select * from %s where %s=\'%s\'' % (table, main_column, main_value)).fetchall()
        else:
            results = self.db.execute('select * from %s where %s=\'%s\' and %s=\'%s\'' % (db, main_column, main_value, sec_column, sec_value)).fetchall()
        return results


    # Attaches an output to an input source. Doesn't affect database, just implements a mapping
    def attach(self, output_device, output_name, input_device, input_name):
        print "Mapper: trying to attach %s.%s to %s.%s" % (output_device, output_name, input_device, input_name)
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
        print "Mapper: trying to associate %s.%s with %s.%s" % (output_device, output_name, input_device, input_name)
        # Silently delete any old mappings for this output, then add it
        # TODO: Should similar mappings be deleted? or just overridden later?
        self.db.execute('delete from mappings where output_device=\'%s\' and output_name=\'%s\'' % (output_device, output_name))
        self.db.execute('insert into mappings values(\'%s\', \'%s\', \'%s\', \'%s\')' % (output_device, output_name, input_device, input_name))
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
            #print "-->waiting for commands/data"
            message = self.dataqueue.get()

            # New data from a device
            if message['type'] == "data":
                device = message['device']
                id = device.getAttribute('device_id')
                for input in device.getElementsByTagName('input'):
                    try:
                        name = input.getAttribute('name')
                        data = input.getAttribute('data')
                        self.devices[id].inputs[name].notify_outputs(data)
                    except Exception:
                        print "Error accessing data from message or device/input"

            # Shut down the entire mapping system
            elif message['type'] == 'shutdown':
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
                    device_id = enddevice.getAttribute('device_id')
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
                    input_data = (input.getAttribute('device_id'), input.getAttribute('name'))
                    print "found input: name %s" % input_data[0]
                    # Get all the outputs to be mapped to it
                    outputs = mapping.getElementsByTagName('output')
                    for output in outputs:
                        output_data = (output.getAttribute('device_id'), output.getAttribute('name'))
                        print "found output: name %s" % output_data[0]
                        self.associate(output_device=output_data[0],
                                              output_name=output_data[1],
                                              input_device=input_data[0],
                                              input_name=input_data[1])
                

    def shutdown(self):
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
                print "-->data from device %s" % (device.getAttribute('device_id'))
                msg = {'type':'data', 'device':device}
                self.parent.dataqueue.put(msg)
        else:
            print "DataComm: Unrecognized request type!"






if __name__ == '__main__':
    import os
    pid = os.fork()
    if pid == 0:
        mapper = Mapper()
        mapper.run()
    else:
    	print "Mapping daemon started"

    







