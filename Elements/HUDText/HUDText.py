__author__ = 'Francholi'

# panda imports
from direct.gui.DirectGui import *
from direct.task.Task import *
from panda3d.core import *
from Element import *

#sys utils
import sys

class HUDText(Element):
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
        super(HUDText, self).__init__(**kwargs)
        # this defines:
        # self.sceneNP and self.hudNP

        text = getattr(self.config, 'text', None)
        if text is None:
            printOut("Missing 'text' attribute in experiment file", 0)
            sys.exit()

        # text is hung by the aspect2D, which is -1 to 1
        # in height and w/h in width.
        leftBorder = - self.config.world.camera.screenWidth / float(self.config.world.camera.screenHeight)

        tN = TextNode(self.config.name)
        tN.setAlign(TextNode.ALeft)
        tNP = NodePath(tN)
        tNP.setName(self.config.name)
        tNP.setScale(0.09)

        topLeft = getattr(self.config,'topLeft',[0.0,0.0])

        tNP.setPos(leftBorder + topLeft[0], 0, 0.6 + topLeft[1])

        tN.setText(self.config.text)
        # attach the text node to the HUD section
        tNP.reparentTo(self.hudNP)
        # hide the whole node
        self.textNode = tN
        self.hideElement()

    def enterState(self):
        # print "entering ScreenText"
        # super class enterState
        Element.enterState(self)
        #taskMgr.add(self.updateTimer, "onScreenTimer", sort=2)

    def exitState(self):
        # print "leaving state ScreenText"
        Element.exitState(self)
        taskMgr.remove("onScreenTimer")

#    def updateTimer(self, task):
        #self.textNode.setText("%.0f" % task.time)
        #return task.cont

