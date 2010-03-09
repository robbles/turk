#! /usr/bin/python
import gobject
import dbus
import dbus.service
import dbus.mainloop.glib
import turk
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

class TwitterFeed(dbus.service.Object):
    def __init__(self, app_id, bus):
        dbus.service.Object.__init__(self, bus, '/Workers/TwitterFeed/%d' % app_id)
        self.app_id = app_id
        self.bus = bus

        self.last_id = 0
        self.timeline = 'global'

        self.api = twitter.Api()

        listen = '/Bridge/ConfigFiles/Workers/%d/%d' % (self.app_id, DRIVER_ID)
        self.bus.add_signal_receiver(self.new_config, path=listen)

        gobject.timeout_add(SLEEP_TIME, self.poll_server)

        print 'TwitterFeed: listening for %s' % listen


    def poll_server(self):
        try:
            if self.timeline == 'user':
                statuses = self.api.GetUserTimeline(count=1, since_id=self.last_id)
                if statuses:
                    self.new_data(statuses[0].text)
                    self.last_id = statuses[0].id
                else:
                    print 'TwitterFeed: status is still the same'
            else:
                statuses = self.api.GetPublicTimeline(since_id=self.last_id)
                if statuses:
                    print 'TwitterFeed: found new public status'
                    self.new_data(statuses[0].text)
                    self.last_id = statuses[0].id
                else:
                    print 'TwitterFeed: no new statuses'
        except Exception, e:
            print 'TwitterFeed: error fetching status', e
        finally:
            return True

    def handle_reply(self, *args):
        #print 'TwitterFeed: received %s back from DBus method call' % (args,)
        pass

    def handle_error(self, ex):
        print 'TwitterFeed: error posting data to app', ex

    def new_data(self, status):
        # FIXME : occasional unicode-related errors...?
        print 'TwitterFeed: status updated'

        # Use bridge to update app
        try:
            print 'TwitterFeed: converting status to unicode'
            ustatus = unicode(status)

            print 'TwitterFeed: sending status to app'
            bridge = self.bus.get_object(turk.TURK_BRIDGE_SERVICE, '/Bridge')
            bridge.PublishUpdate('app', ustatus, unicode(DRIVER_ID),
                    reply_handler=self.handle_reply, error_handler=self.handle_error)
        except dbus.DBusException, e:
            print 'TwitterFeed: error posting data to app', e
        except Exception, e:
            print 'TwitterFeed: error converting data', e

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

    @dbus.service.signal(dbus_interface=turk.TURK_DRIVER_ERROR, signature='s') 
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

    bus = os.getenv('BUS', turk.get_config('global.bus'))

    print "TwitterFeed driver started... app id: %u" % (app_id)
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    driver = TwitterFeed(app_id, getattr(dbus, bus)())
    driver.run()

    

