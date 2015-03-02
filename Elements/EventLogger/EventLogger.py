__author__ = 'Francholi'
__author__ = 'Francholi'

# panda imports
from Element import *

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

        #self.eventLog = Logger(self.config.logfile, 'w')
        #self.eventLog.startLog()
        #self.eventLog.logEvent('Event logger started\n')
        self.registeredEvents = messenger.getEvents()
        #for e in self.registeredEvents:
        #    print e
        #    self.config.world.accept(e, self.logEvent, [e])
        #for event in self.registeredEvents:
        #    messenger.accept(event)

        self.hideElement()

    def logEvent(self, event):
        print event

    def enterState(self):
        # super class enterState
        Element.enterState(self)

    def exitState(self):
        # super class exitState
        Element.exitState(self)
        #self.eventLog.logEvent('Event logger stopped\n')
        #self.eventLog.closeLog()


