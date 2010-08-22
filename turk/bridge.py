#! /usr/bin/env python

import dbus
import dbus.service
import dbus.mainloop.glib
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
import yaml
import os
import turk
from turk import get_config
import urllib, urllib2
import logging

from twisted.internet import glib2reactor
glib2reactor.install()

import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from twisted.words.protocols.jabber import client, jstrports
    from twisted.words.protocols.jabber.jid import JID
    from twisted.words.protocols.jabber import xmlstream
    from twisted.words.xish.domish import Element
    from twisted.words.xish import xpath
    from twisted.application.internet import TCPClient
    from twisted.internet import reactor
    from wokkel.xmppim import PresenceClientProtocol, RosterClientProtocol

log = logging.getLogger('bridge')

class Bridge(dbus.service.Object):
    """
    Manages the interface between the Turk Cloud and this platform using a
    combination of HTTP (for driver->app updates) and XMPP (for app->driver messages).
    Listens for relevant D-BUS signals and logs them to the XMPP server.
    """
    def __init__(self, server, port, jid, password, bus):
        # Setup D-BUS service and signal callbacks
        bus_name = dbus.service.BusName(turk.TURK_BRIDGE_SERVICE, bus)
        self.bus = bus
        dbus.service.Object.__init__(self, bus_name, '/Bridge')

        # Setup XMPP client 
        factory = client.XMPPClientFactory(jid, password)
        self.manager = xmlstream.StreamManager(factory)
        self.handler = BridgeXMPPHandler(self, self.manager)
        self.manager.addHandler(self.handler)
        client_svc = TCPClient(server, port, factory)
        client_svc.startService()

        # Setup driver registry
        self.drivers = {}

        # Init driver subscriptions
        self.subscriptions = {}

        log.debug('started')


    @dbus.service.method(dbus_interface=turk.TURK_BRIDGE_INTERFACE,
                         in_signature='t', out_signature='')
    def RegisterDriver(self, driver_id):
        """
        Registers a driver ID with the bridge, so that it can receive updates.
        """
        if driver_id not in self.drivers:
            log.debug('registering driver %d' % driver_id)
            self.drivers[driver_id] = Driver(self.bus, driver_id)
        else:
            log.debug('driver %d already registered' % driver_id)


    @dbus.service.method(dbus_interface=turk.TURK_BRIDGE_INTERFACE,
                         in_signature='sss', out_signature='')
    def PublishUpdate(self, type, update, driver):
        """
        Publishes a new update via HTTP to all apps that have registered to
        this data driver
        """
        log.debug('publishing update from %s - ' % (driver))

        driver = int(driver)

        log.debug('subscriptions: %s'% self.subscriptions)
        if driver in self.subscriptions:
            for app in self.subscriptions[driver]:
                try:
                    # build app URL
                    url = self.subscriptions[driver][app]
                    log.debug('POSTing to url %s' % url)
                    # encode params
                    request = urllib2.Request(url, update)
                    # POST request
                    response = urllib2.urlopen(request, timeout=1)
                    page = response.read(100)

                    log.debug('successfully updated app %d' % (app) )
                    log.debug(page)

                except urllib2.HTTPError, e:
                    log.debug('PublishUpdate: HTTP error %d' % e.getcode())
                except Exception, e:
                    log.debug('PublishUpdate: %s'% e)
                    
    def SignalUpdate(self, driver, app, update):
        """ Sends a signal to indicate an update for a driver has been received.  """
        if driver not in self.drivers:
            self.drivers[driver] = Driver(self.bus, driver)

        self.drivers[driver].Update(driver, app, update)

    
    def registerObserver(self, driver, app, url):
        """
        Registers app to be notified of events coming from driver.
        All updates will be POSTed to url with HTTP
        """
        log.debug('registerObserver: driver:%s app:%s url:%s' % (driver, app, url))
        if driver in self.subscriptions:
            if app not in self.subscriptions[driver]:
                self.subscriptions[driver][app] = url
                log.debug('Added subscription to driver %s for app %s' % (driver, app))
            else:
                log.debug('App %d is already subscribed to driver %d' % (app, driver))
        else:
            self.subscriptions[driver] = {app : url}
            log.debug('Added subscription to driver %s for app %s' % (driver, app))

    
    def requireService(self, driver, app):
        """
        Notifies Spawner that driver needs to be started or already running.
        Forwards any error notifications to the server through XMPP
        """
        log.debug('requireService: driver:%s app:%s' % (driver, app))
        try: 
            spawner = self.bus.get_object(turk.TURK_SPAWNER_SERVICE, '/Spawner')
            spawner.requireService(type, driver, app, 
                    reply_handler=lambda:None, error_handler=self.driverFail)
        except dbus.DBusException, e:
            log.debug(e)

    def driverFail(self, exception):
        log.debug('failed to start require driver: %s' % exception)

    @dbus.service.signal(dbus_interface=turk.TURK_BRIDGE_INTERFACE, signature='')
    def BridgeStarted(self):
        """
        Called to indicate that the Bridge has successfully started up and
        authenticated with the XMPP server
        """


