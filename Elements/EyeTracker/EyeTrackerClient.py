from panda3d.core import *

from Utils.Debug import printOut
from Utils.Utils import enum
from Elements.Element.Element import *
from Logger import Logger

# Basic protocol to communicate with the Eye Tracker
# message from Client to EyeTracker server
CLIENT_MSG_ID = enum(
	DUMMY_MSG		= 0,
	START_CALIB		= 1,
	STOP_CALIB		= 2,
	ADD_CALIB_POINT	= 3,
	REM_CALIB_POINT = 4,
	START_TRACKING  = 5,
	STOP_TRACKING   = 6,
    GET_STATUS      = 7,
    REM_LAST_CALIB_POINT = 8,
    SAVE_CALIB = 9,
    LOAD_CALIB = 10,
)
# message from Eyetracker Server to Client
SERVER_MSG_ID = enum(
	DUMMY_MSG = 0,
	OK        = 1,
	ERR       = 2,
	GAZE_DATA = 4,
    TRACKER_STATUS = 5
)

TRACKER_STATUS = enum(
    DISCONNECTED    = 0,
    CONNECTED       = 1,
    CALIBRATING     = 2,
    TRACKING        = 3,
)

CLIENT_STATUS = enum(
    CALIBRATING = 0,
    TRACKING = 1,
    NONE = 2
)
CLIENT_STATUS_STR = {CLIENT_STATUS.CALIBRATING:'CALIBRATING',
                     CLIENT_STATUS.TRACKING:'TRACKING',
                     CLIENT_STATUS.NONE:'NONE'}

class EyeTrackerClient(Element):
    def __init__(self, **kwargs):
        """
        Basic empty constructor for an EyeTracakerClient class
        :param kwargs: list
        :return: None
        """
        if getattr(self, "defaults", None) is None:
            self.defaults = {}
        # setting logGaze before constructing Element, so it will
        # end up in self.config.logGaze == True
        self.defaults["logGaze"] = True

        # call Element constructor
        super(EyeTrackerClient, self).__init__(**kwargs)

        # this is not a visible element!!!
        self.hideElement()

        """ constructor for the EyeTracker class """
        self.status = TRACKER_STATUS.DISCONNECTED
        # gazeData is a list of triplets (timeStamp, x, y)
        if (getattr(self.config,"smoothWindow",None) == None):
            self.config.smoothWindow = 5.0
        else:
            self.config.smoothWindow = float(self.config.smoothWindow)
        self.gazeData = [(0,0,0)] * int(self.config.smoothWindow)
        self.smoothSampleXY = [0.0,0.0]

        if self.config.logGaze:
            # one gaze log per participant
            self.gazeLogger = Logger(self.baseTime, "run/gazeData_"+self.config.world.participantId+".log",mode='w')
        else:
            self.gazeLogger = Logger(self.baseTime, "noLog")
        self.gazeLogger.startLog()

        # create a mutex for accessing the gazeData list
        self.gazeMutex = Mutex('gazeMutex')

        gazeTex = loader.loadTexture('Elements/Game/models/textures/outter_circle.png')
        gazeTex.setMinfilter(Texture.FTLinearMipmapLinear)
        gazeTex.setAnisotropicDegree(2)

        gazeNode = loader.loadModel("Elements/Game/models/plane")
        gazeNode.reparentTo(self.hudNP)
        gazeNode.setScale(0.1,1.0,0.1)
        gazeNode.setTransparency(1)
        gazeNode.setAlphaScale(0.1)
        gazeNode.setTexture(gazeTex)
        gazeNode.setPos(-1.7,0,0)
        self.gazeNode = gazeNode
        cam = self.config.world.getCamera()
        w,h = map(float,(cam.screenWidth,cam.screenHeight))
        self.normX = w/h
        self.hudNP.setBin('fixed',10)


    def getLastSampleAndTime(self, smooth=False):
        """
        Get last tracker sample, for now no smoothing or filter is applied
        :param smooth: Bool
        :return: (float,float) or None
        """
        return None

    def toggleGaze(self):
        print "toggle!"
        if self.gazeNode.isHidden():
            self.config.showGaze = True
            self.showGaze()
        else:
            self.config.showGaze = False
            self.hideGaze()

    def showGaze(self):
        self.gazeNode.show()

    def hideGaze(self):
        self.gazeNode.hide()

    def getLastSample(self, smooth=True):
        """
        Get last tracker sample, for now no smoothing or filter is applied
        :param smooth: Bool
        :return: (float,float) or None
        """
        value = (-1,-1)
        self.gazeMutex.acquire()
        if smooth:
            value = self.smoothSampleXY
        else:
            value = self.gazeData[-1][-2:]
        self.gazeMutex.release()
        return value


    def appendSample(self, timestamp, x, y):
        s = self.config.smoothWindow
        self.gazeMutex.acquire()
        self.gazeData.append((timestamp,x,y))
        # discard oldest, add new.
        self.smoothSampleXY[0] +=(-self.gazeData[-int(s+1)][1]/s) + (x/s)
        self.smoothSampleXY[1] +=(-self.gazeData[-int(s+1)][2]/s) + (y/s)
        self.gazeMutex.release()

    def startTracking(self):
        pass

    def stopTracking(selfs):
        pass

    def startCalibration(self):
        pass

    def stopCalibration(self):
        pass

    def addCalibrationPoint(self, x, y):
        pass

    def removeCalibrationPoint(self, x, y):
        pass

    def connect(self):
        """
        Implemented in subclass
        :return:
        """
        pass

    def disconnect(self):
        """
        Implemented in subclass
        :return:
        """
        pass

    def enterState(self):
        super(EyeTrackerClient, self).enterState()
        self.gazeLogger.logEvent("INFO - Starting EyeTracker client\n")
        if not self.config.showGaze:
            self.gazeNode.hide()

    def exitState(self):
        self.gazeLogger.logEvent("INFO - Closing EyeTracker client\n")
        self.gazeLogger.stopLog()
        super(EyeTrackerClient, self).exitState()

