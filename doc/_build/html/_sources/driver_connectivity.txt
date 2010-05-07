Driver Connectivity
=======================================

.. _driver-design:

Advanced Driver Design
----------------------

The examples of simple drivers given in the :ref:`getting_started` section are
effective for establishing simple communication between a device or service and
a web application, but have some major limitations. Due to the latency of the
Internet and various other factors, there is an upper limit on the speed at
which messages between drivers and applications can be sent. However, there are
many workarounds for this limitation. Messages from applications are primarily
meant to be used to update the current state of a driver, not to stream large
amounts of real-time data. With this in mind, the ideal way is to instruct the
driver to connect independently to a server, by giving it the
necessary details in a message.

Sending data between two drivers with the application as the intermediary is
another problem. Although the simplest way to do this is to relay the data
through the application and back down to the driver, this is far from ideal. If
there is minimal translation of the data involved, the drivers should be able to
communicate directly with each other.

Interconnecting Drivers and Apps
--------------------------------

A basic outline of the process of connecting a driver to an external service is
as follows, using RSS feeds as a simple example of an web service.

* Application registers to updates from driver:

.. code-block:: xml

    <message xmlns="jabber:client" to="turk-platform-account@xmpp-server.tld">
        <register xmlns="http://turkinnovations.com/protocol" app="2" url="http://example.com/updates/">
            <driver id="8" />
        </register>
    </message>

* User adds a new feed to be monitored to application
* Application notifies driver that it should start checking a new feed:

.. code-block:: xml

    <message xmlns="jabber:client" to="turk-platform-account@xmpp-server.tld">
        <update xmlns="http://turkinnovations.com/protocol" to="100" from="101">
            <feed type="atom" update="1min">
                <title>Digg News</title>
                <url>http://feeds.digg.com/digg/news/popular.rss</url>
            </feed>
        </update>
    </message>

* Driver starts fetching the RSS content from the URL every 1 minute
* When a new story is found, the driver sends out an update addressed to the
  app:

.. code-block:: xml

    <message xmlns="jabber:client" to="turk-platform-account@xmpp-server.tld">
        <update xmlns="http://turkinnovations.com/protocol" to="101" from="100">
            <story type="atom" date="1273212547">
            <title>Baboon attacks Prime Minister! Nation in panic.<title>
            <author>Lois Lane</author>
            </story>
        </update>
    </message>
    

Connecting two drivers together is even simpler, as all that is needed is a
D-Bus address and path. This allows one driver to make RPC calls to the other,
without going through the overhead of the XMPP handlers and the internet
communication.

.. code-block:: xml

    <message xmlns="jabber:client" to="turk-platform-account@xmpp-server.tld">
        <update xmlns="http://turkinnovations.com/protocol" to="101" from="100">
            <driver type="dbus" method="Update">
                <address>org.turkinnovations.exampledriver</address>
                <path>/Drivers/ExampleDriver/42</path>
            </driver>
        </update>
    </message>


Driver Dependencies
-------------------

A common issue with setting up a Turk system arises when drivers are dependent
on each other to run properly. Drivers can be reused as services to maximize
their capabilities, and can also be connected directly to each other for more
efficient communication. However, there are several important things to keep in
mind when implementing a system like this. 

Another issue that can arise with dependencies is fault tolerance.
Unfortunately, even the best drivers can have software bugs, and occasionally,
they crash. The framework is designed to deal with this, however, and will
automatically restart a driver when it detects a problem like this, unless
configured otherwise. However, other drivers must be able to handle any
connections being dropped or data lost in the process. Depending on the method
of communication used, other drivers may need to re-open the connection when the
program at the other end is restarted. DBus proxy connections, for example, are
based on the unique name of the connection. This means that if a driver was
using a reference to another driver, received from a controlling application, that
reference would be useless once the other driver was restarted. The same principle
as before applies to this situation - the driver has to monitor the connection,
and take steps to fix any communication problems when they occur.


Running Drivers on Demand
-------------------------

The simplest way to make sure a required driver is running is to include in the
configuration file and restart the framework. However, there are some use cases
for starting and stopping drivers on the fly. Examples of these are:

* Multi-driver systems that can turn off certain features when not in use
* Utility drivers that other drivers can start up when needed
* Controlling the Turk Framework from a graphical user interface

As a result, there is a way to do this through the Turk API. The API calls
StartDriverByName, RestartDriverByID, StopDriverByID and GetDriverList can be
used to control the Spawner component. This allows drivers and plugins to be
written that can dynamically control the list of drivers currently being managed
by the framework.

