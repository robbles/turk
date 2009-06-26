#!/usr/bin/python
""""
The driver-spawner creates a new instance of a driver for each device,
by looking it up in a sqlite database. The turk server is queried for 
unknown IDs, which are then added to the database
"""

#from pysqlite2 import dbapi2 as sqlite
import socket
import os
import struct
import time
from pysqlite2 import dbapi2 as sql


def test(startspawner=0, port=45000):
    #                         Zigbee Address       Turk Device ID
    if startspawner == 1:
        sp = DriverSpawner()
        sp.start()
    else:
        sp = 0
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    msg = struct.pack('>QQQ', 0, 0x0013A2004052DA9A, 1)
    s.sendto(msg, ('localhost', port))
    s.close()
    if sp:
        sp.shutdown()


class DriverSpawner():
    def __init__(self, port=45000):
        self.s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.bind(('', port))
        self.s.settimeout(3)
        self.running = 1

    def run(self):
        self.db = sql.connect('drivers.db')
        while self.running==1:
            try:
                buffer, ipaddr = self.s.recvfrom(1024)
            except socket.timeout:
                continue
            device_addr, device_id = struct.unpack('>QQ', buffer[0:16])
            print "Spawner: received a driver request from xbee 0x%X, device_id is %u" % (device_addr, device_id) 

            # Get the driver's path from the db
            results = self.fetch_path(device_id)
            
            #TODO: need to test whether driver should be spawned multiple times,
            # or notified to respawn itself instead

            if results != None:
                drivername, driverargs = results[2], results[3]
                args = [drivername, str(device_id), "0x%X" % device_addr]
                if driverargs != '':
                    args.extend(driverargs.split(' '))
                os.spawnv(os.P_NOWAIT, str(results[2]), args)

        # Shutdown was called, close the socket
        print "Spawner: Shutting down..."
        self.s.close()
        self.db.close()

    def shutdown(self):
        self.running = 0

    def fetch_path(self, device_id):
        results = self.db.execute('select * from drivers where device_id = %d limit 1' % (device_id)).fetchall()
        if results:
            return results[0]
        else:
            print "Spawner: no driver found for %s" % (device_id)
            # TODO: fetch the driver from the Turk servers
            return None



# Run standalone

if __name__ == '__main__':
    import sys
    import os
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 45000

    if os.fork() == 0:
        sp = DriverSpawner(port)
        sp.run()
    else:
        print "Spawner daemon started"


