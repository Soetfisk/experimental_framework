import socket
import time
from time import sleep

IP = '127.0.0.1'
PORT = 2345
BUFFER_SIZE = 128  # Normally 1024, but we want fast response

cli = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
count = 0
num = 0
mb = 0

baseT = time.time()
while 1:
    try:
        sleep(0.001)
        cli.sendto(str(num),(IP,PORT))
        num+=1
        #elapsed = time.time() - baseT
        #if count % 1<<20 == 0:
        #    mb+=1
        #    print mb
    except socket.error,e:
        print e
        break

print "Total sent: " + str(num)
cli.close()