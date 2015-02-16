from Elements.EyeTracker.EyeTrackerClient import EyeTrackerClient
from panda3d.core import *
import socket
import time
from ast import literal_eval


# @TODO Implement TCP client, protocol over TCP to connect to C Client,
# @TODO
# empty class
class Tobii_UDP_Client(EyeTrackerClient):

    def __init__(self, **kwargs):
        """
        Simply waits for UDP packets from the EyeTracker.
        :param kwargs: dict
        :return: None
        """
        if getattr(self, "defaults", None) is None:
            self.defaults = {}
        self.defaults["serverIp"] = "127.0.0.1"
        self.defaults["serverPort"] = 2345

        super(Tobii_UDP_Client, self).__init__(**kwargs)

        # fill in some empty samples in case I am asked for samples right away
        self.gazeData = [((0.0,0.0), 0)] * 20

    def connect(self):
        self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpSocket.bind( (self.config.serverIp, self.config.serverPort ) )
        self.udpSocket.settimeout(0.05)

        # create a task chain with ONE thread to listen for UDP packets
        taskMgr.setupTaskChain('listen_eyetracker', numThreads = 1, tickClock = None,
                       threadPriority = None , frameBudget = None,
                       frameSync = None, timeslicePriority = None)
        taskMgr.add( self.listenUdp, 'listenUdp', taskChain = 'listen_eyetracker' )

        self.seqNum = 0

    def disconnect(self):
        print "disconnecting"
        self.udpSocket.close()
        print "disconnecting after close"
        taskMgr.remove('listenUdp')
        print "after remove task"

    def startTracking(self):
        pass

    def stopTracking(self):
        pass

    def enterState(self):
        EyeTrackerClient.enterState(self)
        self.gazeLogger.writeln("GameTime, Gaze coords, timestamp in us")
        self.connect()
        self.startTracking()

    def exitState(self):
        self.stopTracking()
        self.disconnect()
        EyeTrackerClient.exitState(self)

    def listenUdp(self, t):
        try:
            data, addr = self.udpSocket.recvfrom(128)
            if data:
                gameTime = time.time()
                gazeSample, timestamp = literal_eval(data)
                self.gazeMutex.acquire()
                self.gazeData.append((gazeSample,timestamp))
                self.gazeMutex.release()
                self.gazeLogger.logEvent(data+'\n',gameTime)
        except socket.timeout, timeout:
            return t.cont
        except Exception, e:
            print e

        #if (self.seqNum != int(data)):
        #    print 'Missed package: ' + str(self.seqNum)
        #else:
        #    self.seqNum
        return t.cont

    def readGaze(self,samples=1):
        """
        Read the last 'samples' from the gaze data. At the begining there are only 20 empty samples
        :param samples: int
        :return: list
        """
        self.gazeMutex.acquire()
        temp = self.gazeData[-samples:]
        self.gazeMutex.release()
        return temp
