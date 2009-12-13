#! /usr/bin/python
import gobject
import dbus
import dbus.service
import dbus.mainloop.glib
from xml.dom.minidom import parseString
import twitter

DRIVER_ID = 7

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

# Max number of requests per hour, and calculated sleep time in milliseconds
TWITTER_MAX_REQUESTS = 100.0
SLEEP_TIME = int(3600.0 / TWITTER_MAX_REQUESTS * 1000)

TURK_DRIVER_ERROR = "org.turkinnovations.drivers.Error"
TURK_BRIDGE = "org.turkinnovations.core.Bridge"

class TwitterFeed(dbus.service.Object):
    def __init__(self, app_id):
        dbus.service.Object.__init__(self, dbus.SystemBus(), '/Workers/TwitterFeed/%d' % app_id)
        self.app_id = app_id
        self.bus = dbus.SystemBus()

        self.last_id = 0
        self.timeline = 'global'

        self.api = twitter.Api()

        self.bus.add_signal_receiver(self.new_config, path='/Bridge/ConfigFiles/%d' % self.app_id)

        gobject.timeout_add(SLEEP_TIME, self.poll_server)

        print 'TwitterFeed: listening for %s' % ('/Bridge/ConfigFiles/%d' % self.app_id)


    def poll_server(self):
        try:
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
        finally:
            return True

    def new_data(self, status):
        # FIXME : occasional unicode-related errors...?
        print u'TwitterFeed: status is now "%s"' % (status)

    def new_config(self, driver, xml):
        print 'new xml config received: %s' % xml
        tree = parseString(xml)
        try:
            timeline = tree.getElementsByTagName('timeline')[0]
            type = timeline.getAttribute('type')
            if type in ['user', '']:
                user = timeline.getElementsByTagName('user')[0]
                name, password = (user.attributes['name'].nodeValue, 
                                  user.attributes['password'].nodeValue)
                self.api.SetCredentials(name, password)
                self.timeline = 'user'
            elif type == 'global':
                self.timeline = 'global'
            else:
                # TODO: emit an error signal for bridge
                print 'TwitterFeed: unknown timeline type'

        except Exception, e:
            # TODO: emit an error signal for bridge
            self.error('TwitterFeed: ' + str(e))
            print e
        
    def run(self):
        loop = gobject.MainLoop()
        loop.run()

    @dbus.service.signal(dbus_interface=TURK_DRIVER_ERROR, signature='s') 
    def error(self, message):
        """ Called when an error/exception occurs. Emits a signal for any relevant
            system management daemons and loggers """
        print message
        

# Run as a standalone driver
if __name__ == '__main__':
    import os
    try:
        app_id = int(os.getenv('APP_ID'))
    except Exception:
        #TODO: find better way of returning error (dbus?)
        print 'TwitterFeed: error parsing environment variables'
        exit(1)

    print "TwitterFeed driver started... app id: %u" % (app_id)
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    driver = TwitterFeed(app_id)
    driver.run()

    

