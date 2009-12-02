#! /usr/bin/python
import gobject
import dbus
import dbus.service
import dbus.mainloop.glib
from xml.dom.minidom import parseString
import twitter

DRIVER_ID = 7

"""
Max number of requests per hour, and calculated sleep time in milliseconds
"""
TWITTER_MAX_REQUESTS = 100.0
SLEEP_TIME = 3600.0 / TWITTER_MAX_REQUESTS * 1000
print SLEEP_TIME

"""
### Sample config ###

'<?xml version="1.0" encoding="UTF-8"?>
<timeline type="user">
    <user name="turkbot" password="turkinnovations" />
</timeline>'

'<?xml version="1.0" encoding="UTF-8"?>
<timeline type="global">
</timeline>'

"""

TURK_DRIVER_ERROR = "org.turkinnovations.drivers.Error"
TURK_BRIDGE = "org.turkinnovations.core.Bridge"

class TwitterFetcher(dbus.service.Object):
    def __init__(self, device_id):
        dbus.service.Object.__init__(self, dbus.SessionBus(), '/Drivers/Twitter_Fetcher/%d' % device_id)
        self.device_id = device_id
        self.bus = dbus.SystemBus()

        self.last_id = 0
        self.timeline = 'global'

        self.api = twitter.Api()

        self.bus.add_signal_receiver(self.new_config, path='/ConfigData/%d' % (DRIVER_ID))

        gobject.timeout_add(SLEEP_TIME, self.poll_server)

        print 'TwitterFetcher: listening for %s' % ('/ConfigData/%d' % (DRIVER_ID))


    def poll_server(self):
        if self.timeline == 'user':
            statuses = self.api.GetUserTimeline(count=1, since_id=self.last_id)
            if statuses:
                self.new_data(statuses[0].text)
                self.last_id = statuses[0].id
        else:
            statuses = self.api.GetPublicTimeline(since_id=self.last_id)
            if statuses:
                self.new_data(statuses[0].text)
                self.last_id = statuses[0].id
        return True

    def new_data(self, status):
        print 'TwitterFetcher: status is now "%s"' % (status)

    def new_config(self, xml):
        print 'new xml config received: %s' % xml
        tree = parseString(xml)
        try:
            timeline = tree.getElementsByTagName('timeline')[0].firstChild.nodeValue
            type = timeline.getAttribute('type')
            if type in ['user', '']:
                user = timeline.getElementsByTagName('user')
                name, password = (user.attributes['name'].nodeValue, 
                                  user.attributes['password'].nodeValue)
                self.SetCredentials(name, password)
                self.timeline = 'user'
            elif type == 'global':
                self.timeline = 'global'
            else:
                # TODO: emit an error signal for bridge
                print 'TwitterFetcher: unknown timeline type'

        except Exception, e:
            # TODO: emit an error signal for bridge
            self.error('TwitterFetcher: ' + str(e))
            print e
        
    def run(self):
        loop = gobject.MainLoop()
        loop.run()

    @dbus.service.signal(dbus_interface=TURK_DRIVER_ERROR, signature='s') 
    def error(self, message):
        """ Called when an error/exception occurs. Emits a signal for any relevant
            system management daemons and loggers """
        pass
        

# Run as a standalone driver
if __name__ == '__main__':
    import os
    try:
        device_id = int(os.getenv('DEVICE_ID'))
    except Exception:
        #TODO: find better way of returning error (dbus?)
        print 'TwitterFetcher: error parsing environment variables'
        exit(1)

    print "TwitterFetcher driver started... device id: %u" % (device_id)
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    driver = TwitterFetcher(device_id)
    driver.run()

    

