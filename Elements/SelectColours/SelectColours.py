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

class SelectColours(Element):
    """
    Little sliding tile puzzle game
    """

    def __init__(self, **kwargs):
        # build parent object class
        super(SelectColours, self).__init__(**kwargs)

        self.colours_names = [ 'red', 'white', 'yellow', 'darkblue', 'darkgreen', 'magenta', 'brown', 'cyan', 'black' ]
        colours = [
            (250,0,0,255),      # red
            (254,254,254,255),  # white
            (255,255,0,255),    # yellow
            (0,0,150,255),      # dark blue
            (0,150,0,255),      # dark green
            (197,16,253,255),   # magenta
            (102,51,0,255),     # brown
            (0,255,255,255),    # cyan
            (0,0,0,255) ]       # black

        self.colours = [(r/255.0,g/255.0,b/255.0,a/255.0) for (r,g,b,a) in colours]


        # add UI elements to enlarge/shrink grid
        #self.addButtonsBigSmall()
        # shuffle the grid from its original correct order.
        #self.shuffle()
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
#                                      extraArgs=[1.1])
#
#        self.smaller = DirectButton(parent = self.hudNP,
#                                      text="Smaller", #pad=pad0,
#                                      pad=(.1,.2),
#                                      scale=0.082,
#                                      pos=(1.0, 0, -0.906),
#                                      command=self.changeSize,
#                                      extraArgs=[0.9])
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
        for t in self.correctTiles:
            t.destroy()
        self.makeGrid()

    def nextSizeFunc(self, args):
        if (len(self.sizesToTry)):
            self._recreateGrid(self.sizesToTry.pop(0))
        else:
            printOut("sizes completed!")
            self.sendMessage('end_' + self.config.name)

#    def changeSize(self, scale):
#        """
#        Create a new grid, bigger or smaller, and re-shuffled.
#        :param scale: scale factor to increase
#        :return: nothing.
#        """
#        self._recreateGrid(self.config.scale*scale)

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
                idx = x+y*gridWidth
                # send idx as an INT and the colour associated.
                self.tiles[-1].bind(DGG.B1PRESS, self.clicked, extraArgs=[idx, temp[idx]])

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

    def clicked(self, idx, tileId, who='mouse'):
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
            tile = self.tiles[idx]

            eyeX,eyeY = (0,0)
            try:
                eyeX,eyeY = self.eyeTracker.getLastSample()
            except:
                pass

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

            self.correctTiles[self.currentTile]['frameColor'] = (0,0,0,0.1)
            self.currentTile+=1
            # are we done with this size of tile
            if self.currentTile == len(self.correctTiles):
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

        self.locked=False
        try:
            # force a copy!
            self.sizesToTry = list(self.config.tileSizes)
        except:
            printOut("missing property 'tileSizes' in config file")
            self.config.world.quit()

        random.shuffle(self.sizesToTry)

        self.config.scale = self.sizesToTry.pop(0)
        # start a new grid, using self.config.scale, or recreate one if tiles already exist!
        if getattr(self,'tiles',False):
            self._recreateGrid(self.config.scale)
        else:
            self.makeGrid()

    def exitState(self):
        # super class leaveState
        Element.exitState(self)
