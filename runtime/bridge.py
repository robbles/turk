#! /usr/bin/env python

from pdb import set_trace

import dbus
import dbus.service
import dbus.mainloop.glib
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

from twisted.internet import glib2reactor
glib2reactor.install()

from twisted.words.protocols.jabber import client, jstrports
from twisted.words.protocols.jabber.jid import JID
from twisted.words.protocols.jabber import xmlstream
from twisted.words.xish.domish import Element
from twisted.words.xish import xpath
from twisted.application.internet import TCPClient
from twisted.internet import reactor
from wokkel.subprotocols import XMPPHandler
from wokkel.xmppim import AvailablePresence, UnavailablePresence, Presence
from wokkel.xmppim import PresenceClientProtocol, MessageProtocol, RosterClientProtocol

server =    ('macpro.local', 5222)
thorax =    JID('thorax@macpro.local')
app =       JID('app@macpro.local')
platform =  JID('platform@macpro.local')
jid =       JID("platform@macpro.local")
password =  'password'
debug = False
daemon = False

TURK_BRIDGE_SERVICE = "org.turkinnovations.core.Bridge"
TURK_BRIDGE_INTERFACE = "org.turkinnovations.core.Bridge"
TURK_CONFIG_INTERFACE = "org.turkinnovations.core.Configuration"
TURK_CONFIG_NAMESPACE = "http://turkinnovations.com/protocol/1.0/config"


def debug(func):
    name = func.__name__
    def wrapper(*args, **kwargs):
        if func.func_code.co_code in ['d\x00\x00S','d\x01\x00S']:
            print '# %s #' % name
        else:
            print '[ %s ]' % name
        return func(*args, **kwargs)
    return wrapper


