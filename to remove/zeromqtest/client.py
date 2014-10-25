import zmq

context = zmq.Context()

print "Connecting to server"
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")

for request in range(1000):
    print "sending request %s" % request
    socket.send(b"Hello")

    message = socket.recv()
    print "received message: %s" % message