class BridgeXMPPHandler(PresenceClientProtocol, RosterClientProtocol):

    REQUIRE = "/message/require[@xmlns='http://turkinnovations.com/protocol']"
    REGISTER = "/message/register[@xmlns='http://turkinnovations.com/protocol']"
    UPDATE = "/message/update[@xmlns='http://turkinnovations.com/protocol']"

    def __init__(self, bridge, stream):
        self.bridge = bridge
        self.stream = stream

    def connectionInitialized(self):
        """
        Called right after connecting to the XMPP server. Sets up handlers
        and subscriptions and sends out presence notifications
        """

        log.debug('connectionInitialized')
        PresenceClientProtocol.connectionInitialized(self)
        RosterClientProtocol.connectionInitialized(self)

        # Debug callback for all stanza types
        #self.xmlstream.addObserver('/*', self.dataReceived)

        # Callback for chat messages
        self.xmlstream.addObserver('/message/body', self.onMessage)

        # Callback for subscribed presence
        self.xmlstream.addObserver("/presence[@type='subscribe']", self.subscribeReceived)

        # Callbacks for require, register, update
        self.xmlstream.addObserver(self.REQUIRE, self.onRequire)
        self.xmlstream.addObserver(self.REGISTER, self.onRegister)
        self.xmlstream.addObserver(self.UPDATE, self.onUpdate)

        self.bridge.BridgeStarted()

        def rosterReceived(roster):
            """ Subscribe to all contacts in roster """
            for jid in roster:
                self.subscribe(JID(jid))
        # Get roster
        self.getRoster().addCallback(rosterReceived)

        # Set status to available
        self.available(show="chat", statuses={'':'Turk Platform Ready'})

    
    def dataReceived(self, element):
        """
        Called when any data is received
        """
        log.debug(element.toXml())

    
    def send(self, element):
        """
        Sends a message over the XML stream
        """
        self.stream.send(element)

    
    def sendMessage(self, to, message, type='normal'):
        """
        Sends a message to another XMPP client 
		"""
        msg = Element(("jabber:client", "message"))
        msg.attributes = { 'to': to.full(), 'type':type }
        body = msg.addElement("body", content=message)
        self.send(msg)

    
    def onMessage(self, message):
        """
        Called when a message stanza was received.
        """
        print
        text = str(message.body)
        type = message.getAttribute('type')

        log.debug("BridgeXMPPHandler: received a '%s' message: '%s'" % (type, text))

    def onRequire(self, message):
        """ Called when Turk require element(s) are received """
        log.debug('require stanza received')
        for driver in xpath.queryForNodes(self.REQUIRE + "/driver", message):
            require = driver.parent
            id = int(str(driver))
            app = int(require['app'])
            log.debug('driver %s required for app %s' % (id, app))

            # Check for and/or start the driver
            self.bridge.requireService(id, app)

    def onRegister(self, message):
        """
        Called when Turk register element(s) are received
        """
        log.debug('register stanza received')
        for driver in xpath.queryForNodes(self.REGISTER + "/driver", message):
            register = driver.parent
            id = int(driver['id'])
            app = int(register['app'])
            url = register['url']
            log.debug('app %s registering to driver %s' % (id, app))
            self.bridge.registerObserver(id, app, url)

    def onUpdate(self, message):
        """
        Called when Turk update element(s) are received
        """
        log.debug('update stanza received')
        for update in xpath.queryForNodes(self.UPDATE, message):
            try:
                driver = int(update['to'])
                app = int(update['from'])
                log.debug('got an update for driver#%s from app#%s' % (driver, app))

                # Send the update to the driver
                self.bridge.SignalUpdate(driver, app, update.toXml())

            except Exception, e:
                log.debug('Error parsing update XML: %s' % e)

    
    def subscribeReceived(self, entity):
        """
        Subscription request was received.
        Approve the request automatically by sending a 'subscribed' presence back
        """
        self.subscribed(entity)


class Driver(dbus.service.Object):
    def __init__(self, bus, id):
        self.path = '/Bridge/Drivers/%d' % (id)
        bus_name = dbus.service.BusName(turk.TURK_BRIDGE_SERVICE, bus)
        dbus.service.Object.__init__(self, bus_name=bus_name, object_path=self.path)
        self.type = type
        self.id = id
        self.last_update = ''

    @dbus.service.signal(dbus_interface=turk.TURK_BRIDGE_INTERFACE, signature='tts')
    def Update(self, driver, app, update):
        self.last_update = update
        log.debug('%s received an update: %s' % (self.path, update.replace('\n','')))

    @dbus.service.method(dbus_interface=turk.TURK_DRIVER_INTERFACE, in_signature='', out_signature='s')
    def GetLastUpdate(self):
        return self.last_update


def run(conf='turk.yaml'):
    # Load conf if it's a filename
    if isinstance(conf, basestring):
        try:
            conf = yaml.load(open(conf, 'rU'))
        except Exception:
            print 'failed opening configuration file "%s"' % (conf)
            exit(1)

    global log
    log = turk.init_logging('bridge', conf)
    log.debug('DBUS Session Bus is at %s' % os.environ['DBUS_SESSION_BUS_ADDRESS'])

    jid = JID(get_config('bridge.username', conf))

    try:
        bus = dbus.SessionBus()
    except dbus.DBusException:
        log.critical('Failed to connect to DBus SessionBus')
        log.debug('DBus UNIX socket is at %s' % os.getenv('DBUS_SESSION_BUS_ADDRESS'))
        exit(1)

    server, port = get_config('bridge.server', conf), get_config('bridge.port', conf)
    password = get_config('bridge.password', conf)

    bridge = Bridge(server, port, jid, password, bus)
    reactor.run()



if __name__ == '__main__':
    run()