class Bridge(dbus.service.Object):
    """
    Manages the interface between the Turk Cloud and this platform using a
    combination of HTTP (for driver->app updates) and XMPP (for app->driver messages).
    Listens for relevant D-BUS signals and logs them to the XMPP server.
    """
    def __init__(self, server, port, jid, password, bus):
        # Setup D-BUS service and signal callbacks
        bus_name = dbus.service.BusName(TURK_BRIDGE_SERVICE, bus)
        self.bus = bus
        dbus.service.Object.__init__(self, bus_name, '/Bridge')

        # Setup XMPP client 
        factory = client.XMPPClientFactory(jid, password)
        self.manager = xmlstream.StreamManager(factory)
        self.handler = BridgeXMPPHandler(self, self.manager)
        self.manager.addHandler(self.handler)
        client_svc = TCPClient(server, port, factory)
        client_svc.startService()

        # Setup config files
        self.configs = {}

    @dbus.service.method(dbus_interface=TURK_BRIDGE_INTERFACE, in_signature='sss', out_signature='')
    def PublishUpdate(self, utype, update, source):
        """
        Publishes a new update via HTTP to all apps that have registered to
        this data source
        """

    @debug
    def updateConfig(self, utype, driver, config, app):
        """
        Associates a new config entry with it's driver name, or updates
        the corresponding driver config if it already exists
        """
        print 'updateConfig: utype:%s driver:%s config:%s app:%s' % (utype, driver, config, app)
        if driver in self.configs:
            self.configs[driver].NewDriverConfig(driver, config, app)
        else:
            self.configs[driver] = ConfigFile(self.bus, driver, config, app)

    @debug
    def registerObserver(self, service, app):
        """
        Registers app to be notified of events coming from service
        """
        print 'registerObserver: service:%s app:%s' % (service, app)

    @debug
    def requireService(self, service, app):
        """
        Notifies Spawner that service needs to be started or already running.
        Forwards any error notifications to the server through XMPP
        """
        print 'requireService: service:%s app:%s' % (service, app)

    @dbus.service.signal(dbus_interface=TURK_BRIDGE_INTERFACE, signature='')
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

    @debug
    def connectionInitialized(self):
        """
        Called right after connecting to the XMPP server. Sets up handlers
        and subscriptions and sends out presence notifications
        """

        PresenceClientProtocol.connectionInitialized(self)
        RosterClientProtocol.connectionInitialized(self)

        # Debug callback for all stanza types
        #self.xmlstream.addObserver('/*', self.dataReceived)

        # Callback for chat messages
        self.xmlstream.addObserver('/message/body', self.onMessage)

        # Callbacks for require, register, update
        self.xmlstream.addObserver(self.REQUIRE, self.onRequire)
        self.xmlstream.addObserver(self.REGISTER, self.onRegister)
        self.xmlstream.addObserver(self.UPDATE, self.onUpdate)

        self.bridge.BridgeStarted()

        @debug
        def rosterReceived(roster):
            """ Get roster and subscribe to all contacts """
            for jid in roster:
                print 'subscribing to presence from %s' % jid
                self.subscribe(JID(jid))
        self.getRoster().addCallback(rosterReceived)

        # Set status to available
        self.available(show="chat", statuses={'':'Turk Platform Ready'})

    @debug
    def dataReceived(self, element):
        """
        Called when any data is received
        """
        print element.toXml()

    @debug
    def send(self, element):
        """
        Sends a message over the XML stream
        """
        self.stream.send(element)

    @debug
    def sendMessage(self, to, message, type='normal'):
        """
        Sends a message to another XMPP client 
		"""
        msg = Element(("jabber:client", "message"))
        msg.attributes = { 'to': to.full(), 'type':type }
        body = msg.addElement("body", content=message)
        self.send(msg)

    @debug
    def onMessage(self, message):
        """
        Called when a message stanza was received.
        """
        print
        text = str(message.body)
        type = message.getAttribute('type')

        print "BridgeXMPPHandler: received a '%s' message: '%s'" % (type, text)

    @debug
    def onRequire(self, message):
        """
        Called when Turk require element(s) are received
        """
        for service in xpath.queryForNodes(self.REQUIRE + "/service", message):
            require = service.parent
            app = require['app']
            print 'service %s required for app %s' % (str(service), app)
            self.bridge.requireService(str(service), app)

    @debug
    def onRegister(self, message):
        """
        Called when Turk register element(s) are received
        """
        for service in xpath.queryForNodes(self.REGISTER + "/service", message):
            register = service.parent
            app = register['app']
            print 'app %s registering to service %s' % (app, str(service))
            self.bridge.registerObserver(str(service), app)

    @debug
    def onUpdate(self, message):
        """
        Called when Turk update element(s) are received
        """
        for update in xpath.queryForNodes(self.UPDATE, message):
            utype = update['type']
            dest = update['to']
            source = update['from']
            print 'got a update of type %s' % utype
            self.bridge.updateConfig(utype, dest, str(update), source)

    @debug
    def subscribeReceived(self, entity):
        """
        Subscription request was received.
        """
        self.subscribed(JID(entity['from']))

    @debug
    def probeReceived(self, presence):
        """
        Probe presence was received.
        """

    @debug
    def availableReceived(self, entity, show=None, statuses=None, priority=0):
        """
        Available presence was received.
        """

    @debug
    def unavailableReceived(self, entity, statuses=None):
        """
        Unavailable presence was received.
        """

    @debug
    def subscribedReceived(self, entity):
        """
        Subscription approval confirmation was received.
        """

    @debug
    def unsubscribedReceived(self, entity):
        """
        Unsubscription confirmation was received.
        """

    @debug
    def unsubscribeReceived(self, entity):
        """
        Unsubscription request was received.
        """


class ConfigFile(dbus.service.Object):
    def __init__(self, bus, driver, config, app):
        dbus.service.Object.__init__(self, bus, '/Bridge/ConfigFiles/%s' % driver)
        self.driver = driver
        self.app = app
        self.config = config
        self.NewDriverConfig(driver, config, app)

    @dbus.service.signal(dbus_interface=TURK_BRIDGE_INTERFACE, signature='sss')
    def NewDriverConfig(self, driver, config, app):
        self.config = config

    @dbus.service.method(dbus_interface=TURK_CONFIG_INTERFACE, in_signature='', out_signature='s')
    def GetConfig(self):
        return self.config

    @dbus.service.method(dbus_interface=TURK_CONFIG_INTERFACE, in_signature='', out_signature='s')
    def GetApp(self):
        return self.app



if __name__ == '__main__':
    from sys import argv
    from os import fork
    for arg in argv[1:]:
        if arg in ['-D', '--debug']:
            debug = True
        if arg in ['-d', '--daemon']:
            daemon = True

    if daemon and fork():
        print 'Bridge: forking into background'
        exit(0)

    bridge = Bridge(server[0], server[1], jid, password, dbus.SystemBus())
    reactor.run()




