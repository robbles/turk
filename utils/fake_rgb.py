#!/usr/bin/python

from BaseHTTPServer import HTTPServer
from BaseHTTPServer import HTTPRequestHandler

class RGB_Display(object):
    def __init__(self, color):
        self.color = color
        self.driverport = None

    def get_color(self):
        return self.color


RGB = RGB_Display((255, 255, 255))

color_page = string.Template("""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<meta http-equiv="pragma" content="no-cache">
<html>
<body>
<div style="width:100%;height:100%;margin:0px;background-color:rgb($color);">&nbsp;</div>
</body>
</html>
""")

class HTTPHandler(HTTPRequestHandler):
    def do_GET(self):
        global color_page
        self.send_response(200)
        self.wfile.write(color_page.substitute(color=self.get_color()))

    def get_color(self):
        global RGB
        colors = RGB.get_color()
        return "%d, %d, %d" % colors

