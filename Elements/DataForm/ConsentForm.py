from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import *
from panda3d.core import *

from Element import *

import sys
from Utils.Utils import splitString
from Utils.Debug import printOut

class ConsentForm(Element):
    """Class to display a consent form, which is made of a
    question label, a tick control, and YES/NO option buttons"""
    def __init__(self, **kwargs):
        """
        Class constructor
        """
        # build basic element
        super(ConsentForm, self).__init__(**kwargs)
        printOut("Element for ConsentForm constructed", 1)
        # the config is loaded by Element automatically into self.config
        self.setupGUI()
        printOut("Consent form GUI constructed", 1)
        # default answer will be NO
        self.answer = 'NO'

    def setupGUI(self):
        """ Builds the GUI based on the YAML description """
        # DirectFrame that will contain the GUI
        # Find out window dimensions
        ratio = self.config.world.camera.ratio
        frameSize = (-ratio, ratio, -1.0, 1.0)
        # centered
        pos = (0, 1.0, 0)
        # guiLabels colour
        labelColour = self.config.settings.labelcolour
        # global scale of the frame
        scale = self.config.settings.scale
        # canvas with scrolling capabilities
        self.myFrame = DirectScrolledFrame(canvasSize=(frameSize[0],
                                                       frameSize[1],
                                                       50*frameSize[2],
                                                       frameSize[3]),
                                                       frameColor=self.colours['dark_grey'],
                                                       frameSize=frameSize,
                                                       pos=pos)

        # reparent the frame to the hudNP so we can hide it easily
        self.myFrame.reparentTo(self.hudNP)

        # read title or set to a default value
        title = getattr(self.config.settings,"title", "")

        # title of the frame
        label = OnscreenText( text = title,
                              pos = (0, frameSize[3] - scale*1.5 ),
                              scale = scale * 1.5, fg=labelColour,
                              align=TextNode.ACenter, mayChange=1 )
        label.reparentTo(self.myFrame.getCanvas())

        tN = TextNode("consentTextNode")
        tN.setAlign(TextNode.ALeft)
        tN.setWordwrap(25)
        tNP = NodePath(tN)
        tNP.setName("consentText")
        tNP.setPos(-ratio*0.9,0.0,0.7)
        tNP.setScale(0.09)
        tN.setText(self.config.settings.consentText)
        # attach the text node to the HUD section
        tNP.reparentTo(self.myFrame.getCanvas())

        pad0 = (0.9,0.7)
        self.yesButton = DirectButton(parent = self.myFrame.getCanvas(),
                                      text="Yes", pad=pad0, scale=0.08,
                                      pos=(0, 0, -0.8),
                                      command=self.yesPressed)

        self.noButton = DirectButton(parent = self.myFrame.getCanvas(),
                                      text="No", pad=pad0, scale=0.08,
                                      pos=(0.4, 0, -0.8),
                                      command=self.noPressed)


    def yesPressed(self):
        self.answer = 'yes'
        self.sendMessage('yesPressed')

    def noPressed(self):
        self.answer = 'no'
        self.sendMessage('noPressed')

    def enterState(self):
        Element.enterState(self)
        #self.config.world.stopKeyboard()

    def exitState(self):
        # exit state
        Element.exitState(self)


