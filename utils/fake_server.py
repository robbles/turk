#!/usr/bin/env python
# encoding: utf-8
"""
fake_server.py

Created by Rob O'Dwyer on 2009-10-09.
Copyright (c) 2009 Turk Innovations. All rights reserved.
"""

import os, sys
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

class FakeServer(SimpleHTTPRequestHandler):
    def do_POST(self):
        """
        Treat all POST requests the same as GET requests, so that
        filesystem in 'REST' is exposed through POST
        """
        print 'POST for %s' % self.path
        self.do_GET()
    
    def list_directory(self, path):
        """
        Serve index.xml files instead of directory listing
        """
        self.path = self.path + 'index.xml'
        print self.path
        if(os.path.exists(self.path[1:])):
            print 'found %s' % self.path
            return self.send_head()
        else:
            self.send_error(404, "No index file")

def main():
    # Change to 'REST' directory
    path, file = os.path.split(sys.argv[0])
    os.chdir((path + '/REST' if path else 'REST'))
    
    http_server = HTTPServer(('localhost', 8888), FakeServer)
    http_server.serve_forever()

if __name__ == '__main__':
    main()



