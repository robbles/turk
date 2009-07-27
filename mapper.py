#! /usr/bin/python

import socket
import Queue
import time
from xml.dom import minidom
from sqlite3 import dbapi2 as sqlite
import threading
import signal
import SimpleXMLRPCServer


###################### Mapper Classes ##########################################

# Important note: device ID's (output_device, input_device) are INTEGERS,
# input/output names (output_name, input_name) are STRINGS
# DON'T mix them up, or angry digital unicorns will eat your computer

# TODO make bridge do all it's sqlite changes through the mapper
class Mapper():
    """
    Keeps track of all devices, and handles mapping
    of DeviceOutputs and DeviceInputs.
    All of the mapping and device info is kept in a SQLite database, which is managed by this class. 
    Data in mappings is restored on restart of the platform, but not devices. This may change in future.
    
    All database and mapping functionality is exposed through XML-RPC
    """
    def __init__(self, port=44000):
        self.devices = {}
        self.dataqueue = Queue.Queue(50)
        # fun with XML-RPC :D
        self.server = SimpleXMLRPCServer.SimpleXMLRPCServer(addr=('localhost', port), allow_none=True)
        self.server.register_function(self.register_device, 'register_device')
        self.server.register_function(self.make_mapping, 'make_mapping')
        self.server.register_function(self.route_data, 'route_data')
        self.server.register_introspection_functions()

    # interfaces is an xml dom node, not a string
    def register_device(self, device_id, name, description, addr):
        print "Mapper: adding device id:%d, name:%s" % (device_id, name)
        if (self.db.execute('select * from devices where device_id=?', (device_id,)).fetchall()):
            print "Mapper: WARNING - device already registered - removing old device..."
            # Remove the old device
            self.db.execute('delete from devices where device_id=?', (device_id,))
            self.db.commit()

        new_device = EndDevice(name, addr, self)
        inter_xml = minidom.parseString(description)
        inputs = inter_xml.getElementsByTagName('input')
        outputs = inter_xml.getElementsByTagName('output')
        for input in inputs:
            new_device.add_input(input.getAttribute('name'), input.getAttribute('protocol'))
        for output in outputs:
            new_device.add_output(output.getAttribute('name'), output.getAttribute('protocol'))
        # Add to the database while Mapper is running
        self.db.execute('insert into devices values (?, ?, ?)', (device_id, name, description))
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


    # Attaches an output to an input source. Doesn't affect database, just implements a virtual mapping
    def attach(self, input_device, input_name, output_device, output_name):
        print "Mapper: trying to attach %d.%s to %d.%s" % (input_device, input_name, output_device, output_name)
        try:
            output = self.devices[output_device].outputs[output_name]
            input = self.devices[input_device].inputs[input_name]
            input.register(output)

        except KeyError:
            print "Error while trying to map inputs/outputs - perhaps they only exist in your head?"
            print "Input devices's inputs:", self.devices[input_device].inputs
            print "Output device's outputs:", self.devices[output_device].outputs
            return
        print "Mapper: mapping implemented - %d.%s is now the only source of data for %d.%s" % (input_device, input_name, output_device, output_name)
        

    # Creates a new mapping between two devices (input to output), then attaches them
    def make_mapping(self, input_device, input_name, output_device, output_name):
        print "Mapper: trying to associate output %d.%s with input %d.%s" % (output_device, output_name, input_device, input_name)
        # Silently delete any old mappings for this output, then add it
        self.db.execute('delete from mappings where output_device=? and output_name=?', (output_device, output_name))
        self.db.execute('insert into mappings (input_device,input_name,output_device,output_name) values(?, ?, ?, ?)', (input_device, input_name, output_device, output_name))
        self.db.commit()
        self.attach(output_device, output_name, input_device, input_name)


    # TODO: route new data from inputs to their registered outputs
    def route_data(self, device_id, input_data):
        if device_id in self.devices:
            for input_name in input_data.keys():
                if input_name in self.devices[device_id].inputs:
                    self.devices[device_id].inputs[input_name].notify_outputs(input_data[input_name])
                    print "routed data from %s.%s successfully!" % (device_id, input_name)
                else:
                    print "%s not in list of inputs for device %s" % (input_name, device_id)
                    return
        else:
            print "device %s is unknown" % (device_id)
            return
        print "done routing"


    # Main Loop
    def run(self):
        # Start database connection - can only be accessed in this thread!
        self.db = sqlite.connect('mappings.db')

        # Delete any remaining devices from failed shutdown
        self.db.execute('delete from devices')
        self.db.commit()

        # Get all the old mappings, and try to use them later as devices are registered
        self.old_mappings = self.db.execute('select input_device,input_name,output_device,output_name from mappings').fetchall()
        print 'old_mappings: ', self.old_mappings

        self.server.serve_forever()
        

    def shutdown(self, signum, data):
        print "Mapper: received a shutdown request"
        print [signame for signame in signal.__dict__.keys() if signal.__dict__[signame] == signum][0]
        #self.db.execute('delete from devices')
        self.db.commit()
        self.db.close()


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

    







