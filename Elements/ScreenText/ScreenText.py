# panda imports
from direct.gui.DirectGui import *
from direct.task.Task import *
from panda3d.core import *
from Element import *

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
        super(ScreenText,self).__init__(**kwargs)
        # this defines:
        # self.sceneNP and self.hudNP

        text = getattr( self, 'plain_text', None)
        if (not text):
            print "Missing reference to what text to display when building ScreenText!"
            sys.exit()

        tN = TextNode(text)
        tN.setAlign(TextNode.ALeft)
        tN.setWordwrap(30)
        tNP = NodePath(tN)
        tNP.setName("plain_text")
        tNP.setPos(-1.5,0.0,0.5)
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

