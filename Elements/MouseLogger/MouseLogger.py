__author__ = 'Francholi'
__author__ = 'Francholi'

# panda imports
from Element import *
from Logger import Logger

class MouseLogger(Element):
    """
    Logs the position of the mouse, in a text file using
     the participant ID and timestamps that are synchronized with the
     rest of the timestamps from other events in the simulation
    """
    def __init__(self, **kwargs):
        """
        See the Element class to find out what attributes are available
        from scratch
        """
        super(MouseLogger, self).__init__(**kwargs)
        self.mouseLog = Logger(self.baseTime, "run/mouseLog_%s.txt" % self.config.world.participantId)
        self.left = MouseButton.one()
        self.leftDown = False
        self.right = MouseButton.two()
        self.rightDown = False
        self.hideElement()

    def enterState(self):
        # super class enterState
        Element.enterState(self)
        self.mouseLog.startLog()
        taskMgr.add(self.logMouseTask, "mouseLogTask_%s" % self.config.world.participantId)

    def exitState(self):
        # super class exitState
        taskMgr.remove("mouseLogTask_%s" % self.config.world.participantId)
        self.mouseLog.stopLog()
        Element.exitState(self)

    def logMouseTask(self, t):
        m = base.mouseWatcherNode
        if not m.hasMouse():
            return t.cont
        try:
            self.mouseLog.logEvent("%f %f" % (m.getMouseX(),
                                              m.getMouseY()))
            if m.is_button_down(self.left):
                self.leftDown = True
            elif self.leftDown:
                    self.mouseLog.logEvent("mouse1")
                    self.leftDown = False

            if m.is_button_down(self.right):
                self.rightDown = True
            elif self.rightDown:
                    self.mouseLog.logEvent("mouse2")
                    self.rightDown = False
        except:
            self.mouseLog.logEvent("mouse outside of the window...")
        finally:
            return t.cont


