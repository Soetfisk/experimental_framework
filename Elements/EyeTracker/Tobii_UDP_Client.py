from Elements.EyeTracker.EyeTrackerClient import *
from panda3d.core import *
from direct.task import Task
import socket
import time
from ast import literal_eval
from Utils.Debug import *
from struct import *


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

        # call constructor, which in turn calls Element constructor
        super(Tobii_UDP_Client, self).__init__(**kwargs)

        # fill in some empty samples in case I am asked for samples right away
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
        self.seqNum = 0

    def toggleTracking(self):
        if self.clientStatus == CLIENT_STATUS.TRACKING:
            self.stopTracking()
        if self.clientStatus == CLIENT_STATUS.NONE:
            self.startTracking()

    def saveCalibration(self, filename):
        notValidStates = [CLIENT_STATUS.CALIBRATING,CLIENT_STATUS.NONE]
        if self.clientStatus in notValidStates:
            printOut("You cannot save the calibration if the tracker is in any of ")
            printOut(str(notValidStates))
            return
        else:
            msg = '' + pack('b',CLIENT_MSG_ID.SAVE_CALIB)
            # filename to save the calibration
            msg += filename
            self.udpServerSocket.send(msg)
            printOut("Saving calibration %s" % filename)

    def loadAndSetCalibration(self, filename):
        notValidStates = [CLIENT_STATUS.CALIBRATING,CLIENT_STATUS.NONE]
        if self.clientStatus in notValidStates:
            printOut("You cannot save the calibration if the tracker is in any of ")
            printOut(str(notValidStates))
            return
        else:
            msg = '' + pack('b',CLIENT_MSG_ID.LOAD_CALIB)
            # filename to load the calibration from
            msg += filename
            self.udpServerSocket.send(msg)
            printOut("Loading and setting calibration %s" % filename)

    def startTracking(self):
        if self.clientStatus != CLIENT_STATUS.NONE:
            print "Client must be in NONE state to start tracking."
            return

        msg = '' + pack('b',CLIENT_MSG_ID.START_TRACKING)
        self.udpServerSocket.send(msg)
        self.clientStatus = CLIENT_STATUS.TRACKING
        print "STARTING TRACKING."
        taskMgr.add( self.listenUdp, 'listenUdp', taskChain = 'listen_eyetracker' )

    def stopTracking(self):
        if self.clientStatus != CLIENT_STATUS.TRACKING:
            print "Client must be in TRACKING state to stop tracking."
            print "Client is in state: %d" % self.clientStatus
            return
        msg = '' + pack('b',CLIENT_MSG_ID.STOP_TRACKING)
        taskMgr.remove( 'listenUdp' )
        self.udpServerSocket.send(msg)
        self.clientStatus = CLIENT_STATUS.NONE
        print "STOPING TRACKING."

    def startCalibration(self):
        if self.clientStatus != CLIENT_STATUS.NONE:
            print "client must in NONE state to start calibrating"
            return
        self.gazeLogger.logEvent('Starting calibration')
        msg = '' + pack('b',CLIENT_MSG_ID.START_CALIB)
        self.udpServerSocket.send(msg)
        self.clientStatus = CLIENT_STATUS.CALIBRATING

    def stopCalibration(self):
        if self.clientStatus != CLIENT_STATUS.CALIBRATING:
            print "client must be in CALIBRATING state to stop calibration"
            return
        # stop and compute!
        self.gazeLogger.logEvent('Stoping calibration')
        msg = '' + pack('b',CLIENT_MSG_ID.STOP_CALIB)
        self.udpServerSocket.send(msg)
        self.clientStatus = CLIENT_STATUS.NONE

    def addCalibrationPoint(self,x,y):
        if self.clientStatus == CLIENT_STATUS.CALIBRATING:
            self.gazeLogger.logEvent("adding calibration point at: %f,%f" % (x,y))
            msg = '' + pack('bdd',CLIENT_MSG_ID.ADD_CALIB_POINT,x,y)
            self.udpServerSocket.send(msg)
        else:
            print "not in calibration mode, current state:",self.clientStatus
    def removeCalibrationPoint(self,x,y):
        if self.clientStatus == CLIENT_STATUS.CALIBRATING:
            self.gazeLogger.logEvent("removing calibration point at: %f,%f" % (x,y))
            msg = '' + pack('bdd',CLIENT_MSG_ID.REM_CALIB_POINT,x,y)
            self.udpServerSocket.send(msg)
        else:
            self.gazeLogger.logEvent("not in calibration mode, current state:",self.clientStatus)
    def removeLastCalibrationPoint(self):
        if self.clientStatus == CLIENT_STATUS.CALIBRATING:
            print "removing last calibration point at server"
            msg = '' + pack('b',CLIENT_MSG_ID.REM_LAST_CALIB_POINT)
            self.udpServerSocket.send(msg)

    def enterState(self):
        EyeTrackerClient.enterState(self)
        self.gazeLogger.writeln("# timestamp(us), gaze_pos(x,y)")
        # ONLY Establish socket connections, but does nothing with the EyeTracker.
        self.connectSockets()

    def exitState(self):
        # remove task, and close sockets.
        if self.clientStatus == CLIENT_STATUS.TRACKING:
            self.stopTracking()
        if self.clientStatus == CLIENT_STATUS.CALIBRATING:
            self.stopCalibration()
        taskMgr.remove('listenUdp')
        try:
            self.udpServerSocket.close()
            self.udpGazeSocket.close()
        except Exception,e:
            print e
        EyeTrackerClient.exitState(self)

    def listenUdp(self, t):
        if self.clientStatus is CLIENT_STATUS.TRACKING:
            try:
                # Format of a package coming from the UDP Server connected to the eye-tracker
                #
                # 8 bytes for timestamp                                  Q long long
                # 4 bytes for tracker_status ENUM                        B unsigned char
                # 4 bytes padding from Compiler                          B unsigned char
                # 88 bytes left eye in double3 double3 double3 double2   ddd ddd ddd dd
                # 88 bytes right eye in double3 double3 double3 double2  ddd ddd ddd dd
                # The 88 bytes are:
                #  struct tobiigaze_point_3d eye_position_from_eye_tracker_mm;
                #  struct tobiigaze_point_3d eye_position_in_track_box_normalized;
                #  struct tobiigaze_point_3d gaze_point_from_eye_tracker_mm;
                #  struct tobiigaze_point_2d gaze_point_on_display_normalized;

                data, addr = self.udpGazeSocket.recvfrom(192)
                if len(data)>0:
                    gaze_data  = unpack('QBB' + 2*(3*'ddd' + 'dd'), data)
                    left2D = (gaze_data[-13],gaze_data[-12])
                    right2D = (gaze_data[-2], gaze_data[-1])
                    avg = ((left2D[0]+right2D[0]) / 2.0 ,(left2D[1]+right2D[1]) / 2.0)

                    if gaze_data[1] == 0: # NO EYE DATA PRESENT
                        self.gazeLogger.logEvent("no eye data present")
                        return Task.cont
                    elif gaze_data[1] == 1: # BOTH EYES TRACKED
                        pass
                        # avg = (left2D[0]+right2D[0] / 2.0 ,left2D[1]+right2D[1] / 2.0)
                    elif gaze_data[1] in {2,3}: # LEFT EYE TRACKED
                        avg = (left2D[0] ,left2D[1])
                    elif gaze_data[1] in {5,6}: # RIGHT EYE TRACKED
                        avg = (right2D[0] ,right2D[1])
                    elif gaze_data[1] == 4:       # WE DONT KNOW
                        self.gazeLogger.logEvent('tracking one eye!, unknown which')
                        self.gazeLogger.logEvent('left X: ', left2D[0])
                        self.gazeLogger.logEvent('right X: ', right2D[0])

                    self.appendSample(data[0], avg[0], avg[1] )
                    last = self.getLastSample(smooth=True)
                    if self.config.showGaze:
                        self.gazeNode.setPos((last[0] * (2*self.normX) - self.normX), 0, - (last[1] * 2 - 1))
                else:
                    printOut("read something empty from UDP socket with Tobii_UDP_Client?",1)

            except socket.timeout,te:
                # sleep 10 millisecond, this is a 30hz eye-tracker!
                # print te
                self.gazeLogger.logEvent("No gaze data available")
                time.sleep(0.01)
        else:
            printOut('executing listenUdp whilst not tracking ?!?!, this seems like a bug!',1)
        return Task.cont

