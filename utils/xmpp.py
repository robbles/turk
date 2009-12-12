#! /usr/bin/env python

from twisted.words.protocols.jabber import client, jstrports
from twisted.words.protocols.jabber.jid import JID
from twisted.words.protocols.jabber import xmlstream
from twisted.words.xish.domish import Element
from twisted.words.xish import xpath
from twisted.application.internet import TCPClient
from twisted.internet import reactor
from wokkel.subprotocols import XMPPHandler
from wokkel.xmppim import PresenceClientProtocol, MessageProtocol, RosterClientProtocol

server, port = 'macpro.local', 5222
jid = JID('platform@macpro.local')
password = 'password'

class SimpleXMPPHandler(PresenceClientProtocol, MessageProtocol, RosterClientProtocol):
    def __init__(self, stream):
        PresenceClientProtocol.__init__(self)
        MessageProtocol.__init__(self)
        RosterClientProtocol.__init__(self)
        self.stream = stream

    def connectionInitialized(self):
        """
        Called right after connecting to the XMPP server. Sets up handlers
        and subscriptions and sends out presence notifications
        """

    def onPresence(self, presence):
        """
        Called when a presence notification is received
        """
        print 'SimpleXMPPHandler: received a presence'

    def onMessage(self, message):
        """
        Called when a message is received
        """
        print 'SimpleXMPPHandler: received a presence'


if __name__ == '__main__':

    # Setup XMPP client 
    factory = client.XMPPClientFactory(jid, password)
    manager = xmlstream.StreamManager(factory)
    handler = SimpleXMPPHandler(manager)
    manager.addHandler(handler)
    client_svc = TCPClient(server, port, factory)
    client_svc.startService()
    reactor.run()





