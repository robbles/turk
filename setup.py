__author__="Rob O'Dwyer"
__date__ ="$Mar 09, 2010 5:34:40 PM$"

from setuptools import setup,find_packages

setup (
    name = 'Turk',
    version = '0.1',
    packages = find_packages(),

    install_requires=['twisted', 'pyserial', 'PyYAML', 'wokkel'],

    author = 'Rob O\'Dwyer',
    author_email = 'odwyerrob@gmail.com',

    summary = 'Turk - the framework for interfacing applications and devices with the web',
    url = 'http://github.com/robbles/turk',
    license = 'MIT',
    long_description= """
Turk - the software framework for interfacing applications and devices to the
Turk Web Interface.  Using XMPP (Jabber) IM accounts and the simple Turk XMPP
protocol, this framework lets you create and automatically run simple plugins
that interface devices and desktop software to web applications. Includes
built-in support for interfacing to Digi XBee modules, serially connected
Arduinos or similar microcontroller devices, and MIDI instruments.

NOTE: You need dbus and python-dbus installed to use this. If there's no precompiled package for your system, get them from:
http://www.freedesktop.org/wiki/Software/dbus
http://dbus.freedesktop.org/releases/dbus-python/
""",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Natural Language :: English',
        'Topic :: Internet',
        'Topic :: Home Automation',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],

    entry_points = {
        'console_scripts': [
            'turkctl = turk.turkctl:main',
        ],
        'gui_scripts': []
    }

)

