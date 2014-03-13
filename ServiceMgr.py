from Utils.Debug import printOut
# some useful functions
from Utils.Utils import *
from Service import *

class ServiceMgr(object):
    """ This class keeps tracks of services, and provides other clients
    with the hooks to make use of these registered services."""

    def __init__(self, services):

        # configuration from JSON config/services
        self.jsonServices = services.services

        # dictionary of services
        self.services = {}

        # create a separate thread to run background services
        taskMgr.setupTaskChain("backGroundServices",numThreads=1)
        self.servicesThread = 'backGroundServices'

    def createFromTemplate( self, tempName ):
        """Creates an instance of a service using a textual template"""
        try:
            for s in self.jsonServices:
              if (str(s.serviceName) == tempName):
                printOut("Creating from template: %s" % s.serviceName,1)
                return Service(s)
            else:
                printOut('WARNING: createFromTemplate could not find a matching service for %s' % tempName,0)
                return None
        except Exception,e:
            print e

    def getService( self, serviceName ):
        """Returns a Service object, that can be used to access the particular
        service"""
        matching_services=[]
        for (key,value) in self.services.items():
          if (serviceName in key):
            matching_services.append(value)
        if (len(matching_services)==0):
          printOut("Warning, asking for a service not registered",0)
          printOut("Service: %s" % serviceName, 0)
          return None
        elif (len(matching_services)>1):
          printOut("Warning, more than one server found for service:",0)
          printOut(str(matching_services),0)
          printOut("Returning FIRST one in the list",0)
        return matching_services[0]

    def registerService(self, server):
        self.services[server.serviceName+'_'+server.serverName] = server
        printOut("Registered server %s for service %s" % (server.serverName,server.serviceName), 2)

    def unregService(self, serviceName):
        """ This removes completely the service, so ANY client that is using
        this service will be automatically disconnected or not receive any
        more messages """
        try:
            self.services[serviceName].stopAll()
            del self.services[serviceName]
        except KeyError,k:
            printOut("Error, trying to de-register an unregistered service!",0)
            printOut("Service: %s" % serviceName,0)
        except ValueError,v:
            printOut("Error, trying to de-register a non-existent handler",0)


