from Utils.Debug import printOut
from Utils.Utils import enum
from Element import *

# Basic protocol to communicate with the Eye Tracker
TRACKER_MSG = enum(CONNECT=0, DISCONNECT=1, START_TRACKING=2, STOP_TRACKING=3)

# empty class
class EyeTrackerClient(Element):
    def __init__(self, **kwargs):

        super(EyeTrackerClient, self).__init__(**kwargs)
        self.hideElement()

        """ constructor for the EyeTracker class """
        self.connected = False
        self.tracking = False
        # gazeData is (timeStamp, x, y)
        self.gazeData = []
        # fixations is (timeStamp, x, y, duration)
        self.fixations = []
#
    def getLastSample(self, smooth=False):
        if (self.tracking and len(self.gazeData > 0)):
            return (self.gazeData[:-1])
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

    def saveGazeData(self):
        """Write to disk gaze data and fixations for this session of tracking"""
        output = open("run/gazeData_"+self.config.world.participantId+".log",mode='w')
        for g in self.gazeData:
            output.write(str(g))
        output.close()
        output = open("run/fixationData_"+self.config.world.participantId+".log", mode='w')
        for f in self.fixations:
            output.write(str(f))
        output.close()

    def enterState(self):
        super(EyeTrackerClient, self).enterState()

    def exitState(self):
        if (getattr(self.config, 'logGaze', False)):
            self.saveGazeData()
        super(EyeTrackerClient, self).exitState()
