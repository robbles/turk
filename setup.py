__author__="Rob O'Dwyer"
__date__ ="$Jan 28, 2010 5:34:40 PM$"

from setuptools import setup,find_packages

setup (
  name = 'Turk Core',
  version = '0.1',
  packages = find_packages(),

  install_requires=['twisted', 'pyserial', 'PyYAML', 'dbus'],

  author = 'Rob O\'Dwyer',
  author_email = 'odwyerrob@gmail.com',

  summary = 'Turk Core - the software framework for interfacing applications and devices to the Turk Web Interface Service',
  url = 'http://turkinnovations.com',
  license = 'GPL',
  long_description= """Turk Core - the software framework for interfacing applications and devices to the Turk Web Interface.
Once you have an account with turkinnovations.com (or another service using the Turk XMPP protocol), this framework lets you develop and
automatically run simple drivers that interface devices and applications to your web apps running in the cloud. Includes a variety of built-in
libraries for interfacing hardware, including Digi XBee modules, serially connected Arduinos or similar microcontroller devices, and MIDI instruments.
  """,

)
