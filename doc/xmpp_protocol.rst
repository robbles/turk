The Turk XMPP Protocol
=======================================

Current Protocol Specification
------------------------------

The Turk XMPP protocol currently consists of three tags that can be sent to and
from a platform:

* <update /> 
    The update tag is used to carry messages from applications to drivers. It
    must specify the driver ID to deliver the message to.
* <register />
    The register tag is sent by an application to subscribe to updates from a
    particular driver.
* <require />
    The require tag asks the framework to ensure that a required driver is
    running. This currently does nothing, but will eventually be used in the
    driver launching part of the framework.

These tags are all under the XML namespace
"http://turkinnovations.com/protocol", and are sent inside jabber:client message
tags like most XMPP chat messages.

Protocol Examples
-----------------

Registering to a driver
^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: xml

    <message xmlns="jabber:client" to="turk-platform-account@xmpp-server.tld">
        <register xmlns="http://turkinnovations.com/protocol" app="2" url="http://example.com/updates/">
            <driver id="8" />
        </register>
    </message>

Sending an update
^^^^^^^^^^^^^^^^^
.. code-block:: xml

    <message xmlns="jabber:client" to="turk-platform-account@xmpp-server.tld">
        <update xmlns="http://turkinnovations.com/protocol" to="8" from="0">
            <command type="on" />
        </update>
    </message>

Requiring a driver
^^^^^^^^^^^^^^^^^^
.. code-block:: xml

    <message xmlns="jabber:client" to="turk-platform-account@xmpp-server.tld">
        <require xmlns="http://turkinnovations.com/protocol" app="2">
            <driver id="8" />
        </require>
    </message>

Message Structure
-----------------

UPDATE
^^^^^^

The update tag must include the "to" and "from" attributes, indicating the
destination driver and source application IDs, respectively. It may also include
an optional "type" attribute, which can be used to indicate the context of the
update. This may be used in a future version of the framework.

REGISTER
^^^^^^^^

The register tag must include the "app" and "url" attributes. The first is used
by the framework to identify the app, and the second to forward messages using
HTTP. Drivers are specified with a list of "driver" tags, each of which must
include an "id" attribute representing the driver ID.

REQUIRE
^^^^^^^

The require tag must include the "app" attribute, which has the same meaning as
it does for the register tag. Drivers are specified with a list of "driver"
tags, each of which must include an "id" attribute representing the driver ID.

Future Developments
-------------------

There are several planned updates to the protocol, which will probably be
indicated by version numbers in the XML namespace. This will ensure
compatibility by allowing newer applications to bundle newer protocol features
into their messages that will be ignored by older versions of the framework.
Some of these features include:

* Allowing other services besides drivers to be specified in register/require
  tags
* Adding a "protocol" attribute to register, which determines the method of
  notifying the application (e.g. HTTP, HTTPS, XMPP)
* Allowing register/require tags to specify drivers by name instead of ID
* Commands to control drivers (restart, stop)
* A "status" tag that will request an update containing a bundle of information
  about the framework






