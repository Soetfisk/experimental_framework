# This class presents a simple abstract class of a Service.
# Every service has a basic structure in which is specified:
# - a textual description of the service
# - one of 'once' or 'multiple' which indicates how many times
#   the service can be invoked once started. (NOT IMPLEMENTED)
# - an input datatype description: float,int,list, etc.
# - an output datatype description: idem.

# Examples of service providers:
# - perform calibration with eyetracker E
#   - result: ONE calibration.
# - calculate the average of a scalar variable.
#   - result: ONE value
# - calculate eye-gaze (this the eye-tracker)
#   - result: samples of gaze data every 1/60 seconds.
#
# Examples of service consumers:
# - read a calibration from calibration element.
# - ask for a statistic for a data set.
# - read sequence of eye-gaze positions.

from panda3d.core import *
from direct.stdpy.threading import Thread
from Utils.Debug import printOut

class Service(object):
    """ Basic class to extend for Service providers """
    def __init__(self, config):
      try:
        self.config = config
        if (str(config.direction)=='pull'):
          self.service = self.pullService
        else:
          self.service = self.pushService
        self.serviceName = config.serviceName
        printOut("New Service created: %s" % config.serviceName, 2)
        self.started = False
      except Exception,e:
        print e

    def setServerName( self, name):
        """Name of the SERVER, not the SERVICE"""
        self.serverName = name

    def setServiceImp(self,implementation):
        """ this is the actual implementation function (hence a callback), the 
        Server that wants to provide the service puts a handler here"""
        self.imp = implementation

 #####################################################

    def pullService(self,input=[], callback=None):
        """classic pull service, so client calls, server replies"""
        if (not callback):
            # sync pull service (simplest blocking call)
            printOut("Calling PULL service %s on server %s" %(self.serviceName,self.serverName),0)
            return self.imp(input)
        else:
            printOut("Error!: are you trying to use a PULL service with a callback?",0)
            printOut("Service name: %s" % self.serviceName,0)
            return None

    def pushService(self,callback=None, input=[]):
        """ push service: once called (or registered), it will keep 
            pushing values for any new data available to a callback specified 
            by the client"""
        if (not callback):
            printOut("Error, calling a pushService without a callback",2)

        printOut("Setting up push service %s" % self.serviceName, 2)
        # launch a new thread using Panda's facilities
        taskMgr.doMethodLater( 0, self._pushService,  self.serviceName, extraArgs = [input,callback] )
                            #   taskChain = self.taskChain )
        return

    def _pushService(self, input, callback):
        """ performs the actual service in an async call"""
        printOut("Calling back with the results of %s" % self.serviceName, 1)
        # transform the input
        result = self.imp(input)
        callback(result)

    def startService(self):
        """initializes the service if needed"""
        pass

    def stopAll(self):
        pass

    def stopService(self):
        """stops the service if needed"""
        pass

