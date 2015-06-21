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

class ColourPreference(Element):
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
        super(ColourPreference,self).__init__(**kwargs)

        sx, sz = getattr(self.config,'scale',[1.0,1.0])
        self.imageNodes={}

        filepath = "PilotData/colorblind/"

        try:
            for pair in self.config.pairs:
                for p in pair:
                    if p not in self.imageNodes:
                        self.imageNodes[p] = OnscreenImage(
                            image=filepath + p + ".png",
                            scale=Vec3(sx,1.0, sz))
                        self.imageNodes[p].setTransparency(TransparencyAttrib.MAlpha)
                        self.imageNodes[p].hide()
                        self.imageNodes[p].setName(p)
                        self.imageNodes[p].reparentTo(self.hudNP)
        except Exception,e:
            printOut("Fatal error, could not load texture file",0)
            printOut(str(e), 0)
            self.config.world.quit()

        # label text
        label = OnscreenText( text = "Reload is working",
                              pos = (0,-0.7),
                              scale = .08,
                              fg= [1.0,1.0,1.0,1.0],
                              align=TextNode.ACenter,
                              mayChange=1 )
        label.reparentTo(self.hudNP)
        # place holder to write

        self.currentPair = None

        #self.input = DirectEntry(text = "" ,scale=.07, width=5,
        #                         pos = (0.4,0.0,-0.7),
        #                         command=self.userInput, initialText="",
        #                         numLines = 1,focus=1,
        #                         focusInCommand=self.clearText)
        #self.input.reparentTo(self.hudNP)

        # a list of strings for each of the answers
        #self.results = []
        #self.rechecking = False


    # def nextImage(self):
    #     # check AND log the answer / SIDE EFFECT
    #     result = self.checkAnswer()
    #     # hide current image
    #     self.imageNodes[self.current][0].hide()
    #     # clean up GUI
    #     self.clearText()
    #
    #     # CORRECT ANSWER
    #     if result:
    #         # remove from current, put in hidden
    #         self.hiddenNodes.append(self.imageNodes[self.current])
    #         self.imageNodes.remove(self.hiddenNodes[-1])
    #     # INCORRECT ANSWER, ADD TO RE-CHECK
    #     else:
    #         self.recheck.append(self.imageNodes[self.current])
    #         self.imageNodes.remove(self.recheck[-1])
    #
    #     if len(self.imageNodes) == 0:
    #         if len(self.recheck) > 0:
    #             if not self.rechecking:
    #                 self.rechecking = True
    #                 self.imageNodes = self.recheck
    #                 self.recheck = []
    #                 self.log("Image query not OK, rechecking\n")
    #             else:
    #                 self.log("Image query not OK\n")
    #                 self.sendMessage("imageQueryBad")
    #                 return
    #         else:
    #             self.log("Image query ok\n")
    #             self.sendMessage("imageQueryOk")
    #             return
    #
    #     self.current = random.randint(0,len(self.imageNodes)-1)
    #     self.imageNodes[self.current][0].show()
    #     self.input['focus'] = True
    #

    def imageSelected(self,args):
        # save the choice in a list or a file.

        pair = self.config.pairs[self.currentPair]

        selection = pair[0]
        if (args == 'right'):
            selection = pair[1]

        currentPair = "Selected {s} from {p[0]} -- {p[1]}".format(p = pair, s=selection)

        self.config.world.log.logEvent(currentPair+"\n")

        if len(self.config.pairs) > self.currentPair+1:
            self.displayPair(self.currentPair+1, True)

    def displayPair(self, which, flip):

        if (self.currentPair):
            self.hidePair(self.currentPair)

        self.currentPair = which
        a,b = self.config.pairs[which]
        if flip:
            temp = a
            a = b
            b = temp

        self.imageNodes[a].show()
        self.imageNodes[a].setPos(-0.6,1.0,0.0)
        self.imageNodes[b].show()
        self.imageNodes[b].setPos(0.6,1.0,0.0)

    def nextImage(self):
        pass

    def enterState(self):
        Element.enterState(self)

        self.displayPair(0, True)

    def exitState(self):
        Element.exitState(self)

