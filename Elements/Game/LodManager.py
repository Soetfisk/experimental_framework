
class CycleEvent(object):
    EVENT_TYPE = "CYCLE"
    def __init__(self, cycleNumber):
        self.cycleNumber = cycleNumber

    def getEventDetails(self):
        message = "Cycle %s just happened\n" % self.cycleNumber
        return message

    def getEventType(self):
        return self.EVENT_TYPE

    def getData(self):
        return self.cycleNumber

class LodManager(object):
    """ Small class to hold a list of the objects that
    need LOD management. When registering an object, the 
    manager will keep a reference to it, and use it when
    the call to "notify" is issued. 

    See config.xml parachutesLOD to see how is the behaviour
    of the manager. Basically it will change the LOD of the
    registered objects to change2Lod value after n cycles of
    the sequence. """

    def __init__(self):
        """ basic init, empty dict for the observers """
        # we store one key for each event, and a list of observers in each
        self.observers = {}
        # LoDHandlers implemented so far
        self.LoDHandlers = {}
        self.LoDHandlersData = {}
     
    def registerHandler(self, eventType, handler=None, xmlData=None):
        """ eventType is a string and handler is any function,
        handler will accept two arguments, the observer object and
        the actual event, and will decide what to do with that."""
        if eventType not in self.LoDHandlers.keys():
            self.LoDHandlers[eventType] = handler
            self.LoDHandlersData[eventType] = xmlData

    def detachHandler(self, eventType):
        """ eventType is a string """
        if eventType in self.LoDHandlers.keys():
            h = self.LoDHandlers.pop(eventType)
            hd= self.LoDHandlersData.pop(eventType)

    def register(self,o, eventTypeList):
        """ registers object o to all the events types in the list
        events, it's a list of strings """
        for e in eventTypeList:
            try:
                # if the observer is not registered for this event.
                if not o in self.observers[e]:
                    self.observers[e].append(o)
                # registering twice ?
                else:
                    print "Warning, registering an observer again\n"
            # no such event, assume that it's the first object for
            # this event.
            except KeyError:
                self.observers[e] = [o]

    def detach(self,o, eventTypeList):
        """ removes the object referenced from the according events
        listed in events"""
        for e in eventTypeList:
            try:
                self.observers[e].remove(o)
            except ValueError:
                pass
            except KeyError:
                pass

    def notify(self, anEvent):
        """ notify the actual observers interested in this event
            about the change. We will pass straight away the event
            anEvent that just happened!"""
        evtType = anEvent.getEventType()

        try:
            for observer in self.observers[evtType]:
                self.LoDHandlers[evtType](observer,anEvent)
        except KeyError:
            print "Notification of non registered event\n"



    # /////////////////////////////////////////////////////////////////////////
    # NEW_CYCLE event handler / highly coupled with parachutes!!!!
    def newCycle(self, observer, event):

        xmlData = self.LoDHandlersData[event.getEventType()]
        newQuality = int(xmlData.newQuality)
        observer.setTexture(toQ=newQuality, inTime=1)
        #print "informing %s about %s" % (observer.name,event.getEventType())
        return
    # ////////////////////////////////////////////////////////////////////////


    #def updateLods(self,cycleCount):
    #    """ changes level of detail after cycleCount cycles of the sequence """
    #    if (cycleCount == int(self.lodConfig.cycles)):
    #        for v in self.objList.values():
    #            v.setTexture(-1,int(self.lodConfig.change2Lod),1)


