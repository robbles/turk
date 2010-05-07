Configuring Turk
=======================================


Setting up Drivers
-------------------------

The Turk configuration file is designed to allow for maximum flexibility when
running drivers. Driver processes can actually be launched separately from the
other services and still function perfectly fine; the Spawner service just
makes this much simpler by both managing the drivers and passing them
information about the rest of the framework. Executables can be passed
information in two ways, command-line arguments and environment variables. These
are specified in the driver's configuration entry in the "args" and "env"
settings. 

Which is better?
^^^^^^^^^^^^^^^^

It is recommended to use environment variables to pass anything other than a
variable-length list of data (e.g. a list of RSS feeds that a driver will fetch)
to a Turk driver. They are much simpler to fetch and parse in most programming
languages, and tend not to suffer from as many formatting and semantic errors as
command-line arguments. Command-line arguments are difficult to use because they
are essentially a list of words passed to the program that need to have some
kind of meaning assigned to them. They require strict checking to make sure
invalid input is not accepted by the program. Environment variables, on the
other hand, are keyed by name, making them ideal for passing settings and simple
variables to a program. An example of this in the real world can be found in the
CGI standard, which used environment variables to pass information from web
requests to server scripts. Although somewhat outdated, this standard was the
most common way of producing dynamic content on the web for a long time.

Unique Identifiers
^^^^^^^^^^^^^^^^^^

The other important consideration for launching a set of drivers is the Device
ID. This number uniquely identifies a driver instance on a platform, and can be
used to ensure that a driver is not started twice by accident. The ID is
represented as a 64 bit (8 bytes) unsigned integer, which means there are
virtually unlimited numbers of Turk devices on one platform. One recommended
practice is for the driver to claim a D-Bus service name that includes the ID
somehow on startup. The D-Bus daemon will automatically enforce the requirement
that these names be unique, and the driver can gracefully shut down instead of
causing potential problems to an existing driver process.

An example of this:

.. code-block:: python

    import dbus, os

    # The device ID is passed automatically as an environment variable
    device_id = int(os.getenv('DEVICE_ID'))

    # Get the Session or System bus
    bus = getattr(dbus, os.getenv('BUS'))()
    
    # Register an object
    dbus.service.Object(bus, '/Drivers/MyDriver/%d' % device_id)


The Driver List
---------------

Drivers are typically started in the order they appear in the configuration
file, after a brief delay to ensure that the rest of the Turk services are
running. Since many programs have a short delay before becoming fully
operational, it is probably a good idea to carefully consider the order in which
the drivers are started. If a service, either from a lower-level plugin or just
another driver, is not available, the program must be able to handle this
gracefully. A reasonably effective way of handling this is to keep trying to
access the required services, with a short delay every time to avoid slowing
down the entire system.

.. code-block:: bash

    # Started first, since wall_display and robot_arm communicate with it
    {'device_id': 1, 'filename': 'remote_control', 'env': {}, 'args': []},

    # Order doesn't matter for these, since they don't connect at all
    {'device_id': 2, 'filename': 'wall_display', 'env':{'DEVICE_ADDRESS':'0x13A2004052DADD'}, 'args': []},
    {'device_id': 3, 'filename': 'robot_arm', 'env':{'DEVICE_ADDRESS':'0x13A2004052DA9A'}, 'args': []},


All Settings
----------------------------

The following is a list of all the possible settings currently available in the
Turk configuration file. Most of these settings are reasonably permanent, and
can be relied on by developers to stay the same. Experimental features will be
usable in various releases of the framework, but may disappear or change
significantly, so use them at your own risk.

* global: These settings apply to all services
    - bus: The D-Bus bus that all services and drivers connect to (SessionBus or
      SystemBus)

* turkctl: Options for the Turk launcher utility
    - pidfile: A file used to store the process ID of the main Turk process.
      turkctl uses this to stop/start the framework.
    - debug: Controls the amount of information when running this utility

* bridge: Options for XMPP communication
    - server: macpro.local
    - port: 5222
    - username: platform@macpro.local
    - password: password
    - debug: Set to True to log additional information about XMPP messages

* spawner: Options for driver spawning and management
    - autostart: [
    - drivers: /usr/share/turk/drivers
    - debug: Set to True to see additional information about drivers being
      started and stopped.

* xbeed: Options for XBee radio interface. Leave this section out to disable, if you aren't using one.
    - name: The name of this daemon. Used by drivers to contact this specific
      instance. May be used to allow multiple instances of this service in the
      future.
    - port: The serial port that the radio module is connected to (e.g.
      /dev/ttyS0)
    - baudrate: The baudrate the radio is configured at (e.g. 9600)
    - escaping: Set to True if this module has the escaping option on (see
      manual for more details)
    - debug: Set to True to see additional information about XBee communication

