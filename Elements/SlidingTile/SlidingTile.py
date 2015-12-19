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

from Elements.EyeTracker.Tobii import TobiiEyeTracker

class SlidingTile(Element):
    """
    Little sliding tile puzzle game
    """

    def __init__(self, **kwargs):
        """
        world is a reference to the main class
        text: is the name of the node in the XML config
        """
        # build basic element
        super(SlidingTile, self).__init__(**kwargs)
        # this defines:
        # self.sceneNP and self.hudNP
        self.locked=False
        self.makeGrid()
        self.addButtonsBigSmall()
        self.shuffle()
        self.hideElement()
        self.tracker = TobiiEyeTracker()
        self.tracker.initLibrary()


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

    def changeSize(self, scale):
        self.config.scale *= scale
        for t in self.tiles:
            t.destroy()
        self.makeGrid()
        self.shuffle()

    # center of tile for any size and pos
    def makePos(self,t, w, h, x ,y):
        return (-w*t/2-t/2 + x*t,h*t/2+t/2 - y*t)

    def makeGrid(self):
        gridWidth = self.config.gridWidth
        gridHeight = self.config.gridHeight
        tileSize = self.config.scale

        tilesNames = range(0,gridWidth*gridHeight)
        #rnd.shuffle(tilesNames)
        self.tiles = []

        # background
        for y in range(0,gridHeight):
            for x in range(0,gridWidth):
                sx,sy = self.makePos(tileSize,gridWidth,gridHeight,x+1,y+1)
                # column order
                self.tiles.append(self.makeTile(sx,sy, tileSize/2, tilesNames[x+y*gridWidth]))
                self.tiles[-1].bind(DGG.B1PRESS, self.clicked, extraArgs=[tilesNames[x+y*gridWidth]])

    def unlockFunc(self):
        self.locked=False

    def swapTiles(self, tileA, tileB, anim=True):

        temp = self.tiles[tileA]
        self.tiles[tileA] = self.tiles[tileB]
        self.tiles[tileB] = temp

        if anim:
            AtoB = LerpPosInterval(self.tiles[tileA], 0.2, self.tiles[tileB].getPos(), blendType='easeOut')
            BtoA = LerpPosInterval(self.tiles[tileB], 0.2, self.tiles[tileA].getPos(), blendType='easeOut')
            self.locked=True
            AtoB.setDoneEvent('unlock')
            messenger.accept('unlock', self, self.unlockFunc)
            AtoB.start()
            BtoA.start()
        else:
            tempPos = self.tiles[tileA].getPos()
            self.tiles[tileA].setPos(self.tiles[tileB].getPos())
            self.tiles[tileB].setPos(tempPos)

    def clicked(self, tileId, who):
        if self.locked:
            return

        anim=True
        if who == 'shuffle':
            anim=False

        pos = 0
        w = self.config.gridWidth
        h = self.config.gridHeight
        empty = str(w*h-1)
        while self.tiles[pos].getName()!=str(tileId):
            pos=pos+1
        rb = (pos % w == w-1)
        lb = (pos % w == 0)
        tb = (pos / w == 0)
        bb = (pos / w == h-1)
        if (not rb) and self.tiles[pos+1].getName()==empty:
            self.swapTiles(pos,pos+1,anim)
            return
        if (not lb) and self.tiles[pos-1].getName()==empty:
            self.swapTiles(pos,pos-1,anim)
            return
        if (not tb) and self.tiles[pos-w].getName()==empty:
            self.swapTiles(pos,pos-w,anim)
            return
        if (not bb) and self.tiles[pos+w].getName()==empty:
            self.swapTiles(pos,pos+w,anim)
            return

    def shuffle(self):
        for i in range(100):
            self.clicked(random.randint(0,self.config.gridWidth*self.config.gridHeight - 1), 'shuffle')

    def printPuzzle(self):
        print self.checkResult()

    def checkResult(self):
        w = self.config.gridWidth
        h = self.config.gridHeight
        if self.tiles[w*h-1].getName()!=str(w*h-1):
            return False
        for i in range(w*h - 2):
            if int(self.tiles[i].getName()) > int(self.tiles[i+1].getName()):
                return False
        return True

    def makeTile(self,x,y,size,tileId):
        frameColor = self.config.color_tile
        order = 10
        emptyPos = self.config.gridWidth*self.config.gridHeight-1
        relief=DGG.RAISED

        if tileId == emptyPos:
            frameColor = base.getBackgroundColor()
            order = 0
            relief = None

        myFrame = DirectFrame(frameColor=frameColor,scale=size,
                              frameSize=(-1, 1, -1, 1), pos=(x, 0, y),
                              sortOrder=order, state=DGG.NORMAL,
                              parent = self.hudNP, relief=relief)
        myFrame.setName(str(tileId))

        if tileId != emptyPos:
            textN = TextNode(str(x)+str(y))
            textN.setAlign(TextNode.ACenter)
            textN.setText(str(tileId))
            textNP = NodePath(textN)
            textNP.setPos(-0.1,0,-0.2)
            textNP.reparentTo(myFrame)

        return myFrame


    def pressed(self):
        pass

    def enterState(self):
        # print "entering ScreenText"
        # super class enterState
        Element.enterState(self)

    def exitState(self):
        # print "leaving state ScreenText"
        Element.exitState(self)
