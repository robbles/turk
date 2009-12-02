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
from time import sleep

#TURK_CONFIG_SERVER = 'http://config.turkinnovations.com/%s'
TURK_CONFIG_SERVER = 'http://localhost:8888/%s'
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
        while True:
            newconfig = self.fetch_data()
            if newconfig:
                self.config = newconfig
            sleep(self.poll_delay)
            
    def fetch_data(self):
        """
        GETs the configuration data for this Turk platform from the server. Parses the
        XML into a dictionary form for easy querying by Apps/Devices later on. 
        """
        try:
            print 'fetching', TURK_CONFIG_SERVER % 'config/all.xml'
            raw_config = urlopen(TURK_CONFIG_SERVER % 'config/all.xml').read()
            config = parseString(raw_config)
        except Exception, e:
            print 'Failed to fetch config:', e
            return None
         
    def convert_XML(xml_node, storage={}):
        """ Converts the XML DOM tree into a dictionary format"""
        if xml_node.nodeName not in storage:
            storage[xml_node.nodeName] = 
        
        
        
class AppConfig(dict):
    """
    Allows apps to easily query their configuration based on the most recently fetched data
    """
    _apps = {}
    def __new__(cls, app_id=None):
        """
        If app_id is given, try to return the configuration for that app. Otherwise,
        construct a new AppConfig ready to be constructed with XML data.
        """
        if app_id:
            return AppConfig._apps[app_id]
        else:
            return dict.__new__(cls, app_id)
            
    def refresh(self):
        pass
        
    def __getitem__(self, key):
        return 'a config item'


def run():
	bridge = Bridge()
	bridge.run()


if __name__ == '__main__':
	run()

