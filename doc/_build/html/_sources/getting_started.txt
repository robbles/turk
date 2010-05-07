***************************************
Getting started with the Turk Framework
***************************************

.. _getting-started:

Installing
----------

Turk is a package on the Python Package Index (http://pypi.python.org/pypi), and
can be installed using the easy_install or pip command-line tools:
    
.. code-block:: bash

    $ easy_install Turk

    $ pip install Turk

It can also be installed from source, by downloading the latest source archive
from a variety of places and using the included setup script:
    
.. code-block:: bash

    $ tar xvzf Turk-0.1.1.tar.gz
    $ cd Turk-0.1.1/
    $ [sudo] python setup.py install

Needless to say, Python needs to be installed to do this. Turk works with any
version in the 2.5-2.6 series, which are installed by default on many platforms.
The other main dependencies are the D-Bus library and its python bindings (usually
called python-dbus). These can be obtained from `freedesktop.org <http://dbus.freedesktop.org/releases/>`_.
    

Setting up the configuration
----------------------------

Setting up a customized configuration file is a very important step. This file
is not only used to configure the framework to work properly on your system, but
also to organize drivers to be run and servers to connect to. It's written in
YAML [#yaml]_, and can be placed anywhere on the system.


Why use YAML?
^^^^^^^^^^^^^
According to the YAML website:

    YAML™ (rhymes with “camel”) is a human-friendly, cross language, Unicode
    based data serialization language designed around the common native data
    types of agile programming languages. It is broadly useful for programming
    needs ranging from configuration files to Internet messaging to object
    persistence to data auditing. 

Many other data formats are used for software configuration, including XML, INI files,
and programming languages themselves. However, YAML has two significant
advantages, namely that it is one of the most human-readable formats, and that
it maps well to many logical data types. This allows the configuration file to
be easily edited by both users and software.

Example Configuration
^^^^^^^^^^^^^^^^^^^^^

The configuration file has a set of known defaults, which means an empty file
will result in a set of reasonably sane values being used. However, these values
may change between versions, and shouldn't be relied upon for important
settings. A safe method is to start with a configuration that specifies all
values as the default, and change them as necessary. That way, when the software
is upgraded, only new values will be unspecified, and should be set to
non-disruptive values (i.e. new features will be turned off by default). 


The following is a basic template to start off with:

.. code-block:: yaml

    # Global configuration
    global:
        bus: SessionBus

    # control interface and launcher (corectl.py)
    turkctl:
        pidfile: '/var/run/turk.pid'
        debug: True

    # bridge (handles XMPP relaying)
    bridge:
        server: macpro.local
        port: 5222
        username: platform@macpro.local
        password: password
        debug: True

    # spawner (starts/stops and manages drivers)
    spawner:
        # Location of drivers (prefixed to all driver filenames)
        drivers: /usr/share/turk/drivers

        # Add drivers that should be automatically started here along with their
        # environment variables and command line arguments
        autostart: [
            {'device_id': 1, 'filename': 'tick.py', 'env': {}, 'args': []},
            #{'device_id': 2, 'filename':'rgb_lamp.py', 'env':{'DEVICE_ADDRESS':'0xFF'}, 'args': []},
        ]
        debug: True

    # xbeed (handles XBee communication)
    xbeed:
        name: xbee0
        port: '/dev/ttys8'
        baudrate: 9600
        escaping: True
        debug: True
    

Writing a simple driver
-------------------------

Although the framework comes with drivers for some simple tasks such as fetching
the current date and time, and controlling simple wireless devices, most
projects will need their own custom drivers. 

Drivers are meant to be a way of translating the XML protocol used by Turk
applications into another protocol, using a network or serial interface, or a
web API. A web application can send XMPP messages to a predefined JID [#jid]_, and
the framework will forward those messages to the correct driver. The drivers can
send out their own messages, and any number of applications can subscribe to
these updates.

Drivers are usually started by adding a listing to the configuration file that
specifies the location of the file to run, any environment variables or
command-line arguments it needs, and a unique identification number, or "device
ID". This ID represents the abstracted "device" that the driver controls, and
allows multiple drivers of the same type to be run at once. An example of such a
listing can be seen in the sample configuration file above, in the autostart
section.

Once started, communication between the driver and the rest of the framework is
done through the D-Bus protocol. This allows drivers to use other services in
the framework through remote method calls, and to receive messages through
signals. For more information on how D-Bus method calls and signals work, read
`this introduction to D-Bus <http://www.freedesktop.org/wiki/IntroductionToDBus>`_.

Example Driver
^^^^^^^^^^^^^^

The following is an example of a simple self-contained driver, written in
Python. It uses both the Bridge API to receive updates from applications, and
the XBee service to send binary packets to a wireless device.

.. code-block:: python

    #! /usr/bin/env python
    import gobject
    import dbus
    import dbus.mainloop.glib
    from turk.xbeed import xbeed
    from xml.dom.minidom import parseString
    import turk

    class RGBLamp(dbus.service.Object):
        def __init__(self, device_id, device_addr, bus):
            """ Initializes the driver and connects to any relevant signals """
            dbus.service.Object.__init__(self, bus, '/Drivers/RGBLamp/%X' % device_addr)
            self.device_id = device_id
            self.device_addr = device_addr
            self.bus = bus

            # Get proxy for XBee interface
            self.xbee = self.bus.get_object(xbeed.XBEED_SERVICE, xbeed.XBEED_DAEMON_OBJECT % 'xbee0')

            # Register update signal handler
            listen = '/Bridge/Drivers/%d' % (self.device_id)
            self.bus.add_signal_receiver(handler_function=self.update,
                                         bus_name=turk.TURK_BRIDGE_SERVICE,
                                         signal_name='Update',
                                         path=listen)
            
        def update(self, driver, app, xml):
            """ Called every time an update for this driver is received. """
            try:
                tree = parseString(xml)

                command = tree.getElementsByTagName('command')[0]
                ctype = command.getAttribute('type') 

                if ctype == 'color':
                    # Parse hex color into RGB values
                    color = command.childNodes[0].nodeValue.lstrip('# \n\r')
                    red, green, blue = [int(color[i:i+2], 16) for i in range(0, 6, 2)]

                    # Build a message of the form "[RGB]"
                    msg = ''.join(['[', chr(red), chr(green), chr(blue), '#]'])

                    # Send it to the device
                    self.xbee.SendData(dbus.ByteArray(msg), dbus.UInt64(self.device_addr), 1)

                elif ctype in ['on', 'off', 'shift', 'noshift']:
                    command_byte = {
                            'on' : '@',
                            'off' : '*',
                            'shift' : '$',
                            'noshift' : '|' }[ctype]
                    msg = ''.join(['[\x00\x00\x00', command_byte, ']'])
                    self.xbee.SendData(dbus.ByteArray(msg), dbus.UInt64(self.device_addr), 2)

            except Exception, e:
                # emit an error signal for Bridge
                self.Error(e.message)
            
        def run(self):
            """ Loops forever and waits for signals from the framework """
            loop = gobject.MainLoop()
            loop.run()

        @dbus.service.signal(dbus_interface=turk.TURK_DRIVER_ERROR, signature='s') 
        def Error(self, message):
            """ Called when an error/exception occurs. Emits a signal for any relevant
                system management daemons and loggers """
            pass

    # Run as a standalone driver
    if __name__ == '__main__':
        import os
        device_id = int(os.getenv('DEVICE_ID'))
        device_addr = int(os.getenv('DEVICE_ADDRESS'), 16)
        bus = os.getenv('BUS', turk.get_config('global.bus'))
        print "RGB Lamp driver started... driver id: %u, target xbee: 0x%X" % (device_id, device_addr)
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        driver = RGBLamp(device_id, device_addr, getattr(dbus, bus)())
        driver.run()

    
There are more examples of drivers included with the framework written in
several other languages, including Ruby, Java, and C++. As D-Bus has bindings
for most commonly used programming languages, this allows developers to
leverage already-written code or libraries to write their drivers. The main
limitation of this approach is the relative lack of support for the Windows
platform, as there is currently no stable port available. However, this
situation should change relatively soon, as the project is still under active
development.

For more detail about writing drivers and the APIs available to them, see
the :ref:`driver-design` section.



Writing and deploying a web application
---------------------------------------

Creating a web application that uses Turk is even simpler, as they just send
simple XMPP messages to the framework, and only need to be able to process HTTP
POST requests. An application's work-flow looks something like this:

* Application sends a "register" XMPP message to the Turk platform when activated, to
  subscribe to any updates from a specified set of drivers.
* Application sends "update" XMPP messages to the platform on input from the user,
  and they are automatically forwarded to the relevant drivers.
* Driver sends a new "update", and the framework translates it into a HTTP POST
  to the application.
* Application is re-activated by the POST, and can choose to send a message back
  to the platform through XMPP.

How does it work?
^^^^^^^^^^^^^^^^^

The important concept to understand here is that the communication from
application to driver is done through XMPP, whereas drivers send messages back
through HTTP POST requests. Although the content uses the same XML-based
protocol, the transport is different. This is necessary due to the nature of the
client-server model used by most web applications. The web application can't
actively listen for XMPP messages, thus requiring HTTP requests to "wake it up",
and the Turk platform likely isn't listening on a known internet address,
requiring XMPP messages to "push" data to it.

Implementation
^^^^^^^^^^^^^^

The two main difficulties involved in designing an application lie in sending
the XMPP messages and determining when the application registers itself to the
platform. XMPP messages can be easily sent server-side using a variety of
available libraries for languages such as PHP, Python, Ruby and Java. Depending
on the XMPP server used, there are also ways of sending client-side messages
using Javascript and AJAX requests. Some XMPP servers, such as ejabberd and
OpenFire, support an extension called BOSH (Bidirectional-streams Over
Synchronous HTTP), which enables applications to use XMPP through HTTP requests.

The following shows a simple example of sending an XMPP message with PHP and the
`XMPPHP library <http://code.google.com/p/xmpphp/>`_:

.. code-block:: php

    <?php
    include 'XMPPHP/XMPP.php';

    $platform = "turk-platform-account@xmpp-server.tld";
    $driver_id = 8;
    $conn = new XMPPHP_XMPP('xmpp-server.tld', 5222, 'turk-app-account', 'password', 'xmpphp');

    try {                   
        # Connect to server and indicate presence
        $conn->connect();   
        $conn->processUntil('session_start');
        $conn->presence();

        # Build update message containing simple XML command
        $msg = '<message xmlns="jabber:client" to="'.$platform.'">';
        $msg .= '<update xmlns="http://turkinnovations.com/protocol" to="'.$driver_id.'" from="0">';
        $msg .= '<command type="on" />';
        $msg .= '</update>';
        $msg .= '</message>';

        # Send message and close the connection
        $conn->send($msg);
        $conn->disconnect();
    } catch(XMPPHP_Exception $e) {
        die($e->getMessage());
    }
    ?>

Running this script on your server will send the following XMPP message to
turk-platform-account@xmpp-server.tld (the XMPP JID the platform
is using). 

.. code-block:: xml

    <message xmlns="jabber:client" to="turk-platform-account@xmpp-server.tld">
        <update xmlns="http://turkinnovations.com/protocol" to="8" from="0">
            <command type="on" />
        </update>
    </message>

In this case, the "update" stanza is interpreted by the Turk
framework as a request to forward data to a driver. The "to" attribute holds the
ID of the driver to send it to. The "command" stanza (and anything else inside
the update) is custom data for the driver to receive, and can be anything,
including text or binary data, as long as it is properly escaped or encoded as
XML.

For the application to receive data back from the driver, it needs to provide
the platform with a URL to connect back to. Subscribing to a driver's updates is
done by sending a "register" to the platform.

.. code-block:: xml

    <message xmlns="jabber:client" to="turk-platform-account@xmpp-server.tld">
        <register xmlns="http://turkinnovations.com/protocol" app="2" url="http://example.com/updates/">
            <driver id="8" />
        </register>
    </message>
    
This notifies the platform that any updates from driver #8 should be sent to
"http://example.com/updates/" as an HTTP POST request. The data from the
driver will be wrapped up in a "update" stanza, with the "to" and "from" fields
automatically filled in.

.. code-block:: xml

    POST /update/ HTTP/1.1
    Host: example.com
    User-Agent: TurkFramework/0.12
    Content-Type: application/xml; charset=utf-8
    Content-Length: 268

    <?xml version="1.0" encoding="utf-8"?>
    <update xmlns="http://turkinnovations.com/protocol" to="0" from="8">
        <status>OK</status>
    </update>


Deploying an Application
^^^^^^^^^^^^^^^^^^^^^^^^

Although applications can send messages to a Turk platform from anywhere in the
world through the internet, they need to have a well-known, publically visible
URL for Turk to send updates back. To get around this limitation, there will
most likely be an update to the protocol allowing applications to register their
XMPP JID (e.g. "turk-app-account@xmpp-server.tld") instead of a URL, so that
they will receive updates as XMPP messages. This will also be useful for
client-side Javascript applications, as they will be able to send and receive
data from the platform without involving the web server at all!

However, the most common usage is to have the application hosted somewhere on
the web, with server-side scripts doing the XMPP and HTTP processing. This is
the simplest method, and allows the application to store semi-permanent state
information about the drivers it controls.









.. rubric:: Footnotes

.. [#yaml] YAML: YAML Ain't Markup Language (see `yaml.org <http://yaml.org>`_)

.. [#jid] JID: Jabber ID, a unique identifier for a user on an XMPP server. Structured like an email address (username@host.tld)


