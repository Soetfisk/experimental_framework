# panda imports
from direct.gui.DirectGui import *
from direct.task.Task import *
from panda3d.core import *
from direct.gui.OnscreenText import OnscreenText
import random as rnd
from direct.interval.MetaInterval import *
from direct.interval.FunctionInterval import *
from direct.interval.IntervalGlobal import *
import random

from Elements.Element.Element import *
from Logger import Logger

#sys utils
import sys

#from Elements.EyeTracker.Tobii import TobiiEyeTracker

class SelectNumbers(Element):
    """
    Little sliding tile puzzle game
    """

    def __init__(self, **kwargs):
        # build parent object class
        super(SelectNumbers, self).__init__(**kwargs)
        self.hideElement()



    def showElement(self):
        Element.showElement(self)
        self.resetGame()

    def resetGame(self):
        pass

#    def addButtonsBigSmall(self):
#        self.bigger = DirectButton(parent = self.hudNP,
#                                      text="Bigger", #pad=pad0,
#                                      scale=0.08,
#                                      pad=(.1,.1),
#                                      pos=(0.6, 0, -0.9),
#                                      command=self.changeSize,
#                                      extraArgs=[1.5])
#
#        self.smaller = DirectButton(parent = self.hudNP,
#                                      text="Smaller", #pad=pad0,
#                                      pad=(.1,.2),
#                                      scale=0.082,
#                                      pos=(1.0, 0, -0.906),
#                                      command=self.changeSize,
#                                      extraArgs=[0.5])
#
#        self.shuffleButton = DirectButton(parent = self.hudNP,
#                                      text="Shuffle", #pad=pad0,
#                                      pad=(.1,.2),
#                                      scale=0.082,
#                                      pos=(0.1, 0, -0.906),
#                                      command=self.changeSize,
#                                      #state=0, # disabled
#                                      extraArgs=[1.0])
#
#        self.nextSizeButton = DirectButton(parent = self.hudNP,
#                                      text="Next", #pad=pad0,
#                                      pad=(.1,.2),
#                                      scale=0.082,
#                                      pos=(-0.5, 0, -0.906),
#                                      command=self.nextSizeFunc)
         #self.shuffleButton.setTransparency(TransparencyAttrib.MAlpha)
        #self.shuffleButton.setAlphaScale(0.3)


    def _recreateGrid(self, newSize):
        self.config.scale = newSize
        for t in self.tiles:
            t.destroy()
        self.sequenceNP.removeNode()
        self.makeGrid()

    def nextSizeFunc(self, args):
        if (len(self.sizesToTry)):
            self._recreateGrid(self.sizesToTry.pop(0))
        else:
            printOut("sizes completed!")
            self.sendMessage('end_' + self.config.name)

    def changeSize(self, scale):
        """
        Create a new grid, bigger or smaller, and re-shuffled.
        :param scale: scale factor to increase
        :return: nothing.
        """
        self._recreateGrid(self.config.scale*scale)

    # center of tile for any size and pos
    def makePos(self,t, w, h, x ,y, margin = 1.0):
        """
        Compute the center of a tile in the grid
        :param t: Tile size
        :param w: Grid width
        :param h: Grid height
        :param x: tile pos, from 1..N
        :param y: tile pos, from 1..N
        :param margin: and additional distance away from the center
        :return: Tuple containing x,y center position of the tile
        """
        return ((-w*t/2-t/2 + x*t)*margin,(h*t/2+t/2 - y*t)*margin)

    def makeGrid(self):
        """
        Create the game grid tiles and put them in place, IN ORDER.
        So the puzzle is solved after this.
        :return: None
        """
        gridWidth = self.config.gridWidth
        gridHeight = self.config.gridHeight
        tileSize = self.config.scale

        tilesNames = range(1,gridWidth*gridHeight + 1)
        random.shuffle(tilesNames)
        self.tiles = []
        margin = getattr(self.config, 'margin', 1.0)
        # background
        for y in range(0,gridHeight):
            for x in range(0,gridWidth):
                sx,sy = self.makePos(tileSize,gridWidth,gridHeight,x+1,y+1, margin)
                # column order
                self.tiles.append(self.makeTile(sx,sy, tileSize/2, tilesNames[x+y*gridWidth]))
                # listen to mouse
                self.tiles[-1].bind(DGG.B1PRESS, self.clicked, extraArgs=[tilesNames[x+y*gridWidth]])

        self.correctSequence = range(1,gridWidth*gridHeight + 1)
        random.shuffle(self.correctSequence)

        textVersion = str(self.correctSequence).replace('[','').replace(']','')
        sequenceText = TextNode('sequence')
        sequenceText.setAlign(TextNode.ACenter)
        sequenceText.setText(textVersion)
        textNP = NodePath(sequenceText)
        textNP.setScale(0.2)
        textNP.setPos(0.0,0,0.8)
        textNP.reparentTo(self.hudNP)
        self.sequenceText = sequenceText
        self.sequenceNP = textNP


    def unlockFunc(self):
        self.locked=False

    def clicked(self, tileId, who='mouse'):
        """
        Method called when the user presses the mouse
        When each tile is created, a method is bound to the NodePath, so I do not
        have to check if it is valid here.
        So far, the "mouse" can call by clicking, or the method "shuffle" when shuffling
        the grid.
        :param tileId: Receive the tileId where the user clicked
        :param who: who has called this method (just a string with semantics...)
        :return: None
        """
        correct = False

        if len(self.correctSequence) > 0 and tileId == self.correctSequence[0]:

            correct = True

            mouseX,mouseY = base.mouseWatcherNode.getMouse()

            cam = self.config.world.getCamera()
            width,height = map(float,(cam.screenWidth,cam.screenHeight))

            eyeX,eyeY = (0,0)
            try:
                eyeX,eyeY = self.eyeTracker.getLastSample()
            except:
                pass

            # find the tile using the tileId (slow way)
            tile = [x for x in self.tiles if int(x.getName()) == tileId][0]
            tile.setColor(0.2,0.0,0.0,0.5)
            tile['frameColor'] = (.5,.5,.5,0.5)

            # result, tile centre, mouse clicked, eye-gaze pos
            outString = "correct, %.4f, %s,%.4f %.4f, %.4f %.4f, %.4f %.4f" %\
                        (
                            self.config.scale,                          # size %
                            tileId,                                     # colour
                            tile.getPos().getX(),tile.getPos().getZ(),  # tile center
                            (width / height)*mouseX, float(mouseY),     # mouse pos
                            eyeX,eyeY                                   # gaze pos
                        )
            self.logFile.logEvent(outString)

            self.correctSequence.pop(0)

            # are we done with this size of tile
            if len(self.correctSequence) == 0:
                taskMgr.doMethodLater(1.0,self.nextSizeFunc,'nextSizeFun')


    def printPuzzle(self):
        print self.checkResult()

    def checkResult(self):
        """
        Check that the numbers have been all selected.
        :return: boolean
        """
        w = self.config.gridWidth
        h = self.config.gridHeight
        return False

    def makeTile(self,x,y,size,tileId):
        frameColor = self.config.color_tile
        order = 10
        relief=DGG.RAISED

        myFrame = DirectFrame(frameColor=frameColor,scale=size,
                              frameSize=(-1, 1, -1, 1), pos=(x, 0, y),
                              sortOrder=order, state=DGG.NORMAL,
                              parent = self.hudNP, relief=relief)
        myFrame.setName(str(tileId))

        textN = TextNode(str(x)+str(y))
        textN.setAlign(TextNode.ACenter)
        textN.setText(str(tileId))
        textNP = NodePath(textN)
        textNP.setScale(self.config.textSize/size)

        textNP.setPos(-textNP.getScale()/10)
        textNP.reparentTo(myFrame)
        return myFrame

    def pressed(self):
        pass

    def enterState(self):
        # super class enterState
        Element.enterState(self)
        if not getattr(self.config, 'textSize', None):
            setattr(self.config,'textSize',0.05)
        # force a copy of the list
        self.sizesToTry = list(self.config.tileSizes)
        random.shuffle(self.sizesToTry)
        self.config.scale = self.sizesToTry.pop(0)
        self.locked=False
        # recreate the grid if this is not the first time
        if getattr(self,'tiles', False):
            self._recreateGrid(self.config.scale)
        else:
            self.makeGrid()

    def exitState(self):
        # super class leaveState
        Element.exitState(self)
