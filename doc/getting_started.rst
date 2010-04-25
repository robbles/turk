***************************************
Getting started with the Turk Framework
***************************************

Installing
----------

Turk is a package on the Python Package Index (http://pypi.python.org/pypi), and
can be installed using the easy_install or pip command-line tools:
    
.. code-block:: bash

    $ easy_install Turk

    $ pip install Turk

It can also be installed from source, by downloading the latest source archive
from a variety of places and using python:
    
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

Setting up a customized configuration file is a very important step for every
Turk setup. This file is not only used to configure the framework to work
properly on your system, but also to organize drivers to be run and servers to
connect to. It's written in YAML [#yaml]_, and can be placed anywhere on the
system.


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

Example
^^^^^^^

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

    # bridge (drivers <-> XMPP <-> apps)
    bridge:
        server: macpro.local
        port: 5222
        username: platform@macpro.local
        password: password
        debug: True

    # spawner (starts/stops and manages drivers)
    spawner:
        # Location of all drivers (prefixed to all driver filenames)
        drivers: /usr/share/turk/drivers

        # Add drivers that should be automatically started here along with their
        # environment variables and command line arguments
        autostart: [
            {'device_id': 1, 'filename': 'tick.py', 'env': {}, 'args': []},
            #{'device_id': 2, 'filename':'rgb_lamp.py', 'env':{'DEVICE_ADDRESS':'0x0'}, 'args': []},
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
web API. A web application can send XMPP messages to a predefined account, and
the framework will forward those messages to the correct driver. The drivers can
send out their own messages, and any number of applications can subscribe to
these updates.

Drivers are usually started by adding a listing to the configuration file that
specifies the location of the file to run, any environment variables or
command-line arguments it needs, and a unique identification number, or "device
ID". This ID represents the abstracted "device" that the driver controls, which
allows multiple drivers of the same type to be run at once. An example of such a
listing can be seen in the sample configuration file above, in the autostart
section.

Once started, communication between the driver and the rest of the framework is
done through the D-Bus protocol. This allows drivers to use other services in
the framework through remote method calls, and to receive messages through
signals. For more information on how D-Bus method calls and signals work, read
`this introduction to D-Bus <http://www.freedesktop.org/wiki/IntroductionToDBus>`_.

Example
^^^^^^^

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

    DRIVER_ID = 6

    """
    ### Sample config ###

    ## XMPP commands ##
    <command type="color">#63A7E7</command>
    <command type="on" />
    <command type="off> />
    <command type="shift" />
    <command type="noshift" />

    ### Sent to device ###
    "[\x63\xA7\xE7#]" (for color command)

    """

    class RGBLamp(dbus.service.Object):
        def __init__(self, device_id, device_addr, bus):
            """ Initializes the driver and connects to any relevant signals """
            dbus.service.Object.__init__(self, bus, '/Drivers/RGBLamp/%X' % device_addr)
            self.device_id = device_id
            self.device_addr = device_addr
            self.bus = bus

            # Get proxy for XBee interface
            self.xbee = xbeed.get_daemon('xbee0', self.bus)

            listen = '/Bridge/Drivers/%d' % (self.device_id)
            self.bus.add_signal_receiver(self.update, path=listen)

            
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

    


Writing and deploying a web application
---------------------------------------

Malesuada elementum, nisi. Integer vitae enim quis risus aliquet gravida.
Curabitur vel lorem vel erat dapibus lobortis. Donec dignissim tellus at arcu.
Quisque molestie pulvinar sem.

Nulla magna neque, ullamcorper tempus, luctus eget, malesuada ut, velit. Morbi
felis. Praesent in purus at ipsum cursus posuere. Morbi bibendum facilisis
eros. Phasellus aliquam sapien in erat. Praesent venenatis diam dignissim dui.
Praesent risus erat, iaculis ac, dapibus sed, imperdiet ac, erat. Nullam sed
ipsum. Phasellus non dolor. Donec ut elit.

Sed risus.

Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Vestibulum sem lacus,
commodo vitae, aliquam ut, posuere eget, dui. Praesent massa dui, mattis et,
vehicula.

Troubleshooting
---------------

Justo ac sem.

Pellentesque at dolor non lectus sagittis semper. Donec quis mi. Duis eget
pede. Phasellus arcu tellus, ultricies id, consequat id, lobortis nec, diam.
Suspendisse sed nunc. Pellentesque id magna. Morbi interdum quam at est.
Maecenas eleifend mi in urna. Praesent et lectus ac nibh luctus viverra. In vel
dolor sed nibh sollicitudin tincidunt. Ut consequat nisi sit amet nibh. Nunc mi
tortor, tristique sit amet, rhoncus porta, malesuada elementum, nisi. Integer
vitae enim quis risus aliquet gravida. Curabitur vel lorem vel erat dapibus
lobortis. Donec dignissim tellus at arcu. Quisque molestie pulvinar sem.

Nulla magna neque, ullamcorper tempus, luctus eget.




.. rubric:: Footnotes

.. [#yaml] YAML: YAML Ain't Markup Language (see `yaml.org <http://yaml.org>`_)



