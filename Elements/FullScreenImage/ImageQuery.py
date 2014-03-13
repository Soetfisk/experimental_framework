# panda imports
from direct.gui.DirectGui import *
from direct.task.Task import *
from panda3d.core import *
from Element import *
from direct.gui.OnscreenImage import OnscreenImage

#sys utils
import sys
import random
from Utils.Debug import printOut

class ImageQuery(Element):
    """
    Class to display an image and waits for an answer from the
     user which has to match one of a set of predefined strings
     in the configuration of the ImageQuery element.
    """

    def __init__(self, **kwargs):
        """
        Class constructor
        """
        # build basic element  
        super(ImageQuery,self).__init__(**kwargs)

        sx, sz = getattr(self,'scale',[1.0,1.0])
        self.imageNodes=[]
        self.hiddenNodes=[]

        tempNodes=[]

        # pick a random image to start
        self.current = random.randint(0, len(self.imageNodes))
        # load images for the test
        try:
            for arg in self.imageStrArgs:
                finalName = self.imageNameStr % arg
                tempNodes.append(OnscreenImage(image=finalName,
                                               scale=Vec3(sx, 1.0, sz)))
                tempNodes[-1].setTransparency(TransparencyAttrib.MAlpha)
                tempNodes[-1].hide()
                tempNodes[-1].reparentTo(self.hudNP)

            self.imageNodes = zip(tempNodes, self.imageAnswers)

        except Exception,e:
            printOut("Fatal error, could not load texture file",0)
            printOut(str(e), 0)
            self.world.quit()

        # label text
        label = OnscreenText( text = "What do you see?",
                              pos = (0,-0.7),
                              scale = 0.08,
                              fg= [1.0,1.0,1.0,1.0],
                              align=TextNode.ACenter,
                              mayChange=1 )
        label.reparentTo(self.hudNP)
        # place holder to write
        self.input = DirectEntry(text = "" ,scale=.05,command=self.userInput,
                initialText="", numLines = 1,focus=1,focusInCommand=self.clearText)
        self.input.reparentTo(self.hudNP)

    def userInput(self, text):
        print text

    def clearText(self):
        self.input.set("")

    def restartCheck(self):
        for n in self.hiddenNodes:
            if n not in self.imageNodes:
                self.imageNodes.append(n)
        self.current=random.randint(0,len(self.imageNodes))
        self.hiddenNodes=[]

        self.imageNodes[self.current][0].show()

    def nextImage(self):
        if len(self.imageNodes)==1:
            # FINISHED
            # send finished message and end colour blind check
            return

        # hide the image
        self.imageNodes[self.current][0].hide()
        # clean up GUI
        # TODO

        # remove from current, put in hidden
        self.hiddenNodes.append(self.imageNodes[self.current])
        self.imageNodes.remove(self.hiddenNodes[-1])

        self.current = random.randint(0,len(self.imageNodes)-1)
        self.imageNodes[self.current][0].show()

        self.clearText()

    def enterState(self):
        Element.enterState(self)
        self.restartCheck()

    def exitState(self):
        Element.exitState(self)

