Designing Web Interfaces
=======================================

Speed and Latency Issues
------------------------

The simplest way to send and receive messages through a web application (using a
server-side script) has some limitations that become obvious fairly quickly.
Even with a fast computer and internet connection, the time it takes to make a
new connection to an XMPP server is usually several seconds. Once the
connection is ready, however, messages can be sent very quickly. This means that
there is a huge performance advantage for an application to stay connected to
the server. There are two ways to achieve this:

* Start a daemon process on the server that holds a connection, and send
  messages through it using some kind of RPC call.

* Make a client-side connection with Javascript, and occasionally synchronize
  with the server-side code if necessary.

Each have their own pros and cons. The daemon process method is more complicated,
and adds another layer of complexity to the application, but can be re-used for
other applications, and has a much wider range of uses. The Javascript solution,
on the other hand, is trivial to set up, but requires a web browser to operate.
In other words, it can't do anything in the background, because it requires the
user interface to be "running".

Another downside to the Javascript solution is the problem of cross-site
scripting. Most modern web browsers prevent client-side scripts from connecting
to other domains or web services. This causes a problem for XMPP client scripts,
since the server they connect to is frequently located on a different domain or
port. Common workarounds for this include running a web proxy that forwards any
requests to the XMPP server, and using Flash to provide an alternate means of
communication.

Connecting Web Apps to Platforms
--------------------------------

Once you have a Turk platform running, and a couple of applications to use with
it, the next step is to reliably connect them together. Depending on the usage,
it may be a good idea to use a separate XMPP account (JID) for each application.
XMPP servers have different policies regarding multiple clients using the same
account, and some may refuse access in such a situation. It is also possible to
connect as a specific *resource*, which allows for multiple connections to the
same JID, as long as the resource names are different.

The next step is to work out the mechanics of receiving updates from drivers.
Applications need to have a URL for the platform to send updates to, and have to
register to receive updates with the drivers they use. This can be done whenever
the UI is opened, or just on a regular interval. The framework will ignore any
identical register requests, so it is better to err on the side of caution.


