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

.. highlight:: yaml

The following is a basic template to start off with::

    # Global configuration
    global:
        bus: SessionBus

    # control interface and launcher (corectl.py)
    turkctl:
        pidfile: 'turk.pid'
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

    
    

Writing your first driver
-------------------------

Proin neque elit, mollis vel, tristique nec, varius consectetuer, lorem. Nam
malesuada ornare nunc. Duis turpis turpis, fermentum a, aliquet quis, sodales
at, dolor. Duis eget velit eget risus fringilla hendrerit. Nulla facilisi.
Mauris turpis pede, aliquet ac, mattis sed, consequat in, massa. Cum sociis
natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus.
Etiam egestas posuere metus. Aliquam erat volutpat. Donec non tortor. Vivamus
posuere nisi mollis dolor. Quisque porttitor nisi ac elit. Nullam tincidunt
ligula vitae nulla::
    
    # This is a code sample
    class Driver(dbus.service.Object):
        """ This interfaces a device to the Turk Framework """
        def __init__(self, address, bus):
            self.bus = bus
            self.address = address
            super(dbus.service.Object, self).__init__()

        def recieve(message):
            do_something(message)

This is some C++ code:
            
.. code-block:: c++

    void TurkDriver::ReceiveMessage(Message msg) {
        this.doSomething(msg);
        return;
    }

Vivamus sit amet risus et ipsum viverra malesuada. Duis luctus. Curabitur
adipiscing metus et felis. Vestibulum tortor. Pellentesque purus. Donec
pharetra, massa.

Writing and deploying a Tapp
----------------------------

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

