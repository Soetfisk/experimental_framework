# panda imports
from direct.gui.DirectGui import *
from direct.task.Task import *
from panda3d.core import *
from direct.gui.OnscreenText import OnscreenText
import random as rnd

from Elements.Element.Element import *


#sys utils
import sys

class ScreenText(Element):
    """
    Class to display a text node
    Will get some configuration from JSON configuration.
    """

    def __init__(self, **kwargs):
        """
        world is a reference to the main class
        text: is the name of the node in the XML config
        """
        # build basic element
        super(ScreenText, self).__init__(**kwargs)
        # this defines:
        # self.sceneNP and self.hudNP

        text = getattr(self.config, 'file message', None)
        if text is None:
            printOut("Missing reference to what text to display when building ScreenText!", 0)
            sys.exit()

        margin = 0.9 # used as a %

        # text is hung by the aspect2D, which is -1 to 1 in height and w/h in width.
        leftBorder = - self.config.world.camera.screenWidth / float(self.config.world.camera.screenHeight)
        leftBorder = leftBorder * margin

        topBorder = 1.0 * margin

        tN = TextNode(text)
        tN.setAlign(TextNode.ALeft)
        tN.setWordwrap(25)
        tNP = NodePath(tN)
        tNP.setName("message")
        tNP.setPos(leftBorder,0.0,topBorder)
        tNP.setScale(0.09)

        lines = open(text).read()
        tN.setText(lines)
        # attach the text node to the HUD section
        tNP.reparentTo(self.hudNP)
        # hide the whole node

        self.hideElement()

    def enterState(self):
        # print "entering ScreenText"
        # super class enterState
        Element.enterState(self)

    def exitState(self):
        # print "leaving state ScreenText"
        Element.exitState(self)
