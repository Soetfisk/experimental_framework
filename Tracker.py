from direct.showbase.DirectObject import DirectObject

from Utils.Debug import printOut

from threading import Thread
from time import sleep
from Queue import *
from socket import socket,error,AF_INET,SOCK_STREAM
from time import time

# enum in Python
def enum(**enums):
    return type('Enum',(),enums)

class Tracker(DirectObject):
    """Tracker class, holding a TCP socket, and some knowledge
    about how to comunicate with the EyeWriter software"""

    def __init__(self, config=None):
        # create Queue to hold eye-gaze data
        self.eyeData = Queue()
        # config
        self.trackerLocation = ('127.0.0.1',9997)
        # tcp socket
        self.sock = socket(AF_INET, SOCK_STREAM)

        # enums extracted from CPP tracker code
        self.COM = enum(UNKNOWN_COMMAND='0',REG_EYE_DATA='1',UNREG_EYE_DATA='2',START_CALIBRATION=3,
                        ADD_CALIBRATION_PT='4',REMOVE_CALIBRATION_PT='5',STOP_CALIBRATION='6',START_TRACKING='7',
                        STOP_TRACKING='8',GET_WINDOW_SIZE='9')
        self.trackerWinSize = None
        self.logger = None

    def connect(self):
        """Connect to eyetracker TCP server"""
        loc=self.trackerLocation
        try:
            self.sock.connect(loc)
            printOut("Connection established with tracker",1)
        except error,se:
            printOut("Socket error",1)
            print se
        except Exception,e:
            printOut("Could not connect to tracker on %s:%s"%(loc[0],loc[1]),1)
            print e

    def track(self):
        """start reading gaze data from tracker"""
        try:
            # read the window size if possible
            self.sock.send(self.COM.GET_WINDOW_SIZE)
            # origin(X,Y), dimensions(W,H)
            X, Y, W, H = map(float, self.sock.recv(19).strip().split())
            self.trackerWinSize = (X,Y,W,H)

            # register to receive gaze data.
            self.sock.send(self.COM.REG_EYE_DATA)
            # OpenFrameworks uses this termination string for messages
            # but now I am using raw char functions
            #self.sock.send('[/TCP]')
            response = self.sock.recv(256)
            printOut("Respuesta del server: %s"%response,1)
            if ('OK' in response):
                # clear any old gaze data
                self.eyeData.queue.clear()
                taskMgr.add(self.readGazeData, "readGazeData")
            else:
                printOut("Tracker not responding to EyeDataCommand!",1)
        except Exception,e:
            printOut("Error starting the tracking",1)

    def stopTrack(self):
        """stop reading gaze data from tracker"""
        # 1 code means to REGISTER FOR EYE DATA
        # the tracker also expects a string '[/TCP]' to flag end
        # of message
        try:
            self.sock.send(self.COM.UNREG_EYE_DATA)
            # OpenFrameworks uses this termination string for messages
            # but now I am using raw char functions
            # self.sock.send('[/TCP]')
            response = self.sock.recv(256)
            printOut("Respuesta del server: %s"%response,1)
            if 'OK' in response:
                # clear any old gaze data
                self.eyeData.queue.clear()
                taskMgr.remove("readGazeData")
            else:
                printOut("Tracker not responding to EyeDataCommand!",1)
            self.sock.close()
        except Exception,e:
            printOut("Error stoping the tracking",1)

    def setLogger(self,logger):
        self.logger = logger

    def readGazeSample(self, mapping=None):
        """
        :return: None
        """
        if not mapping: mapping = [-1, 1, -1, 1]
        try:
            return self.eyeData.get_nowait()
        except Empty:
            printOut("TRACKER:: queue empty!", 0)
            return None

    def readGazeData(self,task, sort=1):
        '''Task to read data from the eye-tracker'''
        print "readGazeData task"
        try:
            # consume data from socket
            data = self.sock.recv(20)
            try:
                x, y = map(int, data.split(' '))

                # if we are consuming slower than the producer
                while self.eyeData.qsize() > 1:
                    printOut("WARNING, EYE TRACKER IS PRODUCING FASTER THAN WE CAN CONSUME",0)
                    printOut("DROPPING DATA",0)
                    drop = self.eyeData.get()
                # queue sample for thread-safe consumption
                self.eyeData.put((x,y))
            except ValueError,v:
                printOut("Error converting numeric values from EyeTracker: %s" % data,0)
            except Exception,e:
                print e

            return task.cont

        except Exception,e:
            printOut("Error reading from socket",1)
            print e
            return task.done
 

 
