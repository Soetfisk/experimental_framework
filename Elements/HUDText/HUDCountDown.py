__author__ = 'Francholi'

# panda imports
from direct.gui.DirectGui import *
from direct.task.Task import *
from panda3d.core import *
from Element import *
from HUDText import HUDText

#sys utils
import sys

class HUDCountDown(HUDText):
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
        super(HUDCountDown, self).__init__(**kwargs)

        # check if hide boolean has been specified
        # otherwise assume visible
        self.config.hide = getattr(self.config,'hide',False)

        if (not getattr(self.config,'countDown')):
            printOut("Error building HUDCountDown, missing countDown attribute in YAML",0)
            self.config.world.quit()

        if (not getattr(self.config,'delayStart',1.0)):
            self.config.delayStart = 1.0
            printOut("Warning, starting count down timer in 1 second by default",0)

        if (not getattr(self.config,'trigger',False)):
            self.config.trigger = 'auto'
            printOut("Warning, this count down timer triggers event 'auto' by default",0)

        # by default Element renders in bin fixed,5
        self.hudNP.setBin('fixed',10)

    def enterState(self):
        # print "entering ScreenText"
        # super class enterState
        HUDText.enterState(self)
        # I WANT THIS NODE TO BE ALWAYS ON TOP
        self.log("Starting count down timer: %s\n" % self.config.name)
        taskMgr.add(self.delayStart, "delayStart", sort=2)
        # is it visible??
        if (self.config.hide):
            self.hideElement()

    def exitState(self):
        # print "leaving state ScreenText"
        taskMgr.remove("onScreenTimer")
        HUDText.exitState(self)

    def delayStart(self, task):
        if (task.time >= self.config.delayStart):
            taskMgr.add(self.updateTimer, "onScreenTimer", sort=2)
            return task.done
        else:
            return task.cont

    def updateTimer(self, task):
        if (self.config.countDown - task.time <= 0):
            # enter into a passive mode, hides the node and
            # and does NOTHING ELSE until exits the state.
            self.hideElement()
            self.sendMessage(self.config.trigger)
            return task.done
        else:
            if (not self.config.hide):
                self.textNode.setText("%s \n %.0f" % (self.config.text,self.config.countDown - task.time))
            return task.cont

