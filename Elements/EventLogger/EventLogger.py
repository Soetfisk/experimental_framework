__author__ = 'Francholi'
__author__ = 'Francholi'

# panda imports
from Element import *
from direct.showbase.DirectObject import DirectObject

from Logger import Logger

class EventLogger(Element):
    """
    As the name indicates, it's an empty state. It does nothing.
    It can react to timeout events using:
    timeout: float

    """
    def __init__(self, **kwargs):
        """
        See the Element class to find out what attributes are available
        from scratch
        """
        super(EventLogger, self).__init__(**kwargs)
        self.listener = DirectObject()

        # registering some events by hand
        self.listener.accept('crossHair',self.logEvent)

        uniqueFileName = self.config.logfile +"_"+ self.config.world.participantId + ".log"
        self.eventLog = Logger(uniqueFileName, 'w')
        self.eventLog.startLog()
        self.eventLog.logEvent('Event logger started\n')
        taskMgr.add( self.updateHooks, 'updateHooks' )

        self.registeredEvents = messenger.getEvents()
        for e in self.registeredEvents:
            self.listener.accept(e, self.logEvent, [e])

        self.hideElement()

    def logEvent(self, event=None, args=[]):
        if event == 'mouse1':
            args = base.mouseWatcherNode.getMouse()
        self.eventLog.logEvent("%s;%s\n"%(event,args))

    def enterState(self):
        # super class enterState
        Element.enterState(self)

    def exitState(self):
        # super class exitState
        Element.exitState(self)
        taskMgr.remove( 'updateHooks' )
        self.eventLog.logEvent('Event logger stopped\n')
        self.eventLog.closeLog()

    def updateHooks(self, task):
        # run every 100 ms
        task.delayTime = 0.1
        newEvents = [x for x in messenger.getEvents() if x not in self.registeredEvents]
        for x in newEvents:
            #print "NEW EVENT"
            self.listener.accept(x, self.logEvent, [x])
            self.registeredEvents.append(x)
        return task.cont





