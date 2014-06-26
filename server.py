__author__ = 'Francholi'

import socket
import threading
import SocketServer

class RequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        data = self.request.recv(1024)
        print "Message from client: "+data
        cur_thread = threading.current_thread()
        print "Thread" + str(cur_thread)
        response = "Hello from server: " + str(cur_thread.name)
        self.request.sendall(response)

class Server(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

if __name__=="__main__":
    myServer = Server(('127.0.0.1', 2357), RequestHandler)
    server_thread = threading.Thread(target=myServer.serve_forever)
    server_thread.start()



