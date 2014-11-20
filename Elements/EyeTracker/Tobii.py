"""
Notes on the Tobii eyetracker API.

A background thread MUST be created to receive data from
the tracker, specifically an instance of "MainloopThread".
No calls to the tobii sdk should be made from the background
thread!

Coordinates provided by the eyetracker are in User coordinate
System (UCS), which are in milimiters and with the center 
in the middle of FRONTAL FACE OF THE EYE_TRACKER -- not the screen)

During calibration, calibration points are given in normalized 
coordinates. (0,0) is top-left, (1,1) is bottom-right

The gaze data reported by the eye tracker is time stamped with a time 
from the high-resolution clock built into the eye tracker hardware. 
This clock is relative with no known start time. In the reminder of 
this document we will refer to this clock as the eye tracker clock.
The clock from the tracker can drift from the clock of the client (PC).
"""

# tobii imports
try:
    from tobii.sdk.basic import EyetrackerException
    import tobii.sdk.mainloop 
    import tobii.sdk.browsing
    import tobii.sdk.eyetracker
    from tobii.sdk.types import Point2D, Blob
except:
    pass

from direct.showbase.DirectObject import DirectObject
from Debug import printOut
class TobiiEyeTracker(DirectObject, simul=True):
    def __init__(self):
        """ constructor for the EyeTracker class """
        self.tracker = None
        self.trackerConnected = False
        self.browser = None
        self.mainLoopThread = None
        self.simul=simul

        # gaze data
        self.gazeData = None
        self.gadeDataHistory = []

        # calibration points
        self.calibPoints = []

    def initLibrary(self):
        """ Mandatory initialization of the whole library """
        
        # TOBII SDK
        if (not self.simul):
            tobii.sdk.init()
            self.mainLoopThread = tobii.sdk.mainloop.MainloopThread()
            self.mainLoopThread.start()

        # creates AND starts the browser right away.
        # The trick of using a lambda function is to actually call the callback from
        # a foreground thread. When the lambda func. gets called, it will be from the
        # background mainloopthread. From there, we add a one-time task in Panda3d, to
        # copy the values and call the actual callback from the foreground thread.
        # The same approach is found all around the code, because the Tobii API needs it.

        # TOBII SDK
        if (not self.simul):
            self.browser = EyetrackerBrowser(
                           self.mainLoopThread, 
                           lambda t,n,i: taskMgr.doMethodLater(self.onBrowserEvent,
                                                               "onBrowserEvent",
                                                               extraArgs=[t,n,i]))
        else:
            # dummy for testing
            self.browser = 'browser'
            # call directly as if the actual call was from the Tobii SDK
            self.onBrowserEvent('FOUND', 'event_name', 'trackerInfo')


    def onBrowserEvent( self, eventType, eventName, trackerInfo ):
        """ this method will be called in one of the Panda3d threads, in which is "safe"
            to call tobii sdk functions.
            trackerInfo is of EyetrackerInfo class """

        # testing some properties, not necesary during normal usage.
        properties = ['product_id', 'given_name', 'model', 'generation', 'firmware_version',
                'status', 'factory_info']
        printOut("Eye tracker event", 0, 'eyetracker')
        for p in properties:
            _p = getattr( trackerInfo, p, None )
            printOut("%s: %s" %(p,str(_p)),0,'eyetracker')

        # Tobii SDK
        # if we found an eye-tracker, connect straight away to it.
        if (not self.simul):
            tobii.sdk.eyetracker.Eyetracker.create_async(self.mainLoopThread, trackerInfo,
                    lambda error, eyetracker: 
                    taskMgr.doMethodLater(self.onEyeTrackerCreated,"onEyeTrackerCreated",
                                          extraArgs=[error,eyetracker, trackerInfo]))
        else:
            # dummy call for testing
            self.onEyeTrackerCreated( None,'tracker','trackerInfo')

    def onEyeTrackerCreated( self, error, tracker, trackerInfo ):
        if error:
            printOut(" Connection to %s failed because of an exception: %s" % 
                    (eyetracker_info,error), 2)
            return False
        self.tracker = tracker
        return True
