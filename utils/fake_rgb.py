#!/usr/bin/python

from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
import string
import random
import time
from threading import Thread
import struct
from socket import socket, AF_INET, SOCK_DGRAM
from turkcore.runtime.spawner import SPAWNER_PORT

class RGB_Display(Thread):
    def __init__(self, color):
        Thread.__init__(self)
        self.daemon = True
        self.color = color
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind(('', 0))

    def serve(self):
        """ Connect to Turk platform and listen for instructions from driver """
        initmsg = struct.pack('>QQ', 0x1122334455667788, 6)
        self.socket.sendto(initmsg, ('localhost', SPAWNER_PORT))
        
        while 1:
            driver_msg, driver_addr = self.socket.recvfrom(1024)
            try:
                if driver_addr[1] == 2:
                    device_addr, driver_id = struct.unpack('>QQ', driver_msg)
                    print 'Fake RGB: got an init message from driver %d' % driver_id
                elif driver_addr[1] == 3:
                    device_addr, red, green, blue = struct.unpack('>QBBB', driver_msg)
                    self.color = (red, green, blue)
                    print 'Fake RGB: driver set color to rgb(%d, %d, %d)' % self.color
                else:
                    print 'Fake RGB: got an unknown Turk packet, ignoring...'
            except Exception:
                continue


    def run(self):
        """ Cycle colors when not being controlled externally """
        while 1:
            time.sleep(1)
            self.color = tuple([max(0, min(255, (c + random.randint(-2, 2)))) for c in self.color])

    def get_rand_color(self):
        return [random.getrandbits(8) for i in range(3)]

    def get_color(self):
        return tuple(self.color)

    def set_color_rgb(self, red, green, blue):
        for color in (red, green, blue):
            if not isinstance(color, int) or not (0<=color<=255):
                raise TypeError('Color values must be 8 bit integers')
        self.color = (red, green, blue)





color_page = string.Template("""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<head>
<meta http-equiv="refresh" content="1">
<meta http-equiv="pragma" content="no-cache">
<style type="text/css">
body { margin:0px;padding:0px;background:#000000; }
.color { width:800px;height:516px;margin:0 auto;background-color:rgb($color); }
</style>
</head>
<html>
<body>
<div class="color"><img src="wall_lamp.png" /></div>
</body>
</html>
""")

class RGB_HTTPHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.serve_page()
        else:
            SimpleHTTPRequestHandler.do_GET(self)

    def serve_page(self):
        self.send_response(200)
        self.wfile.write(color_page.substitute(color=self.get_color()))

    def get_color(self):
        global RGB
        return '%d, %d, %d' % RGB.get_color()

if __name__ == '__main__':
    import os, sys
    path, file = os.path.split(sys.argv[0])
    if path:
        os.chdir(path)
    # Start HTTP server to show current color
    http_server = HTTPServer(('', 0), RGB_HTTPHandler)
    print 'starting HTTP server on', http_server.socket.getsockname() 
    os.system('echo %d | pbcopy' % http_server.socket.getsockname()[1])
    http_server_thread = Thread(target=http_server.serve_forever)
    http_server_thread.daemon = True
    http_server_thread.start()

    RGB = RGB_Display((0, 0, 255))
    # Start cycling colors automatically
    RGB.start()

    # Talk to Turk Platform
    RGB.serve()





