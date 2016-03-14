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
from Logger import Logger

#sys utils
import sys

#from Elements.EyeTracker.Tobii import TobiiEyeTracker

class SelectColours(Element):
    """
    Little sliding tile puzzle game
    """

    def __init__(self, **kwargs):
        # build parent object class
        super(SelectColours, self).__init__(**kwargs)
        # this defines:
        # self.sceneNP and self.hudNP
        # self.config.world

        self.locked=False

        colours = [
            (200,0,0,255), (254,155,14,255), (243,254,30,255),
            (0,240,0,255), (0,254,229,255), (17,41,254,255),
            (197,16,253,255), (120,10,255,255), (0,0,0,255) ]
        m = 255.0
        self.colours = [(r/m,g/m,b/m,a/m) for (r,g,b,a) in colours]

        self.colours_names = [ str(c) for c in colours ]

        self.sizesToTry = self.config.tileSizes
        random.shuffle(self.sizesToTry)
        self.config.scale = self.sizesToTry.pop(0)

        # start a new grid
        self.makeGrid()

        self.logFile = Logger("run/selectColours_%s.txt" % self.config.world.participantId, 'w')

        # add UI elements to enlarge/shrink grid
        self.addButtonsBigSmall()
        # shuffle the grid from its original correct order.
        #self.shuffle()
        self.hideElement()

    def mouseClicked(self):
        mouseX = base.mouseWatcherNode.getMouseX()
        mouseY = base.mouseWatcherNode.getMouseY()
        print mouseX, mouseY

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
                                      extraArgs=[1.1])

        self.smaller = DirectButton(parent = self.hudNP,
                                      text="Smaller", #pad=pad0,
                                      pad=(.1,.2),
                                      scale=0.082,
                                      pos=(1.0, 0, -0.906),
                                      command=self.changeSize,
                                      extraArgs=[0.9])

        self.shuffleButton = DirectButton(parent = self.hudNP,
                                      text="Shuffle", #pad=pad0,
                                      pad=(.1,.2),
                                      scale=0.082,
                                      pos=(0.1, 0, -0.906),
                                      command=self.changeSize,
                                      #state=0, # disabled
                                      extraArgs=[1.0])

        self.nextSizeButton = DirectButton(parent = self.hudNP,
                                      text="Next", #pad=pad0,
                                      pad=(.1,.2),
                                      scale=0.082,
                                      pos=(-0.5, 0, -0.906),
                                      command=self.nextSizeFunc)

 #self.shuffleButton.setTransparency(TransparencyAttrib.MAlpha)
        #self.shuffleButton.setAlphaScale(0.3)

    def _recreateGrid(self, newSize):
        self.config.scale = newSize
        for t in self.tiles:
            t.destroy()
        for t in self.correctTiles:
            t.destroy()
        self.makeGrid()

    def nextSizeFunc(self):
        if (len(self.sizesToTry)):
            self._recreateGrid(self.sizesToTry.pop(0))
        else:
            printOut("sizes completed!")

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

        temp = [ x for x in self.colours_names ]
        random.shuffle(temp)
        self.tiles = []
        self.correctTiles = []
        self.currentTile = 0

        margin = getattr(self.config, 'margin', 1.0)

        # tile grid
        for y in range(0,gridHeight):
            for x in range(0,gridWidth):
                sx,sy = self.makePos(tileSize,gridWidth,gridHeight,x+1,y+1, margin)
                # column order
                self.tiles.append(self.makeTile(sx,sy, tileSize/2, temp[x+y*gridWidth]))
                # listen to mouse
                self.tiles[-1].bind(DGG.B1PRESS, self.clicked, extraArgs=[temp[x+y*gridWidth]])

        # sequence at the top, re-shuffle!
        random.shuffle(temp)
        totalWidth = gridWidth*gridHeight*(0.21)
        for y in range(0,gridHeight):
            for x in range(0,gridWidth):
                # column order
                self.correctTiles.append(self.makeTile(
                    -totalWidth/2.0 + 0.1 + (gridWidth*y)*0.21 + x*0.21,0.8, 0.1, temp[x+y*gridWidth]))
#
        #self.correctSequence = range(0,gridWidth*gridHeight)
        #random.shuffle(self.correctSequence)

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
        if self.currentTile < len(self.correctTiles) and tileId == self.correctTiles[self.currentTile].getName():

            correct = True

            mouseX,mouseY = base.mouseWatcherNode.getMouse()

            cam = self.config.world.getCamera()
            width,height = map(float,(cam.screenWidth,cam.screenHeight))
            tile = self.correctTiles[self.currentTile]

            self.logFile.logEvent("correct tile clicked: %s" % tileId)
            #self.logFile.logEvent("tileCenter: %.4f %.4f" % (tile.getPos().getX(),tile.getPos().getZ()))
            self.logFile.logEvent("tileCenter: %.4f" % (tile.getPos().getX()))
            #self.logFile.logEvent("mouseClicked: %.4f %.4f" % ((width / height)*float(mouseX), mouseY))

            try:
                self.logFile.logEvent("EyeGaze reported: %.4f %.4f" % self.eyeTracker.getLastSample())
            except:
                pass

            self.correctTiles[self.currentTile]['frameColor'] = (0,0,0,0.1)
            self.currentTile+=1

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
        # colours from http://lemerg.com/data/wallpapers/11/823577.jpg


        frameColor = self.colours[self.colours_names.index(tileId)]
        order = 10
        relief=DGG.GROOVE #DGG.SUNKEN

        myFrame = DirectFrame(frameColor=frameColor,scale=size,
                              frameSize=(-1, 1, -1, 1), pos=(x, 0, y),
                              sortOrder=order, state=DGG.NORMAL,
                              parent = self.hudNP, relief=relief,
                              borderWidth = (0.05,0.05))
        myFrame.setName(str(tileId))

        #textN = TextNode(str(x)+str(y))
        #textN.setAlign(TextNode.ACenter)
        #textN.setText(str(tileId))
        #textNP = NodePath(textN)
        #textNP.setScale(1.5)
        #textNP.setPos(-0.1,0,-0.2)
        #textNP.reparentTo(myFrame)
        return myFrame

    def pressed(self):
        pass

    def enterState(self):
        # super class enterState
        Element.enterState(self)
        self.logFile.startLog()

    def exitState(self):
        # super class leaveState
        self.logFile.stopLog()
        Element.exitState(self)
