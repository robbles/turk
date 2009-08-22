#!/usr/bin/python
""""
The driver-spawner creates a new instance of a driver for each device,
by looking it up in a sqlite database. The turk server is queried for 
unknown IDs, which are then added to the database
"""
#TODO: Implement proper management of driver processes
# i.e. keep a table of started drivers pids, shut down old ones as they're replaced

import socket
import os
import struct
import time
from sqlite3 import dbapi2 as sqlite
import signal
import urllib2
from xml.dom.minidom import parseString
import string
import subprocess

TURK_CLOUD_DRIVER_INFO = string.Template('http://drivers.turkinnovations.com/drivers/${driver_id}.xml')
TURK_CLOUD_DRIVER_STORAGE = string.Template('http://drivers.turkinnovations.com/files/drivers/${filename}')

def test(device_id, startspawner=0, port=45000):
    if startspawner == 1:
        sp = DriverSpawner()
        sp.start()
    else:
        sp = 0
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    msg = struct.pack('>QQ', 0x0013A2004052DA9A, device_id)
    s.sendto(msg, ('localhost', port))
    s.close()
    if sp:
        sp.shutdown()


class DriverSpawner():
    def __init__(self, port=45000):
        self.s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print "Using port %d" % port
        self.s.bind(('', port))
        self.s.settimeout(3)
        self.running = 1
        self.driver_list = []

    def run(self):
        self.db = sqlite.connect('drivers.db')
        while self.running==1:
            try:
                buffer, ipaddr = self.s.recvfrom(1024)
            except socket.timeout:
                continue
            except Exception, err:
                print err
                print "Spawner: warning - error reading from socket"
                continue
            device_addr, device_id = struct.unpack('>QQ', buffer[0:16])
            print "Spawner: received a driver request from xbee 0x%X with device_id %u, from %s" % (device_addr, device_id, ipaddr) 

            # Get the driver's path from the db
            results = self.fetch_path(device_id)
            
            #TODO: need to test whether driver should be spawned multiple times,
            # or notified to respawn itself instead, or managed by spawner

            if results != None:
                try:
                    drivername, driverargs = results[2], results[3]
                    print "starting driver %s" % drivername
                    args = ['./' + drivername, str(device_id), "0x%X" % device_addr]
                    args.extend(driverargs.split())
                    self.driver_list.append(subprocess.Popen(args, stdout=sys.stdout))
                except Exception, e:
                    print 'failed starting driver: %s' % e

        # Shutdown was called, close all drivers and sockets
        print "Spawner: Shutting down..."
        for driver in self.driver_list:
            driver.terminate()
        self.s.close()
        self.db.close()
        print

    def shutdown(self, signum, frame):
        print 'received shutdown request'
        self.running = 0

    def fetch_path(self, device_id):
        try:
            results = self.db.execute('select * from drivers where device_id = ? limit 1', (device_id,)).fetchall()
            if results:
                return results[0]
            else:
                print "Spawner: no driver found for %s, trying to GET from server" % (device_id)
                return self.fetch_driver(device_id)
        except Exception, e:
            print "Failed getting driver"
            print e
            return None

    #TODO: check for 404s and 500s and do something about it
    # and also 418s - the driver may be a teapot
    def fetch_driver(self, device_id):
        try:
            # Just assume driver_id == device_id for now
            driver_id = device_id
            addr = TURK_CLOUD_DRIVER_INFO.substitute(driver_id=driver_id)
            driver_info = parseString(urllib2.urlopen(addr).read())
            driver = driver_info.getElementsByTagName('driver')[0] 
            filename = driver.getAttribute('file')
            title = driver.getAttribute('title')
            if driver.hasAttribute('argument'):
                args = driver.getAttribute('argument')
            else:
                args = ''
            print "fetched driver info, driver's name is %s" % title
            print "fetching: " + TURK_CLOUD_DRIVER_STORAGE.substitute(filename=filename)
            try:
                driverdata = urllib2.urlopen(TURK_CLOUD_DRIVER_STORAGE.substitute(filename=filename))
                driverfile = open(filename, 'w')
                driverfile.write(driverdata.read())
                driverfile.close()
            except urllib2.HTTPError, err:
                print "Couldn't fetch driver resource - HTTP error %d" % err.getcode()
                return None
            self.db.execute('insert into drivers (device_id, driver_id, location, arguments) values (?, ?, ?, ?)',
                            (int(device_id), int(driver_id), filename, args))
            self.db.commit()
            print "saved driver data successfully"
            return [device_id, driver_id, filename, args]
        except Exception, err:
            print err
        




# Run standalone

if __name__ == '__main__':
    import sys
    import os
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 45000

    pid = os.fork()
    if pid == 0:
        sp = DriverSpawner(port)
        signal.signal(signal.SIGTERM, sp.shutdown)
        sp.run()
        print 'spawner daemon finished'
    else:
        print "Spawner daemon started"


