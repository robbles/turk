#!/usr/bin/env python
# encoding: utf-8
"""
untitled.py

Created by Rob O'Dwyer on 2009-10-08.
Copyright (c) 2009 Turk Innovations. All rights reserved.
"""

import sys
import os
import time
from turkcore.runtime.bridge import AppConfig
from turkcore.runtime.mapper import MAPPER_ADDR
import xmlrpclib

APP_ID = 2
REQUIRED_DRIVERS = [6] # requires RGB Lamp

#def register_app(self, app_id, app_name, device_ids, app_addr):

def main():
	# Get config from the server
	configs = AppConfig(APP_ID)
	mapper = xmlrpclib.ServerProxy(MAPPER_ADDR)
    
	# Keep checking for new data from the server
	while 1:
	    time.sleep(5)
	    configs.refresh()
	    update_color(configs['red'], configs['green'], configs['blue'])


if __name__ == '__main__':
	main()

