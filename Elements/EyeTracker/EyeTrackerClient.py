"""
Notes on the Eye tracking client.

All communication with the eyetracker must be
done using the ZeroMQ library.

The client can access depending on the eyetracker
client brand to certain information and commands to
read and control the eyetracker behavior.

Coordinates provided by the eyetracker can vary, so
a rectangular bounding box is provided or can be queried
by the client in order to know how to interpret the
coordinates provided.

With each coordinate provided by the tracker, a timestamp
from a hi-res clock is provided.
This clock is relative with not known start time.
"""

from direct.showbase.DirectObject import DirectObject
from Utils.Debug import printOut
from Utils.Utils import enum

MSG = enum(CONNECT=0, DISCONNECT=1, START_TRACKING=2, STOP_TRACKING=3, LOAD_CALIB=4,
           START_CALIB=5, STOP_CALIB=6, ADD_CALIB_POINT=7, RM_CALIB_POINT=8)

class EyeTrackerClient(DirectObject, simul=True):
    def __init__(self):
        """ constructor for the EyeTracker class """
        pass
#        self.trackerUrl = None
#        self.mainLoopThread = None
#        # allow for fake tracker
#        self.simul=simul
#
#        # gaze data
#        self.gazeData = None
#        self.gadeDataHistory = []
#
#        # list of calibration points that are going to
#        # be used to callibrate the tracker
#        self.calibPoints = []

    def connectTracker(self):
        pass

    def clearCalibration(self):
        # get rid of local copies of calibration points
        self.calibPoints = []
            
    # Calibration own screen
    def startCalibration(self):
        pass


#  def addCalibPoint(self, point):
#      printOut("Adding calibration point %d,%d" % (point[0],point[1]),0)
#      if (not self.simul):
#          p = Point2D()
#          p.x, p.y = point[0],point[1]
#          self.tracker.AddCalibrationPoint(p,
#              lambda error,r:
#              taskMgr.doMethodLater( self.onCalPointAdded, "calPointAdded",
#                                       extraArgs=[error,r,p] ) )
#      # testing purposes
#      else:
#          self.onCalPointAdded( None, 'r', p )
#        return False

#    def removeCalibPoint(self, point):
#        printOut("Removing calibration point %d,%d" % (point[0],point[1]),0)
#        if (not self.simul):
#            p = Point2D()
#            p.x, p.y = point[0],point[1]
#            self.tracker.RemoveCalibrationPoint( p,
#                lambda error,r:
#                taskMgr.doMethodLater( self.onCalPointRemoved, "calPointRemoved",
#                                         extraArgs=[error,r,p] ) )
#        # testing purposes
#        else:
#            self.onCalPointRemoved( None, 'r', p)
#        return False
            
#    def computeCalibration(self):
#        if (not self.simul):
#            self.tracker.ComputeCalibration(
#                lambda error, r:
#                taskMgr.doMethodLater( self.onCalibrationComputed,
#                                       "calibration computed",
#                                       extraArgs=[ error, r ] ) )
#        else:
#            # just call the callback directly
#            self.onCalibrationComputed( None, 'r' )
#
#        return False
#
#    def onCalibrationComputed(self, error, r):
#        if error == 0x20000502:
#            printOut("Error on calibration, not enough data: %s"%error,0)
#        else:
#            printOut("Calibration done!",0)
#

#====================================================================================
#====================================================================================
#====================================================================================
# Start tracker and callback to collect gaze data.
#    def startTracking( self ):
#        #if (self.trackerConnected):
#        #    self.tracker.StartTracking ( self.onGazeData )
#        #else:
#        pass
#
#    def onGazeData(self, gaze_data):
#        pass
#
##====================================================================================
#    def stopLibrary(self):
#        #self.mainLoopThread.stop()
#        pass

