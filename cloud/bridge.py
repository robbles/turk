#!/usr/bin/env python
# encoding: utf-8
"""
untitled.py

Created by Rob O'Dwyer on 2009-10-08.
Copyright (c) 2009 Turk Innovations. All rights reserved.
"""

import sys
import os
from urllib2 import urlopen
from xml.dom.minidom import parseString

#TURK_CONFIG_SERVER = 'http://config.turkinnovations.com/%s'
TURK_CONFIG_SERVER = 'http://localhost/%s'
# Time in seconds between each server poll
POLL_DELAY = 10

class Bridge(object):
    """
    Periodically checks the Turk server for updates to configuration, running apps, etc.
    Also sends any relevant platform or app data to the server for processing.
    """
    def __init__(self, poll_delay=POLL_DELAY):
        self.poll_delay = poll_delay
        
    def run(self):
        while 1:
            newconfig = fetch_data()
            if newconfig:
                self.config = newconfig
            time.sleep(self.poll_delay)
            
    def fetch_data(self):
        try:
            raw_config = urlopen(TURK_CONFIG_SERVER % 'config/all.xml')
            config = parseString(raw_config)
        except Exception, e:
            print 'Failed to fetch config:', e
            return None
        
        
class AppConfig(object):
    """
    Allows apps to easily query their configuration based on the most recently fetched data
    """
    def __init__(self, app_id):
        # Get the config from the recently fetched server data
    def refresh(self):
        pass
    def __getitem__(self, key):
        return 'a config item'


def run():
	pass


if __name__ == '__main__':
	run()

