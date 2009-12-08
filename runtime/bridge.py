#! /usr/bin/env python

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
from twisted.application.internet import TCPClient
from twisted.internet import reactor
from wokkel.xmppim import MessageProtocol, PresenceClientProtocol
from wokkel.xmppim import AvailablePresence, UnavailablePresence

server = ('macpro.local', 5222)
thorax = 'thorax@macpro.local'
app = 'app@macpro.local'
jid = JID("platform@macpro.local")
password = 'password'

TURK_BRIDGE_SERVICE = "org.turkinnovations.core.Bridge"
TURK_BRIDGE_INTERFACE = "org.turkinnovations.core.Bridge"
TURK_CONFIG_INTERFACE = "org.turkinnovations.core.Configuration"

class Bridge(dbus.service.Object):
    def __init__(self, server, port, jid, password, bus):
        # Setup D-BUS service and signal callbacks
        bus_name = dbus.service.BusName(TURK_BRIDGE_SERVICE, bus)
        self.bus = bus
        dbus.service.Object.__init__(self, bus_name, '/Bridge')
        bus.add_signal_receiver(self.dbus_signal, byte_arrays=True, member_keyword='member')

        # Setup XMPP client 
        factory = client.XMPPClientFactory(jid, password)
        self.handler = BridgeXMPPHandler(self)
        self.manager = xmlstream.StreamManager(factory)
        self.manager.addHandler(self.handler)
        client_svc = TCPClient(server, port, factory)
        client_svc.startService()

        # Setup config files
        self.configs = {}

        # Change status to available
        self.manager.send(AvailablePresence(JID(thorax),
                         'chat', {'':'XMPP Tester Online'}))

        # Send a message
        self.sendMessage(thorax, 'turk platform initialized')

        self.BridgeStarted()

    def dbus_signal(self, *args, **kw):
        print 'recieved dbus signal!'
        print args
        print kw['member']
        member = kw['member']
        self.sendMessage(thorax, 'dbus:%s' % member)

    def sendMessage(self, to, message):
        msg = Element(("jabber:client", "message"))
        msg["to"] = to
        body = msg.addElement("body", content = message)
        self.manager.send(msg)

    def handleMessage(self, text):
        try:
            #TODO: Make sure that input is sanitized somehow so we can do this
            driver, config, app = text.split(':')
            print 'driver:%s config:%s app:%s' % (driver,config,app)
            
            if driver in self.configs:
                self.configs[driver].NewDriverConfig(driver, app, config)
            else:
                self.configs[driver] = ConfigFile(self.bus, driver, app, config)
        except Exception, e:
            print e
            print 'Bridge: Failed parsing XMPP message'

    @dbus.service.signal(dbus_interface=TURK_BRIDGE_INTERFACE, signature='')
    def BridgeStarted(self):
        pass


class BridgeXMPPHandler(MessageProtocol, PresenceClientProtocol):
    def __init__(self, bridge):
        self.bridge = bridge

        # Add handlers for messages and presence
        MessageProtocol.__init__(self)
        PresenceClientProtocol.__init__(self)

    def connectionInitialized(self):
        MessageProtocol.connectionInitialized(self)
        PresenceClientProtocol.connectionInitialized(self)

    def availableReceived(self, entity, show=None, statuses=None, priority=0):
        print 'availableReceived!'

    def unavailableReceived(self, entity, show=None, statuses=None, priority=0):
        print 'unavailableReceived!'

    def onMessage(self, message):
        text = str(message.body)
        print 'message received: \'%s\'' % text
        self.bridge.handleMessage(text)


class ConfigFile(dbus.service.Object):
    def __init__(self, bus, driver, app, config):
        dbus.service.Object.__init__(self, bus, '/Bridge/ConfigFiles/%s' % driver)
        self.driver = driver
        self.app = app
        self.config = config
        self.NewDriverConfig(driver, app, config)

    @dbus.service.signal(dbus_interface=TURK_BRIDGE_INTERFACE, signature='sss')
    def NewDriverConfig(self, driver, app, config):
        self.config = config

    @dbus.service.method(dbus_interface=TURK_CONFIG_INTERFACE, in_signature='', out_signature='s')
    def GetConfig(self):
        return self.config

    @dbus.service.method(dbus_interface=TURK_CONFIG_INTERFACE, in_signature='', out_signature='s')
    def GetApp(self):
        return self.app



if __name__ == '__main__':
    bridge = Bridge(server[0], server[1], jid, password, dbus.SystemBus())


reactor.run()




