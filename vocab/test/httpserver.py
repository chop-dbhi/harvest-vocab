import SimpleHTTPServer
import SocketServer
from optparse import OptionParser
import webbrowser

parser = OptionParser()
parser.add_option("-p","--port", dest="port", default = 8000, help = "Port to listen on.")
parser.add_option("-d","--docroot", dest="docroot", default = "", help = "A path representing the docroot. If present in a request, it will be stripped.")
(options, args) = parser.parse_args()

PORT = options.port
PREFIX = options.docroot

class SimpleHTTPRequestPrefixableHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.path = self.path.replace(PREFIX, "")
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

Handler = SimpleHTTPRequestPrefixableHandler

httpd = SocketServer.TCPServer(("", PORT), Handler)
print "serving at port", PORT
httpd.serve_forever()



