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

from Element import *

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
        # this defines:
        # self.sceneNP and self.hudNP
        # self.config.world

        self.locked=False
        # start a new grid
        self.makeGrid()
        # add UI elements to enlarge/shrink grid
        self.addButtonsBigSmall()
        # shuffle the grid from its original correct order.
        #self.shuffle()
        self.hideElement()

    def showElement(self):
        Element.showElement(self)
        self.resetGame()

    def resetGame(self):
        pass

    def addButtonsBigSmall(self):
        self.bigger = DirectButton(parent = self.hudNP,
                                      text="Bigger", #pad=pad0,
                                      scale=0.08,
                                      pad=(.1,.1),
                                      pos=(0.6, 0, -0.9),
                                      command=self.changeSize,
                                      extraArgs=[1.5])

        self.smaller = DirectButton(parent = self.hudNP,
                                      text="Smaller", #pad=pad0,
                                      pad=(.1,.2),
                                      scale=0.082,
                                      pos=(1.0, 0, -0.906),
                                      command=self.changeSize,
                                      extraArgs=[0.5])

        self.shuffleButton = DirectButton(parent = self.hudNP,
                                      text="Shuffle", #pad=pad0,
                                      pad=(.1,.2),
                                      scale=0.082,
                                      pos=(0.1, 0, -0.906),
                                      command=self.changeSize,
                                      #state=0, # disabled
                                      extraArgs=[1.0])
        #self.shuffleButton.setTransparency(TransparencyAttrib.MAlpha)
        #self.shuffleButton.setAlphaScale(0.3)


    def changeSize(self, scale):
        """
        Create a new grid, bigger or smaller, and re-shuffled.
        :param scale: scale factor to increase
        :return: nothing.
        """
        self.config.scale *= scale
        for t in self.tiles:
            t.destroy()
        self.sequenceNP.removeNode()

        self.makeGrid()
        #self.shuffle()
        #self.resetGame()

    # center of tile for any size and pos
    def makePos(self,t, w, h, x ,y):
        """
        Compute the center of a tile in the grid
        :param t: Tile size
        :param w: Grid width
        :param h: Grid height
        :param x: tile pos, from 1..N
        :param y: tile pos, from 1..N
        :return: Tuple containing x,y center position of the tile
        """
        return (-w*t/2-t/2 + x*t,h*t/2+t/2 - y*t)

    def makeGrid(self):
        """
        Create the game grid tiles and put them in place, IN ORDER.
        So the puzzle is solved after this.
        :return: None
        """
        gridWidth = self.config.gridWidth
        gridHeight = self.config.gridHeight
        tileSize = self.config.scale

        tilesNames = range(0,gridWidth*gridHeight)
        random.shuffle(tilesNames)
        self.tiles = []

        # background
        for y in range(0,gridHeight):
            for x in range(0,gridWidth):
                sx,sy = self.makePos(tileSize,gridWidth,gridHeight,x+1,y+1)
                # column order
                self.tiles.append(self.makeTile(sx,sy, tileSize/2, tilesNames[x+y*gridWidth]))
                # listen to mouse
                self.tiles[-1].bind(DGG.B1PRESS, self.clicked, extraArgs=[tilesNames[x+y*gridWidth]])

        self.correctSequence = range(0,gridWidth*gridHeight)
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
        if len(self.correctSequence) > 0 and tileId == self.correctSequence[0]:
            tile = [x for x in self.tiles if int(x.getName()) == tileId]
            tile[0].setColor(1.0,0.0,0.0,0.3)
            self.correctSequence.pop(0)



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
        textNP.setScale(1.5)
        textNP.setPos(-0.1,0,-0.2)
        textNP.reparentTo(myFrame)
        return myFrame

    def pressed(self):
        pass

    def enterState(self):
        # super class enterState
        Element.enterState(self)

    def exitState(self):
        # super class leaveState
        Element.exitState(self)
