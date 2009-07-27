#! /usr/bin/python

import os
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
import cgi
from sqlite3 import dbapi2 as sqlite
from xml.dom.minidom import parseString
import string
import xmlrpclib


MAPPER_ADDR = 'http://localhost:44000'

class CloudBridge:
    """
    Allows access to other Turk systems daemons through HTTP requests, and 
    periodically provides the Turk cloud with information about connected gadgets,
    current mappings, and system status

    Includes a synchronous handler for HTTP requests ( from local web interfaces / gadgets )
    """

    def __init__(self, basedir, server_port):
        """
        basedir -- The main Turk Core directory. Should contain a webif folder
            with all html/css/images if served by this program
        server_port -- the port to start the HTTP server on
        """
        self._basedir = basedir
        self._server_port = server_port
        self.db = sqlite.connect('mappings.db')
        self.mapper = xmlrpclib.ServerProxy(MAPPER_ADDR)
        # Now that the sqlite connection is open, move to the webif directory
        # so that the stupidly-designed interface to SimpleHTTPHandler works properly
        os.chdir('./webif')
        self.http_server = HTTPServer(('', server_port), BridgeHTTPHandler)

    def run(self):
        self.http_server.serve_forever()

    def get_device_list(self):
        """ Returns the list of devices and their inputs/outputs """
        return self.db.execute('select * from devices').fetchall()

    def get_mapping_list(self):
        """ Returns all currently active mappings """
        return self.db.execute('select input_device,input_name,output_device,output_name from mappings').fetchall()

    def add_mapping(self, input_device, input_name, output_device, output_name):
        """ Adds a new mapping to the database """
        print "add_mapping called"
        # Do the mapping through the mapping daemon to ensure consistency
        self.mapper.make_mapping(input_device, input_name, output_device, output_name)
        print "mapping added!"

    def remove_mapping(self, input_device, input_name, output_device, output_name):
        """ Removes a specific mapping from the database """
        self.db.execute("""delete from mappings where input_device=? and input_name=? and output_device=?
                           and output_name=?""",(input_device, input_name, output_device, output_name))
        print('deleted a mapping!')

    def remove_all_mappings(self, device, name):
        self.db.execute("""delete from mappings where input_device=? and input_name=?""", (device, name))
        self.db.execute("""delete from mappings where output_device=? and output_name=?""", (device, name))



class BridgeHTTPHandler(SimpleHTTPRequestHandler):
    """
    An HTTP handler for the cloud bridge that is used by the Web Interface.
    Since it runs a basic webserver in 'webif/' and exports data in XML and JSON, it can
    be used to build alternative user interfaces to the platform.

    NOTE: do_GET is handled by SimpleHTTPRequestHandler, this just defines do_POST
    """
    #TODO: Actually support JSON ;P
    #TODO: Return the web interface as XML, and use an XSLT stylesheet defined in the request

    def do_POST(self):
        # Parse the form data posted
        form = cgi.FieldStorage(fp=self.rfile, 
                                headers=self.headers,
                                environ={'REQUEST_METHOD':'POST',
                                         'CONTENT_TYPE':self.headers['Content-Type']})

        #self.wfile.write('Client: %s\n' % str(self.client_address))
        print '\n\n[POST]: Path: %s' % self.path

        print form

        try:
            # Send back an xhtml-formatted list of devices
            if self.path.endswith('/devices'):
                print 'Request for current devices received - sending back listing'
                self.send_response(200)
                self.end_headers()
                self.wfile.write(self.get_devices())

            # Send back an xhtml-formatted list of device IO mappings
            elif self.path.endswith('/mappings'):
                print 'Request for current device mappings received'
                self.send_response(200)
                self.end_headers()
                mappings = self.get_mappings().next()
                print 'sending \'%s\'' % mappings
                self.wfile.write(mappings)

            elif self.path.endswith('/map'):
                print 'Request for new device mapping received'
                print 'input: %s.%s' % (form['input_device'].value, form['input_name'].value)
                print 'output: %s.%s' % (form['output_device'].value, form['output_name'].value)
                self.send_response(200)
                self.end_headers()
                bridge.add_mapping(int(form['input_device'].value),
                                   form['input_name'].value,
                                   int(form['output_device'].value),
                                   form['output_name'].value)

            elif self.path.endswith('/unmap'):
                print 'Request to remove device mapping received'
                print 'device: %s  name: %s' % (form['device'].value, form['name'].value);
                bridge.remove_all_mappings(int(form['device'].value), form['name'].value);
                self.send_response(200)
                self.end_headers()

        except Exception, e:
            print e


    def get_devices(self):
        """
        Fetches a list of the current active devices from CloudBridge and formats in XHTML
        """
        devices = bridge.get_device_list()
        return ''.join([''.join(list(device_xml2xhtml(parseString(device[2]).firstChild, device[0], device[1]))) for device in devices])


    def get_mappings(self, mappings=0):
        """
        Fetches the list of current mappings and returns as xml.
        This is a generator function, so next() should be used
        """
        # Converts SQL result into xml <mappinglist>
        if mappings != 0:
            yield '<mappinglist>'
            for mapping in mappings:
                yield mapping_template.substitute(input_device=mapping[0],
                                                  input_name=mapping[1],
                                                  output_device=mapping[2],
                                                  output_name=mapping[3])
            yield '</mappinglist>'

        # Calls itself and turns all mappings into one big string
        else:
            mappings = bridge.get_mapping_list()
            yield ''.join(self.get_mappings(mappings))



""" Mapping template """
mapping_template = string.Template("""<mapping><input id="${input_device}" name="${input_name}" /><output id="${output_device}" name="${output_name}" /></mapping>""")


# Translating xml data to XHTML for browser awesomeness
device_template = string.Template("""<div class="device" id="${device_id}"><div class="deviceheader"><div class="devicename">${device_name}</div><div class="device_id">${device_id}</div></div><div class="deviceIO">""")

input_template = string.Template("""<div class="deviceinput"><div class="inputname ${name}">$name</div></div>""")
output_template = string.Template("""<div class="deviceoutput"><div class="outputname ${name}">$name</div></div>""")

def device_xml2xhtml(node, device_id=None, device_name=None):
    if node.nodeName == 'interfaces':
        yield device_template.substitute(locals())
        for child in node.childNodes:
            for translated in device_xml2xhtml(child):
                yield translated
        yield '</div></div>'
    elif node.nodeName == 'input':
        yield input_template.substitute(name=node.getAttribute('name'))
    elif node.nodeName == 'output':
        yield output_template.substitute(name=node.getAttribute('name'))
    return








# Start a single global CloudBridge instance, but don't automatically start it yet
bridge = CloudBridge('./', 8080)


if __name__ == '__main__':
    print 'Starting cloudbridge server...'
    bridge.run()









