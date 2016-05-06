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

        sx, sz = getattr(self.config,'tuple_scale',[1.0,1.0])
        self.imageNodes=[]
        self.hiddenNodes=[]
        # if the user makes a mistake, we give ONE chance to ammend at
        # the end of the experiment
        self.recheck=[]

        tempNodes=[]

        # pick a random image to start
        self.current = random.randint(0, len(self.imageNodes))
        # load images for the test
        try:
            for arg in self.config.tuple_imageStrArgs:
                finalName = self.config.fname_imageNameStr % arg
                tempNodes.append(OnscreenImage(image=finalName,
                                               scale=Vec3(sx, 1.0, sz)))
                tempNodes[-1].setTransparency(TransparencyAttrib.MAlpha)
                tempNodes[-1].hide()
                tempNodes[-1].setName(finalName)
                tempNodes[-1].reparentTo(self.hudNP)

            self.imageNodes = zip(tempNodes, self.config.tuple_imageAnswers)

        except Exception,e:
            printOut("Fatal error, could not load texture file",0)
            printOut(str(e), 0)
            self.config.world.quit()

        # label text
        label = OnscreenText( text = "What do you see?",
                              pos = (0,-0.7),
                              scale = .08,
                              fg= [1.0,1.0,1.0,1.0],
                              align=TextNode.ACenter,
                              mayChange=1 )
        label.reparentTo(self.hudNP)
        # place holder to write
        self.input = DirectEntry(text = "" ,scale=.07, width=5,
                                 pos = (0.4,0.0,-0.7),
                                 command=self.userInput, initialText="",
                                 numLines = 1,focus=1,
                                 focusInCommand=self.clearText)
        self.input.reparentTo(self.hudNP)

        # a list of strings for each of the answers
        self.results = []
        self.rechecking = False

    def userInput(self, text):
        self.nextImage()

    def clearText(self):
        self.input.set("")

    def restartCheck(self):
        self.results = []
        for n in self.hiddenNodes:
            if n not in self.imageNodes:
                self.imageNodes.append(n)
        self.current=random.randint(0,len(self.imageNodes)-1)
        self.hiddenNodes=[]
        self.recheck=[]
        # display first image (if the hudNP is visible)
        self.imageNodes[self.current][0].show()
        self.rechecking = False

    def checkAnswer(self):
        answer = self.input.get()
        if answer == str(self.imageNodes[self.current][1]):
            self.results.append("Correct answer: %s" % answer)
            return True
        else:
            self.results.append("Incorrect answer: %s for %s" %
                                (answer,self.imageNodes[self.current][0].getName()))
            return False

    def nextImage(self):
        # check AND log the answer / SIDE EFFECT
        result = self.checkAnswer()
        # hide current image
        self.imageNodes[self.current][0].hide()
        # clean up GUI
        self.clearText()

        # CORRECT ANSWER
        if result:
            # remove from current, put in hidden
            self.hiddenNodes.append(self.imageNodes[self.current])
            self.imageNodes.remove(self.hiddenNodes[-1])
        # INCORRECT ANSWER, ADD TO RE-CHECK
        else:
            self.recheck.append(self.imageNodes[self.current])
            self.imageNodes.remove(self.recheck[-1])

        if len(self.imageNodes) == 0:
            if len(self.recheck) > 0:
                if not self.rechecking:
                    self.rechecking = True
                    self.imageNodes = self.recheck
                    self.recheck = []
                    self.log("Image query not OK, rechecking\n")
                else:
                    self.log("Image query not OK\n")
                    self.sendMessage("imageQueryBad")
                    return
            else:
                self.log("Image query ok\n")
                self.sendMessage("imageQueryOk")
                return

        self.current = random.randint(0,len(self.imageNodes)-1)
        self.imageNodes[self.current][0].show()
        self.input['focus'] = True

    def enterState(self):
        Element.enterState(self)
        self.restartCheck()
        self.input['focus'] = True

    def exitState(self):
        Element.exitState(self)

