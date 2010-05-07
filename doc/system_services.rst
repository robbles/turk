System Services
=======================================

One of the main features of the Turk Framework is the API it provides to drivers
and plugins. This API consists of a collection of D-Bus method calls and signals
that drivers can use. These are outlined here, and organized by the
functionality they provide.

Bridge
----------------------------

The Bridge component acts as an XMPP router between drivers, services and
applications, and can be instructed to send messages. Drivers can also listen
for signals that match their ID, allowing them to asynchronously receive
messages.

Signals
^^^^^^^

* BridgeStarted (signature ''):
    This signal is emitted when the Bridge is started. Drivers can listen for
    this to determine when the Bridge is ready to receive instruction.

* Update (signature 'tts'):
    This signal is emitted when an update is received. Drivers can listen for
    this signal on the path '/Bridge/Drivers/[DRIVER ID]' to receive updates
    sent to them.

Methods
^^^^^^^

* RegisterDriver (in signature 't', out signature ''):
    Registers a driver ID with the bridge, so that it can receive updates.
    Depending on the D-Bus binding being used by the driver, calling this might
    not be necessary

* PublishUpdate (in signature 'sss', out signature ''):
    Sends an update from a driver to any applications that have registered to
    receive data from it. The arguments correspond to the type attribute, the
    update XML, and the driver ID.

* GetLastUpdate (in signature '', out signature 's'):
    Retrieves the last update sent to this driver ID. May be useful for drivers
    that are unable to use a D-Bus event loop, as they can poll the Bridge for
    updates instead.


Spawner
----------------------------

The Spawner handles driver management, and is responsible for keeping the list
of drivers running. It also can be instructed to dynamically start and stop
drivers as necessary.

Signals
^^^^^^^

* SpawnerStarted (signature ''):
    This signal is emitted when the Spawner is started. Drivers can listen for
    this to determine when the Spawner is ready to receive instruction.

* DriverStarted (signature 's'):
    This signal is emitted when a new driver is started.

Methods
^^^^^^^

* RegisterDriver (in signature 't', out signature ''):
    Registers a driver ID with the bridge, so that it can receive updates.
    Depending on the D-Bus binding being used by the driver, calling this might
    not be necessary

* PublishUpdate (in signature 'sss', out signature ''):
    Sends an update from a driver to any applications that have registered to
    receive data from it. The arguments correspond to the type attribute, the
    update XML, and the driver ID.

* GetLastUpdate (in signature '', out signature 's'):
    Retrieves the last update sent to this driver ID. May be useful for drivers
    that are unable to use a D-Bus event loop, as they can poll the Bridge for
    updates instead.

* StartDriverByName (in_signature 'tsa(ss)', out_signature '')
    Starts a driver process, given the device ID, the driver ID, and the
    environment variables to launch it with.

* RestartDriverByID (in_signature 't', out_signature '')
    Restarts the driver with the given ID.

* StopDriverByID (in_signature 't', out_signature '')
    Stops the driver with the given ID.

* GetDriverList (in_signature '', out_signature 'a(ts)')
    Returns a list of the currently running drivers and their names.


XBee Daemon(s)
-------------------------

The XBee daemon is an optional service that can be used to connect to a Zigbee
network using a Digi XBee radio. This service is experimental, and may still be
prone to occasional errors. The configuration also must be set up properly to
match with the settings on the radio itself.

Signals
^^^^^^^

* RecievedData (signature 'ayt'):
    Called when a packet sent to this radio has been received. Returns the data
    in an array of bytes and the hardware address of the radio it was received
    from.

Methods
^^^^^^^

* SendData (in signature 'ayty', out signature ''):
    Sends the given data to the radio with the given hardware address. The last
    parameter is a frame ID that can be used to verify whether the packet made
    it to the destination.


Other plugins and services
----------------------------------

Other services can be added to the Turk Framework by exposing D-Bus APIs on the
same bus. The simplest way to do this currently is to launch them as drivers, as
they can be specified in the configuration file and re-configured through a web
interface.

