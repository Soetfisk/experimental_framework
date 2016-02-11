from Elements.EyeTracker.EyeTrackerClient import *
from panda3d.core import *
from direct.task import Task
import socket
import time
from ast import literal_eval
from Utils.Debug import *
from struct import *


CLIENT_STATUS = enum(
    CALIBRATING = 0,
    TRACKING = 1,
    NONE = 2
)

# @TODO Implement TCP client, protocol over TCP to connect to C Client,
# @TODO
# empty class
class Tobii_UDP_Client(EyeTrackerClient):
    def __init__(self, **kwargs):
        """
        Implements a simple communication protocol with the EyeTracker
        server listening on a UDP socket. It also has a dedicated UDP
        socket to receive gaze data.
        :param kwargs: dict
        :return: None
        """
        if getattr(self, "defaults", None) is None:
            self.defaults = {}
        self.defaults["serverIp"] = "127.0.0.1"
        self.defaults["serverPort"] = 2345
        self.defaults["gazeDataIp"] = "127.0.0.1"
        self.defaults["gazeDataPort"] = 5432

        super(Tobii_UDP_Client, self).__init__(**kwargs)

        # fill in some empty samples in case I am asked for samples right away
        self.gazeData = [((0.0,0.0), 0)] * 20

        self.clientStatus = CLIENT_STATUS.NONE
    def connectSockets(self):

        """
        Create two socket connections, one to talk to the EyeTracker server, one to
        only receive gaze data samples
        :return: None
        """
        self.udpServerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpServerSocket.settimeout(0.01)
        self.udpServerSocket.connect((self.config.serverIp, self.config.serverPort))

        self.udpGazeSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpGazeSocket.settimeout(0.1)
        self.udpGazeSocket.bind(('',5432))
        #self.udpGazeSocket.connect((self.config.gazeDataIp, self.config.gazeDataPort))

        # set address for recv_from and send_to automatically for the socket,
        # so it is not really "connecting", just the lazy programmer...
        #self.udpSocket.bind( (self.config.serverIp, self.config.serverPort ) )

        # create a task chain with ONE thread to listen for UDP messages
        taskMgr.setupTaskChain('listen_eyetracker', numThreads = 1, tickClock = None,
                       threadPriority = None , frameBudget = None,
                       frameSync = None, timeslicePriority = None)
        # This task will listen for protocol messages from the server and also for
        # gaze data in a single thread.
        taskMgr.add( self.listenUdp, 'listenUdp', taskChain = 'listen_eyetracker' )
        self.seqNum = 0
    def startTracking(self):
        if self.clientStatus != CLIENT_STATUS.NONE:
            print "Client must be in NONE state to start tracking."
            return

        msg = '' + pack('b',CLIENT_MSG_ID.START_TRACKING)
        self.udpServerSocket.send(msg)
        self.clientStatus = CLIENT_STATUS.TRACKING
    def stopTracking(self):
        if self.clientStatus != CLIENT_STATUS.TRACKING:
            print "Client must be in TRACKING state to stop tracking."
            return
        msg = '' + pack('b',CLIENT_MSG_ID.STOP_TRACKING)
        self.udpServerSocket.send(msg)
        self.clientStatus = CLIENT_STATUS.NONE
    def startCalibration(self):
        if self.clientStatus != CLIENT_STATUS.NONE:
            print "client must in NONE state to start calibrating"
            return
        msg = '' + pack('b',CLIENT_MSG_ID.START_CALIB)
        self.udpServerSocket.send(msg)
        self.clientStatus = CLIENT_STATUS.CALIBRATING
    def stopCalibration(self):
        if self.clientStatus != CLIENT_STATUS.CALIBRATING:
            print "client must be in CALIBRATING state to stop calibration"
            return
        # stop and compute!
        msg = '' + pack('b',CLIENT_MSG_ID.STOP_CALIB)
        self.udpServerSocket.send(msg)
        self.clientStatus = CLIENT_STATUS.NONE
    def addCalibrationPoint(self,x,y):
        if self.clientStatus == CLIENT_STATUS.CALIBRATING:
            print "adding calibration point at: %f,%f" % (x,y)
            msg = '' + pack('bdd',CLIENT_MSG_ID.ADD_CALIB_POINT,x,y)
            self.udpServerSocket.send(msg)
        else:
            print "not in calibration mode, current state:",self.clientStatus
    def removeCalibrationPoint(self,x,y):
        if self.clientStatus == CLIENT_STATUS.CALIBRATING:
            print "removing calibration point at: %f,%f" % (x,y)
            msg = '' + pack('bdd',CLIENT_MSG_ID.REM_CALIB_POINT,x,y)
            self.udpServerSocket.send(msg)
        else:
            print "not in calibration mode, current state:",self.clientStatus
    def removeLastCalibrationPoint(self):
        if self.clientStatus == CLIENT_STATUS.CALIBRATING:
            print "removing last calibration point at server"
            msg = '' + pack('b',CLIENT_MSG_ID.REM_LAST_CALIB_POINT)
            self.udpServerSocket.send(msg)

    def enterState(self):
        EyeTrackerClient.enterState(self)
        self.gazeLogger.writeln("GameTime, Gaze coords, timestamp in us")
        # ONLY Establish socket connections, but does nothing with the EyeTracker.
        self.connectSockets()
    def exitState(self):
        # self.stopTracking()
        # remove task, and close sockets.
        taskMgr.remove('listenUdp')
        self.udpServerSocket.close()
        self.udpGazeSocket.close()
        EyeTrackerClient.exitState(self)

    def listenUdp(self, t):
        if self.clientStatus is CLIENT_STATUS.TRACKING:
            # listen for gaze data, 24 bytes! (long long, double, double)
            try:
                # packages here should always be 24 bytes (timestamp long long, double x, double y)
                data, addr = self.udpGazeSocket.recvfrom(24)
                if len(data)>0:
                    timestamp,x,y  = unpack('Qdd', data)
                    # TODO: append samples!
                    # self.appendSample(timestamp,x,y)
                    print timestamp,x,y
            except socket.timeout,te:
                # sleep 10 millisecond, this is a 30hz eye-tracker!
                # print te
                time.sleep(0.01)
        return Task.cont

