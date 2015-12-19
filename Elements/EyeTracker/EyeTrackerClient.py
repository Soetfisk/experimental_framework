from panda3d.core import *

from Utils.Debug import printOut
from Utils.Utils import enum
from Element import *
from Logger import Logger

# Basic protocol to communicate with the Eye Tracker
CLIENT_MSG_ID = enum(
	DUMMY_MSG		= 0,
	INIT_TRACKER	= 1,
	START_CALIB		= 1<<1,
	STOP_CALIB		= 1<<2,
	ADD_CALIB_POINT	= 1<<3,
	REM_CALIB_POINT = 1<<4,
	START_TRACKING  = 1<<5,
	STOP_TRACKING   = 1<<6
)
SERVER_MSG_ID = enum(
	DUMMY_MSG = 0,
	OK        = 1,
	ERR       = 2,
	GAZE_DATA = 4
)
TRACKER_STATUS = enum(
    DISCONNECTED = 0,
    CONNECTED = 1,
    CALIBRATING = 2,
    TRACKING = 4,
)

class EyeTrackerClient(Element):
    def __init__(self, **kwargs):
        """
        Basic empty constructor for an EyeTracakerClient class
        :param kwargs: list
        :return: None
        """
        if getattr(self, "defaults", None) is None:
            self.defaults = {}
        self.defaults["logGaze"] = True

        super(EyeTrackerClient, self).__init__(**kwargs)

        # this is not a visible element.
        self.hideElement()

        """ constructor for the EyeTracker class """
        self.status = TRACKER_STATUS.DISCONNECTED
        # gazeData is (timeStamp, x, y)
        self.gazeData = []

        if self.config.logGaze:
            self.gazeLogger = Logger("run/gazeData_"+self.config.world.participantId+".log",mode='w')
        else:
            self.gazeLogger = Logger("noLog", mode='w')
        self.gazeLogger.startLog()

        # create a mutex for accessing the gazeData list
        self.gazeMutex = Mutex('gazeMutex')

    def getLastSampleAndTime(self, smooth=False):
        """
        Get last tracker sample, for now no smoothing or filter is applied
        :param smooth: Bool
        :return: (float,float) or None
        """
        return None

    def getLastSample(self, smooth=False, avg=1):
        """
        Get last tracker sample, for now no smoothing or filter is applied
        :param smooth: Bool
        :return: (float,float) or None
        """
        if self.status == TRACKER_STATUS.TRACKING:
            self.gazeMutex.acquire()
            return self.gazeData[-1][0]
            self.gazeMutex.release()
        else:
            return None

    def connect(self):
        pass

    def disconnect(self):
        pass

    def startTracking(self):
        pass

    def stopTracking(self):
        pass

    def enterState(self):
        super(EyeTrackerClient, self).enterState()
        self.gazeLogger.logEvent("INFO - Starting EyeTracker client\n")

    def exitState(self):
        self.gazeLogger.logEvent("INFO - Closing EyeTracker client\n")
        self.gazeLogger.stopLog()
        #if (getattr(self.config, 'logGaze', False)):
        #    self.saveGazeData()
        super(EyeTrackerClient, self).exitState()

