import SimpleHTTPServer
import SocketServer
from optparse import OptionParser
import webbrowser
import os.path

parser = OptionParser()
parser.add_option("-p","--port", dest="port", default = 8000, help = "Port to listen on.")
parser.add_option("-d","--docroot", dest="docroot", default = "", help = "A path representing the docroot. If present in a request, it will be stripped.")
(options, args) = parser.parse_args()

PORT = options.port
PREFIX = options.docroot

class SimpleHTTPRequestPrefixableHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_GET(self):
        print self.path
        self.path = self.path.replace(PREFIX, "")
        if not os.path.isfile(self.path[1:]):
            self.path = "/static/js"+self.path
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

Handler = SimpleHTTPRequestPrefixableHandler

httpd = SocketServer.TCPServer(("", PORT), Handler)
print "serving at port", PORT
httpd.serve_forever()



