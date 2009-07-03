#! /usr/bin/python

import socket
import os
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
import cgi
import pdb
from sqlite3 import dbapi2 as sqlite

class CloudBridge():
    """
    Allows access to other Turk systems daemons through HTTP requests, and 
    periodically provides the Turk cloud with information about connected gadgets,
    current mappings, and system status
    """
    def __init__(self):
        pass


class CloudBridgeHandler(SimpleHTTPRequestHandler):
    """
    Handler for HTTP requests ( from local web interfaces / gadgets )
    NOTE: do_GET is handled by SimpleHTTPRequestHandler, this just handles do_POST
    """

    def do_POST(self):
        # Parse the form data posted
        form = cgi.FieldStorage(
               fp=self.rfile, 
               headers=self.headers,
               environ={'REQUEST_METHOD':'POST',
                        'CONTENT_TYPE':self.headers['Content-Type']})

        #self.wfile.write('Client: %s\n' % str(self.client_address))
        print 'POST: Path: %s' % self.path

        # print out information about what was posted in the form
        try:
            if len(form):
                for key in form.keys():
                    print "    %s : \'%s\'" % (key, form[key].value)

            else:
                print "no content was sent"

            # Send back an xhtml-formatted list of devices
            if self.path == '/devices':
                print 'Request for current devices received - sending back listing'
                self.send_response(200)
                self.end_headers()
                f = open('devicecontent.html', 'rU')
                self.wfile.write(f.read())

            # Send back an xhtml-formatted list of device IO mappings
            elif self.path == '/mappings':
                print 'Request for current device mappings received'

        except Exception, e:
            print e


## End of CloudBridge Classes ##

if __name__ == '__main__':
    # Serve files out of the directory that contains webif data
    if not os.getcwd().endswith('webif'):
        os.chdir('webif')
    # Start a simple HTTP server at http://localhost:8080/
    server = HTTPServer(('localhost', 8080), CloudBridgeHandler)
    print 'Starting server, use <Ctrl-C> to stop'
    server.serve_forever()








