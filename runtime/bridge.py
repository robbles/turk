#! /usr/bin/env python

import dbus
import dbus.service
import dbus.mainloop.glib
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
import yaml

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
    from wokkel.subprotocols import XMPPHandler
    from wokkel.xmppim import AvailablePresence, UnavailablePresence, Presence
    from wokkel.xmppim import PresenceClientProtocol, MessageProtocol, RosterClientProtocol

from turkcore.namespace import *

server =    ('macpro.local', 5222)
jid =       JID("platform@macpro.local")
password =  'password'


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

        # Init worker subscriptions
        self.subscriptions = {}


    @dbus.service.method(dbus_interface=TURK_BRIDGE_INTERFACE,
                         in_signature='sss', out_signature='')
    def PublishUpdate(self, type, update, source):
        """
        Publishes a new update via HTTP to all apps that have registered to
        this data source
        """

    
    def updateConfig(self, type, id, config, app):
        """
        Associates a new config entry with it's driver name, or updates
        the corresponding driver config if it already exists
        """
        if id in self.configs:
            self.configs[id].NewDriverConfig(id, config)
        else:
            self.configs[id] = ConfigFile(self.bus, type, id, config, app)

    
    def registerObserver(self, service, app):
        """
        Registers app to be notified of events coming from service
        """
        print 'registerObserver: service:%s app:%s' % (service, app)
        if service in self.subscriptions:
            self.subscriptions[service].append(app)
        else:
            self.subscriptions[service] = [app]

    
    def requireService(self, type, service, app):
        """
        Notifies Spawner that service needs to be started or already running.
        Forwards any error notifications to the server through XMPP
        """
        print 'requireService: service:%s app:%s' % (service, app)
        try: 
            spawner = self.bus.get_object(TURK_SPAWNER_SERVICE, '/Spawner')
            spawner.requireService(type, service, app, 
                    reply_handler=lambda:None, error_handler=self.serviceFail)
        except dbus.DBusException, e:
            print e

    def serviceFail(self, exception):
        print 'Bridge: failed to start require service: %s' % exception

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
        print element.toXml()

    
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

        print "BridgeXMPPHandler: received a '%s' message: '%s'" % (type, text)

    @debug 
    def onRequire(self, message):
        """
        Called when Turk require element(s) are received
        """
        for service in xpath.queryForNodes(self.REQUIRE + "/service", message):
            require = service.parent
            id = int(str(service))
            app = int(require['app'])
            type = service['type']
            print 'service %s required for app %s' % (id, app)
            self.bridge.requireService(type, id, app)

    @debug 
    def onRegister(self, message):
        """
        Called when Turk register element(s) are received
        """
        for service in xpath.queryForNodes(self.REGISTER + "/service", message):
            register = service.parent
            id = int(str(service))
            app = int(register['app'])
            print 'app %s registering to service %s' % (id, app)
            self.bridge.registerObserver(id, app)

    @debug 
    def onUpdate(self, message):
        """
        Called when Turk update element(s) are received
        """
        for update in xpath.queryForNodes(self.UPDATE, message):
            try:
                type = update['type']
                dest = int(update['to'])
                source = int(update['from'])
                print 'got a update of type %s' % type
                # Send the first element in the update to the driver
                self.bridge.updateConfig(type, dest, update.children[0].toXml(), source)
            except Exception, e:
                print 'Error parsing update XML: ', e

    
    def subscribeReceived(self, entity):
        """
        Subscription request was received.
        Approve the request automatically by sending a 'subscribed' presence back
        """
        self.subscribed(entity)


class ConfigFile(dbus.service.Object):
    def __init__(self, bus, type, id, config, app):
        if type == 'worker':
            self.path = '/Bridge/ConfigFiles/Workers/%d/%d' % (app, id)
        else:
            self.path = '/Bridge/ConfigFiles/Drivers/%d' % (id)
        dbus.service.Object.__init__(self, bus, self.path)
        self.type = type
        self.id = id
        self.config = config
        self.NewDriverConfig(id, config)

    @dbus.service.signal(dbus_interface=TURK_BRIDGE_INTERFACE, signature='ts')
    def NewDriverConfig(self, id, config):
        self.config = config
        print self.path, 'updated with new config:', config.replace('\n','')

    @dbus.service.method(dbus_interface=TURK_CONFIG_INTERFACE,
                         in_signature='', out_signature='s')
    def GetConfig(self):
        return self.config


def run():
    conf = yaml.load(open('core.yml', 'rU'))['bridge']
    print conf
    jid = JID(conf['username'])
    bus = getattr(dbus, conf.get('bus', 'SystemBus'))()
    bridge = Bridge(conf['server'], conf['port'], jid, conf['password'], bus)
    reactor.run()



if __name__ == '__main__':
    run()

