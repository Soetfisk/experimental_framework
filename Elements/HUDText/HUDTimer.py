__author__ = 'Francholi'

# panda imports
from direct.gui.DirectGui import *
from direct.task.Task import *
from panda3d.core import *
from Element import *
from HUDText import HUDText

#sys utils
import sys

class HUDTimer(HUDText):
    """
    Class to display a single piece of text
    The text to display will be specified in a text attribute
    in the Element description in the experiment
    """
    def __init__(self, **kwargs):
        """
        world is a reference to the main class
        """
        # build basic element
        super(HUDTimer, self).__init__(**kwargs)

        # check if hide boolean has been specified
        # otherwise assume visible
        if (not getattr(self.config,'hide',False)):
            self.config.hide = False

        # by default Element renders in bin fixed,5
        self.hudNP.setBin('fixed',10)

    def enterState(self):
        # print "entering ScreenText"
        # super class enterState
        HUDText.enterState(self)
        # I WANT THIS NODE TO BE ALWAYS ON TOP
        self.log("Starting timer: " + self.config.name)
        taskMgr.add(self.updateTimer, "onScreenTimer", sort=2)
        # is it visible??
        if (self.config.hide):
            self.hideElement()

    def exitState(self):
        # print "leaving state ScreenText"
        taskMgr.remove("onScreenTimer")
        self.log("Stopping timer: %s\n" % self.config.name)
        self.log("Time elapsed: %s\n" % str(self.timeElapsed))
        HUDText.exitState(self)

    def updateTimer(self, task):
        if (not self.config.hide):
            self.textNode.setText("%.0f" % task.time)
        return task.cont

