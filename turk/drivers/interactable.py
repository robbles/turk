#! /usr/bin/python
import gobject
import dbus
import dbus.service
import dbus.mainloop.glib
from xml.dom.minidom import parseString, Document
import tuio
import turk

DRIVER_ID = 9

"""
### Sample configs ###

# Sets the update time (driver -> server) to every 5 seconds
<config type="update_time">5</config>

"""

TURK_DRIVER_ERROR = "org.turkinnovations.drivers.Error"
TURK_BRIDGE = "org.turkinnovations.turk.Bridge"

UPDATE_TIME = 1000

class InteracTable(dbus.service.Object):
    def __init__(self, device_id, port, bus):

        dbus.service.Object.__init__(self, bus,
                                     '/Drivers/InteracTable/%d' % port)
        self.device_id = device_id
        self.bus = bus

        listen = '/Bridge/ConfigFiles/Drivers/%d' % (self.device_id)
        self.bus.add_signal_receiver(self.new_config, path=listen)
        print 'interacTable: listening for %s' % listen

        self.tracking = tuio.Tracking(host='', port=port)
        self.markers = {}

        gobject.timeout_add(UPDATE_TIME, self.update)
        gobject.io_add_watch(self.tracking.socket.fileno(), gobject.IO_IN, self.track)

    def track(self, fd, condition):
        try:
            self.tracking.update()
            #print [obj.id for obj in self.tracking.objects()]

            for obj in self.tracking.objects():
                if obj.id not in self.markers:
                    self.markers[obj.id] = obj

        finally:
            return True
    

    def update(self):
        try:
            print 'updating server with current markers:', self.markers.keys()
            
            doc = Document()
            table = doc.appendChild(doc.createElement(u'table'))
            table.setAttribute(u'id', unicode(self.device_id))

            for id in self.markers.keys():
                marker = table.appendChild(doc.createElement(u'marker'))
                marker.setAttribute(u'id', unicode(id))
                marker.setAttribute(u'angle', unicode(self.markers[marker].angle))
                marker.setAttribute(u'xpos', unicode(self.markers[marker].xpos))
                marker.setAttribute(u'ypos', unicode(self.markers[marker].ypos))
            try:
                bridge = self.bus.get_object(turk.TURK_BRIDGE_SERVICE, '/Bridge')
                bridge.PublishUpdate('app', doc.toxml(), unicode(DRIVER_ID),
                        reply_handler=lambda *args: None, error_handler=self.handle_error)
            except dbus.DBusException, e:
                print 'interacTable: error posting data to app', e

            # Remove all markers from list
            self.markers.clear()

        except Exception, e:
            print e
        finally:
            return True


    def handle_error(self, ex):
        print 'interacTable: error posting data to app', ex


    def new_config(self, driver, xml):
        print 'new xml config received:'
        print xml
        try:
            tree = parseString(xml)

            config = tree.getElementsByTagName('config')[0]
            ctype = config.getAttribute('type') 

            if ctype == 'update_time':
                # Parse time value
                self.update_time = int(config.childNodes[0].nodeValue)

        except Exception, e:
            # emit an error signal for bridge
            self.Error(e.message)
            print e
        
    def run(self):
        loop = gobject.MainLoop()
        loop.run()

    @dbus.service.signal(dbus_interface=TURK_DRIVER_ERROR, signature='s') 
    def Error(self, message):
        """ Called when an error/exception occurs. Emits a signal for any relevant
            system management daemons and loggers """
        pass
        

# Run as a standalone driver
if __name__ == '__main__':
    import os
    try:
        device_id = int(os.getenv('DEVICE_ID'))
    except:
        print 'interacTable: error - DEVICE_ID is not set'
        exit(-1)

    bus = os.getenv('BUS', turk.get_config('global.bus'))

    print "interacTable driver started... driver id: %u" % device_id
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    driver = InteracTable(device_id, 3333, getattr(dbus, bus)())
    driver.run()

    