#====================================================================================
#====================================================================================
#====================================================================================
    def clearCalibration(self):
        # Tobii SDK
        # clear the temporary buffers
        if (not self.simul):
            self.tracker.ClearCalibration()
        else:
            pass
        # get rid of local copies of calibration points
        self.calibPoints = []
            
# Calibration
    def startCalibration(self):

        # Tobii SDK
        # Acquire calibration state, and clear the temporary calibration buffer
        if (not self.simul):
            if (self.tracker is not None):
                self.tracker.StartCalibration(
                        lambda error, r:
                        taskMgr.doMethodLater(self.onCalibStart,"onCalibStart",
                                              extraArgs=[error,r]))
        # simulation
        else:
            self.onCalibStart(None,'r')


    def onCalibStart(self, error, r):
        if error:
            self.onCalibDone(False,"Error in calibration: 0x%0x" % error)
            return False
           
        # at this point, the calibration has started!, so Tobii is ready to start
        # receiving calibration points.
        # we will accept messages from a another object, through the Panda3D messaging
        # system, which will define where and when calibration points should be registered.
        self.accept("addCalibPoint", self.addCalibPoint)
        self.accept("removeCalibPoint", self.removeCalibPoint)
        self.accept("computeCalibration", self.computeCalibration )

        return False

    def addCalibPoint(self, point):
        printOut("Adding calibration point %d,%d" % (point[0],point[1]),0)
        if (not self.simul):
            p = Point2D()
            p.x, p.y = point[0],point[1]
            self.tracker.AddCalibrationPoint(p,
                lambda error,r:
                taskMgr.doMethodLater( self.onCalPointAdded, "calPointAdded",
                                         extraArgs=[error,r,p] ) )
        # testing purposes
        else:
            self.onCalPointAdded( None, 'r', p )
        return False

    def removeCalibPoint(self, point):
        printOut("Removing calibration point %d,%d" % (point[0],point[1]),0)
        if (not self.simul):
            p = Point2D()
            p.x, p.y = point[0],point[1]
            self.tracker.RemoveCalibrationPoint( p,
                lambda error,r:
                taskMgr.doMethodLater( self.onCalPointRemoved, "calPointRemoved",
                                         extraArgs=[error,r,p] ) )
        # testing purposes
        else:
            self.onCalPointRemoved( None, 'r', p)
        return False
            
    def onCalPointAdded( self, error, r , point):
        if (not self.simul):
            if error:
                self.onCalibDone( False, "Error adding calibration point: (0x%0x)" % error)
                return False

        # keep track of the calibration point (simulation and real device)
        self.calibPoints.append(point)
        return False

    
    def onCalPointRemoved( self, error, r, point):
        if (not self.simul):
            if error:
                self.onCalibDone( False, "Error removing calibration point: (0x%0x)" % error)
        else:
            pass
        self.calibPoints.remove(point)
    
    def computeCalibration(self):
        if (not self.simul):
            self.tracker.ComputeCalibration(
                lambda error, r:
                taskMgr.doMethodLater( self.onCalibrationComputed, 
                                       "calibration computed",
                                       extraArgs=[ error, r ] ) )
        else:
            # just call the callback directly
            self.onCalibrationComputed( None, 'r' )

        return False

    def onCalibrationComputed(self, error, r):
        if error == 0x20000502:
            printOut("Error on calibration, not enough data: %s"%error,0)
        else:
            printOut("Calibration done!",0)


#====================================================================================
#====================================================================================
#====================================================================================
# Start tracker and callback to collect gaze data.
    def startTracking( self ):
        #if (self.trackerConnected):
        #    self.tracker.StartTracking ( self.onGazeData )
        #else:
        pass
       
    def onGazeData(self, gaze_data):
        pass

#====================================================================================
    def stopLibrary(self):
        #self.mainLoopThread.stop()
        pass

