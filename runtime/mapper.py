#! /usr/bin/python

import socket
from sqlite3 import dbapi2 as sqlite
import signal
import SimpleXMLRPCServer
import xmlrpclib
import sys

MAPPER_PORT = 44000


###################### Mapper Classes ##########################################

# Important note: device/driver/application ID's  are INTEGERS,
# driver/application names are STRINGS
# don't mix them up, or angry digital unicorns will eat your computer

class Mapper(object):
    """
    Keeps track of all devices, and handles routing between drivers and applications
    All of the mapping and device info is kept in a SQLite database, which is managed by this class. 
    Data in mappings is restored on restart of the platform. This may change in future.
    
    All database and mapping functionality is exposed through XML-RPC
    """
    def __init__(self, port=MAPPER_PORT, runtime_db='runtime.db'):
        self.drivers = {}
        self.apps = {}

        # fun with XML-RPC :D
        self.server = SimpleXMLRPCServer.SimpleXMLRPCServer(addr=('', port), allow_none=True)
        self.server_port = port
        self.server.register_function(self.register_driver, 'register_driver')
        self.server.register_function(self.register_app, 'register_app')
        self.server.register_function(self.route_to_driver, 'route_to_driver')
        self.server.register_function(self.route_to_app, 'route_to_app')
        self.server.register_introspection_functions()

        # Socket for UDP communications
        self.outsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def sendto(self, msg, addr):
        """ A wrapper for the mapper's socket sendto() method, in case we need to change it """
        self.outsocket.sendto(msg, addr)
        print 'Mapper: sent \'%s\' to %s' % (msg, addr)

    def register_driver(self, device_id, driver_id, driver_name, driver_info, driver_addr):
        """
        Drivers register themselves through the XML-RPC interface,
        providing a device_id and name, and a structure providing additional info/options
        """
        # TODO: Automatically get address from server request if not specified
        self.drivers[device_id] = Driver(device_id, driver_id, driver_name, driver_addr, self)
        self.db.execute('insert into devices values(?, ?, ?, ?)', (device_id, driver_id, driver_name, driver_info))

    def register_app(self, app_id, app_name, device_ids, app_addr):
        """
        Applications register themselves through the XML-RPC interface,
        providing an app_id and name, and a list of device id's they need 
        """
        # TODO: Automatically get address from server request if not specified
        drivers = [self.drivers[device_id] for device_id in device_ids]
        self.apps[app_id] = Application(app_id, app_name, drivers, app_addr, self)

    def route_to_driver(self, device_id, data):
        """ An application sending a message to it's driver """
        driver = self.drivers[device_id]
        self.sendto(driver.format_message(data), driver.addr)

    def route_to_app(self, device_id, data):
        """ A driver sending a message to it's application """
        app = self.drivers[device_id].app
        self.sendto(app.format_message(data), app.addr)


    # Main Loop
    def run(self):
        # Start database connection - can only be accessed in this thread!
        self.db = sqlite.connect('runtime.db')
        self.db.execute('create table if not exists mappings(device_id int, driver_id int, app_id int, driver_name text, app_name text)')
        self.db.execute('create table if not exists devices(device_id int, driver_id int, driver_name text, driver_info text)')

        # Delete any remaining devices from failed shutdown
        self.db.execute('delete from devices')
        self.db.commit()

        print 'Mapper: starting XML-RPC server on port %d' % self.server_port
        try:
            while 1:
                self.server.serve_forever()
        except Exception, e:
            print e
        except KeyboardInterrupt:
            print 'mapper keyboard int'

        

    def shutdown(self, *args):
        print "Mapper: interrupted, shutting down..."
        self.db.execute('delete from devices')
        self.db.commit()
        self.db.close()
        sys.exit(0)
        


###################### Driver and Applications ################################

class Driver:
    def __init__(self, device_id, driver_id, name, addr, mapper):
        self.device_id = device_id
        self.driver_id = driver_id
        self.name = name
        self.addr = addr
        self.mapper = mapper
        self.app = None

    def connect_to_app(self, app):
        self.app = app

    def format_message(self, data):
        return xmlrpclib.dumps((data,), methodname='app_data')

class Application:
    def __init__(self, app_id, name, devices, addr, mapper):
        self.app_id = app_id
        self.name = name
        self.devices = devices
        self.addr = addr
        self.mapper = mapper

        for device in devices:
            device.connect_to_app(self)

    def format_message(self, data):
        return xmlrpclib.dumps((data,), methodname='device_data')


###################### Main ###################################################

def run(daemon=False):
    """
    Start Mapper as a standalone process.
    if daemon = True, forks into the background first
    """
    if daemon:
        import os
        pid = os.fork()
        if pid:
            return pid
    mapper = Mapper()
    # Shut down the mapper properly if we receive a TERM signal
    signal.signal(signal.SIGTERM, mapper.shutdown)
    mapper.run()

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == '--daemon':
        run(True)
    else:
        run(False)






