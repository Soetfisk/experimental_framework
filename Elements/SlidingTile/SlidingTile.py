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

#sys utils
import sys

#from Elements.EyeTracker.Tobii import TobiiEyeTracker

class SlidingTile(Element):
    """
    Little sliding tile puzzle game
    """

    def __init__(self, **kwargs):
        # build parent object class
        super(SlidingTile, self).__init__(**kwargs)
        # this defines:
        # self.sceneNP and self.hudNP
        # self.config.world

        # how many times has the user tried to do an invalid move.
        self.invalidMoves = 0
        # used to disable the interaction while the tile is animated.
        self.locked=False
        # start a new grid
        self.makeGrid()
        # add UI elements to enlarge/shrink grid
        self.addButtonsBigSmall()
        # shuffle the grid from its original correct order.
        self.shuffle()
        self.hideElement()
        #self.tracker = TobiiEyeTracker()
        #self.tracker.initLibrary()

    def showElement(self):
        Element.showElement(self)
        self.resetGame()

    def resetGame(self):
        self.invalidMoves = 0

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
                                      command=self.shuffle,
                                      state=0, # disabled
                                      extraArgs=[])
        self.shuffleButton.setTransparency(TransparencyAttrib.MAlpha)
        self.shuffleButton.setAlphaScale(0.3)

    def changeSize(self, scale):
        """
        Create a new grid, bigger or smaller, and re-shuffled.
        :param scale: scale factor to increase
        :return: nothing.
        """
        self.config.scale *= scale
        for t in self.tiles:
            t.destroy()
        self.makeGrid()
        self.shuffle()
        self.resetGame()

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
        """
        Blindly swap two tiles, it is assumed here that it is a valid move.
        Do the swap using an animation by default (LERP)
        Without animation is used to shuffle the puzzle
        :param tileA: fromTile, of type NodePath
        :param tileB: toTile, of type NodePath
        :param anim: animate or not the move.
        :return:
        """

        temp = self.tiles[tileA]
        self.tiles[tileA] = self.tiles[tileB]
        self.tiles[tileB] = temp

        if self.checkResult() and anim==True:
            self.shuffleButton.setAlphaScale(1.0)
            self.shuffleButton['state']=1               # enabled
            printOut("Puzzle solved!")

        if anim:
            AtoB = LerpPosInterval(self.tiles[tileA], 0.2, self.tiles[tileB].getPos(), blendType='easeOut')
            BtoA = LerpPosInterval(self.tiles[tileB], 0.2, self.tiles[tileA].getPos(), blendType='easeOut')
            self.locked=True
            # when the animation is done, call "self.unlockFunc"
            AtoB.setDoneEvent('unlock')
            messenger.accept('unlock', self, self.unlockFunc)
            AtoB.start()
            BtoA.start()
        else:
            # instant change
            tempPos = self.tiles[tileA].getPos()
            self.tiles[tileA].setPos(self.tiles[tileB].getPos())
            self.tiles[tileB].setPos(tempPos)

    def clicked(self, tileId, who='mouse'):
        """
        Method called when the user presses the mouse
        When each tile is created, a method is bound to the NodePath, so I do not
        have to check if it is valid here.
        So far, the "mouse" can call by clicking, or the method "shuffle" when shuffling
        the grid. When Shuffling, we dissable animation.
        :param tileId: Receive the tileId where the user clicked
        :param who: who has called this method (just a string with semantics...)
        :return: None
        """
        if self.locked:
            return

        anim=True
        if who == 'shuffle':
            anim=False

        # we need to check if it is a valid move in the grid.
        # a valid move means that the tile clicked has a white/blank
        # space in the north, east, west or south.
        pos = 0
        w = self.config.gridWidth
        h = self.config.gridHeight
        # empty tile has a name which matches the number of tiles, because it
        # is the number assigned when the grid is created in the solved state.
        empty = str(w*h-1)
        while self.tiles[pos].getName()!=str(tileId):
            pos=pos+1
        rb = (pos % w == w-1)       # right
        lb = (pos % w == 0)         # left
        tb = (pos / w == 0)         # top
        bb = (pos / w == h-1)       # bottom
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
        # if we reach this point, it has been an invalid move.
        self.invalidMoves += 1

    def shuffle(self):
        for i in range(500):
            self.clicked(random.randint(0,self.config.gridWidth*self.config.gridHeight - 1), 'shuffle')
        self.shuffleButton.setAlphaScale(0.3)
        self.shuffleButton['state'] = 0             # disable

    def printPuzzle(self):
        print self.checkResult()

    def checkResult(self):
        """
        Check if the puzzle is in a solved state, with numbers
        0,1,2,3,4...N and white space at the end.
        :return:
        """
        w = self.config.gridWidth
        h = self.config.gridHeight

        # quickly check what tile is where the white space should be.
        if self.tiles[w*h-1].getName()!=str(w*h-1):
            return False

        # check that tile N is before N+1 for every N
        for i in range(w*h - 2):
            if int(self.tiles[i].getName()) > int(self.tiles[i+1].getName()):
                return False
        else:
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
        # super class enterState
        Element.enterState(self)

    def exitState(self):
        # super class leaveState
        Element.exitState(self)
