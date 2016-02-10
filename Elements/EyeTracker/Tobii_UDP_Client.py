from Elements.EyeTracker.EyeTrackerClient import *
from panda3d.core import *
from direct.task import Task
import socket
import time
from ast import literal_eval
from Utils.Debug import *
from struct import *


CLIENT_STATUS = enum(
    START_CALIBRATION = 0,
    STOP_CALIBRATION = 1,
    WAIT_START_CALIBRATION = 2,
    WAIT_STOP_CALIBRATION = 3,
    CALIBRATING = 4,
    START_TRACKING = 5,
    WAIT_START_TRACKING = 6,
    STOP_TRACKING = 7,
    WAIT_STOP_TRACKING = 8,
    TRACKING = 9,
    WAIT_ADD_POINT = 10,
    WAIT_REM_POINT = 11,
    NONE = 12
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

    # eye tracker messages
    def startTracking(self):
        if self.clientStatus != CLIENT_STATUS.NONE:
            print "Client must be in NONE state to start tracking."
            return
        self.clientStatus = CLIENT_STATUS.START_TRACKING
    def stopTracking(self):
        if self.clientStatus != CLIENT_STATUS.TRACKING:
            print "Client must be in TRACKING state to stop tracking."
            return
        self.clientStatus = CLIENT_STATUS.STOP_TRACKING
    def startCalibration(self):
        if self.clientStatus != CLIENT_STATUS.NONE:
            print "client must in NONE state to start calibrating"
            return
        self.clientStatus = CLIENT_STATUS.START_CALIBRATION

    def stopCalibration(self):

        if self.clientStatus != CLIENT_STATUS.CALIBRATING:
            print "client must in CALIBRATING state to stop calibration"
            return
        self.clientStatus = CLIENT_STATUS.STOP_CALIBRATION

    def addCalibrationPoint(self,x,y):
        if self.clientStatus == CLIENT_STATUS.CALIBRATING:
            print "adding calibration point at: %f,%f" % (x,y)
            # send a message id, and two doubles
            msg = '' + pack('bdd',CLIENT_MSG_ID.ADD_CALIB_POINT,x,y)
            self.udpServerSocket.send(msg)
            self.clientStatus = CLIENT_STATUS.WAIT_ADD_POINT
        elif self.clientStatus == CLIENT_STATUS.WAIT_ADD_POINT:
            print "waiting for previous calibration point to be added"
            print "last calibration point has been lost!"
        else:
            print "not in calibration state, current state:",self.clientStatus

    def removeCalibrationPoint(self,x,y):
        if self.clientStatus == CLIENT_STATUS.CALIBRATING:
            print "removing calibration point at: %f,%f" % (x,y)
            # send a message id, and two doubles
            msg = '' + pack('bdd',CLIENT_MSG_ID.REM_CALIB_POINT,x,y)
            self.udpServerSocket.send(msg)
            self.clientStatus = CLIENT_STATUS.WAIT_REM_POINT

    def removeLastCalibrationPoint(self):
        if self.clientStatus == CLIENT_STATUS.CALIBRATING:
            print "removing last calibration point at server"
            # send a message id, and two doubles
            msg = '' + pack('b',CLIENT_MSG_ID.REM_LAST_CALIB_POINT)
            self.udpServerSocket.send(msg)
            self.clientStatus = CLIENT_STATUS.WAIT_REM_POINT

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
        if self.clientStatus is CLIENT_STATUS.NONE:
            return Task.cont

        if self.clientStatus is CLIENT_STATUS.TRACKING:
            # listen for gaze data, 24 bytes! (long long, double, double)
            try:
                data, addr = self.udpGazeSocket.recvfrom(100)
                if len(data)>0:
                    # fucking unpack returns always a TUPLE!!!
                    print 'received sample!'
                    timestamp,x,y  = unpack('Qdd', data)
                    #self.appendSample(timestamp,x,y)
                    print timestamp,x,y
            except socket.timeout,te:
                # sleep 1 millisecond
                # print te
                time.sleep(0.1)
            return Task.cont

        if self.clientStatus is CLIENT_STATUS.START_CALIBRATION:
            print 'start calibration message received'
            # send message and wait for OK
            msg = '' + pack('b',CLIENT_MSG_ID.START_CALIB)
            self.udpServerSocket.send(msg)
            self.clientStatus = CLIENT_STATUS.WAIT_START_CALIBRATION
            return Task.cont

        if self.clientStatus is CLIENT_STATUS.WAIT_START_CALIBRATION:
            printOut('Waiting for eye-tracker to start calibration',2)
            try:
                data,addr = self.udpServerSocket.recvfrom(100)
                res = unpack('b',data[0])[0]
                if res == SERVER_MSG_ID.OK:
                    self.clientStatus = CLIENT_STATUS.CALIBRATING
                else:
                    # one byte, one string
                    code, err = unpack('bs', data)
                    printOut("Error from the server: " + err,1)
                    self.clientStatus = CLIENT_STATUS.NONE
            except socket.timeout,te:
                # print te
                time.sleep(0.1)
            return Task.cont

        if self.clientStatus is CLIENT_STATUS.CALIBRATING:
            return Task.cont

        if self.clientStatus is CLIENT_STATUS.WAIT_REM_POINT:
            try:
                data,addr = self.udpServerSocket.recvfrom(100)
                res = unpack('b',data[0])[0]
                if res == SERVER_MSG_ID.OK:
                    self.clientStatus = CLIENT_STATUS.CALIBRATING
                else:
                    #code, err = unpack('bs', data)
                    printOut("Error trying start calibration on server",1)
                    #printOut(err,1)
                    #self.clientStatus = CLIENT_STATUS.NONE
            except socket.timeout,te:
                # print te
                time.sleep(0.01)
            return Task.cont

        if self.clientStatus is CLIENT_STATUS.WAIT_ADD_POINT:
            try:
                data,addr = self.udpServerSocket.recvfrom(100)
                # fucking unpack returns always a TUPLE!!!
                # expecting a single element
                res = unpack('b',data[0])[0]
                if res == SERVER_MSG_ID.OK:
                    self.clientStatus = CLIENT_STATUS.CALIBRATING
                else:
                    code, err = unpack('bs', data)
                    printOut("Error trying start calibration on server",1)
                    printOut(err,1)
                    self.clientStatus = CLIENT_STATUS.NONE
            except socket.timeout,te:
                # print te
                time.sleep(0.01)
            return Task.cont

        if self.clientStatus is CLIENT_STATUS.STOP_CALIBRATION:
            print 'stop calibration message received!'
            # send message and wait for OK
            msg = '' + pack('b',CLIENT_MSG_ID.STOP_CALIB)
            self.udpServerSocket.send(msg)
            self.clientStatus = CLIENT_STATUS.WAIT_STOP_CALIBRATION
            return Task.cont

        if self.clientStatus is CLIENT_STATUS.WAIT_STOP_CALIBRATION:
            print 'waiting for eye-tracker to stop calibration and compute it!'
            try:
                data,addr = self.udpServerSocket.recvfrom(100)
                # fucking unpack returns always a TUPLE!!!
                # expecting a single element
                res = unpack('b',data[0])[0]
                if res == SERVER_MSG_ID.OK:
                    self.clientStatus = CLIENT_STATUS.NONE
                else:
                    code, err = unpack('bs', data)
                    printOut("Error trying to stop calibration on server",1)
                    printOut(err,1)
                    self.clientStatus = CLIENT_STATUS.NONE
            except socket.timeout,te:
                # print te
                pass
                time.sleep(0.01)
            return Task.cont

        # connection with the eye-tracker is asynchronous, so we send the message
        # and wait for a message to come back that it is ok. On the other end,
        # the server sends a message to the tracker and gets called-back and replies
        # to this message.
        if self.clientStatus is CLIENT_STATUS.START_TRACKING:
            print 'start tracking'
            # send message and wait for OK
            msg = '' + pack('b',CLIENT_MSG_ID.START_TRACKING)
            self.udpServerSocket.send(msg)
            self.clientStatus = CLIENT_STATUS.WAIT_START_TRACKING
            return Task.cont

        # wait for message
        if self.clientStatus is CLIENT_STATUS.WAIT_START_TRACKING:
            print 'wait start tracking'
            # wait for OK message.
            # if it does not lock, it will just loop and come back here!
            try:
                data,addr = self.udpServerSocket.recvfrom(100)
                # fucking unpack returns always a TUPLE!!!
                # expecting a single element
                res = unpack('b',data[0])[0]
                if res == SERVER_MSG_ID.OK:
                    self.clientStatus = CLIENT_STATUS.TRACKING
                else:
                    # fucking unpack returns always a TUPLE!!!
                    code, err = unpack('bs', data)
                    printOut("Error trying start tracking on server",1)
                    printOut(err,1)
                    self.clientStatus = CLIENT_STATUS.NONE
            except socket.timeout,te:
                # print te
                time.sleep(0.01)
            return Task.cont

        # send message
        if self.clientStatus is CLIENT_STATUS.STOP_TRACKING:
            print 'stop tracking'
             # send message and wait for OK
            msg = '' + pack('h',CLIENT_MSG_ID.STOP_TRACKING)
            self.udpServerSocket.send(msg)
            self.clientStatus = CLIENT_STATUS.WAIT_STOP_TRACKING
            return Task.cont

        # wait for message
        if self.clientStatus is CLIENT_STATUS.WAIT_STOP_TRACKING:
            print 'wait stop tracking'
            # wait for OK message.
            # what ever happens...we will set CLIENT_STATUS.NONE
            try:
                data,addr = self.udpServerSocket.recvfrom(100)
                if len(data):
                    # fucking unpack returns always a TUPLE!!!
                    res = unpack('b',data[0])[0]
                    if res == SERVER_MSG_ID.OK:
                        self.clientStatus = CLIENT_STATUS.NONE
                    else:
                        code, err = unpack('bs', data)
                        printOut("Error trying to stop tracking on server",1)
                        printOut(err,1)
                        self.clientStatus = CLIENT_STATUS.NONE
            except socket.timeout,te:
                # print te
                time.sleep(0.01)
            return Task.cont

