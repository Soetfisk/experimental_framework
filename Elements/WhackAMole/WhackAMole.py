#sys utils
import sys
import time
import random
from collections import OrderedDict

# panda imports
#from direct.gui import OnscreenImage
#from direct.showbase.DirectObject import DirectObject
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.DirectGui import *
from direct.task.Task import *
from panda3d.core import *
from direct.interval.MetaInterval import *
from direct.interval.FunctionInterval import *
from direct.interval.IntervalGlobal import *

# framework imports
from Elements.Element.Element import *



class GrassTile(object):
    def __init__(self, textures, parent, pos, size):
        self.grassNP = loader.loadModel("Elements/WhackAMole/models/plane")
        self.grassNP.setScale(size,1.0,size)
        self.grassNP.setPos((pos[0],0,pos[1]))
        self.grassNP.setTexture(textures['plainGrass'])
        self.grassNP.setTransparency(TransparencyAttrib.MAlpha)
        self.grassNP.reparentTo(parent)

class MoleHole(DirectObject.DirectObject):
    def __init__(self, textures, moleNP, parent,pos, size):

        self.textures = textures
        self.nodePaths=OrderedDict()
        # use an ordered dict as the Aspect2D node does not have order!!!
        # or use node.reparent(parent, order)

        self.moleHole = NodePath('mole')
        self.moleHole.setScale(size,1.0,size)
        self.moleHole.setPos((pos[0],0,pos[1]))
        self.moleAnim = moleNP.find('**/+SequenceNode').node()

        self.nodePaths['back'] = loader.loadModel("Elements/WhackAMole/models/plane")
        self.nodePaths['holeTop'] = loader.loadModel("Elements/WhackAMole/models/plane")
        #self.nodePaths['mole'] = loader.loadModel("Elements/WhackAMole/models/plane")
        self.nodePaths['mole'] = moleNP
        self.nodePaths['holeBottom'] = loader.loadModel("Elements/WhackAMole/models/plane")

        for k,v in self.nodePaths.items():
            if k!='mole':
                v.setTexture(textures[k])
            v.setTransparency(TransparencyAttrib.MAlpha)
            v.reparentTo(self.moleHole)

        self.nodePaths['holeTop'].setPos((0.0,0.0,size))
        self.nodePaths['holeTop'].setScale(1.0,1.0,0.5)

        self.nodePaths['holeBottom'].setPos((0.0,0.0,-size))
        self.nodePaths['holeBottom'].setScale(1.0,1.0,0.5)

        self.nodePaths['back'].setPos(0.0,0.0,0.0)
        self.nodePaths['mole'].setPos(0.0,0.0,-size - 0.05)
        self.nodePaths['mole'].setScale(0.5,1.0,0.5)

        self.moleHole.reparentTo(parent)
        self.moving = False
        self.moleIsDown = True
        self.size = size

           #     self.imageNodeA.setTransparency(TransparencyAttrib.MAlpha)

    def getMoleAnim(self):
        return self.moleAnim

    def moleUp(self):
        self.moleAnim.pose(0)
        if (not self.moleIsDown) or self.moving:
            return

        self.moving = True
        mole = self.nodePaths['mole']
        l = LerpPosInterval(mole, 0.7, Vec3(0,0,self.size/2.0), blendType='easeOut')
        l.setDoneEvent('moleUp')
        self.acceptOnce('moleUp', self.flipMoving, extraArgs=['up'])
        l.start()

    def flipMoving(self, dir):
        if dir == 'up':
            self.moleIsDown = False
        else:
            self.moleIsDown = True
            self.moleAnim.pose(0)
        self.moving = False

    def moleDown(self):
        if self.moleIsDown or self.moving:
            return
        self.moving = True
        mole = self.nodePaths['mole']
        l = LerpPosInterval(mole, 1, Vec3(0,0,-self.size - 0.05), blendType='easeOut')
        l.setDoneEvent('moleDown')
        self.acceptOnce('moleDown', self.flipMoving, extraArgs=['down'])
        l.start()

class WhackAMole(Element):
    """
    WhackAMole game to perform a hidden calibration
    """

    def __init__(self, **kwargs):
        super(WhackAMole,self).__init__(**kwargs)
        # one whack-a-mole
        textures={}
        # which mole is up, if any, and hit count
        self.moleUp = None
        self.moleUpHitCount = 0
        # lists for moles and grass tiles
        self.moles=[]
        self.calibPoints=[]
        self.grass=[]
        self.moleIsDown = False


        try:
            names = ['fname_holeTop','fname_holeBottom','fname_back','fname_plainGrass']
            for name in names:
                t=loader.loadTexture(getattr(self.config,name))
                t.setWrapU(Texture.WMClamp)
                t.setWrapV(Texture.WMClamp)
                t.setMinfilter(Texture.FTLinearMipmapLinear)
                t.setAnisotropicDegree(2)
                textures[name[6:]] = t
        except Exception,e:
            printOut("Error building mole holes!: %s"%e,0)

        gridSize = self.config.gridSize

        # holes in the corners
        fixedHoles = [(0,0), (0,gridSize-1), (gridSize-1,0), (gridSize-1,gridSize-1)]
        fixedCalibPoints = []

        size = 2.0/gridSize
        for r in range(0,gridSize):
            for c in range(0,gridSize):
                pos = (-1 + size/2 + c*size, 1 + size/2 - (r+1)*size)
                # a 0 in (0,4) means 1/5 chance of being a 0
                # we always put moles in the corners
                if random.randint(0,4)==0 or (r,c) in fixedHoles:
                    moleNP = loader.loadModel(self.config.fname_moleModel)
                    self.moles.append(MoleHole(textures, moleNP,self.hudNP,pos, size))
                    if (r,c) in fixedHoles:
                        fixedCalibPoints.append(len(self.moles)-1)
                    self.calibPoints.append(len(self.moles)-1)
                    self.moles[-1].getMoleAnim().pose(0)
                    self.moles[-1].getMoleAnim().setPlayRate(8)
                else:
                    self.grass.append(GrassTile(textures,self.hudNP,pos,size))

        self.hammer = loader.loadModel("Elements/WhackAMole/models/hammer.egg")
        self.hammer.setTransparency(1)
        self.hammer.setAlphaScale(0.6)
        self.hammerAnim = self.hammer.find('**/+SequenceNode').node()
        self.hammerAnim.pose(0)
        self.hammer.setScale(0.5,0.5,0.5)
        self.hammer.reparentTo(self.hudNP)

        self.hammerAnim.setPlayRate(-1.5)
        self.camRatio = self.config.world.camera.ratio

        # remove some calibration points until reaching the limit from the config file
        while len(self.calibPoints) > self.config.moleCalibPoints:
            x = random.choice([y for y in self.calibPoints if y not in fixedCalibPoints])
            self.calibPoints.remove(x)

        self.lastTime=time.time()
        self.randomWaitForUp = random.randint(1,2)
        self.waitForDown = self.config.waitForDown
        self.hideElement()

    def hammerMouse(self, task):
        # update hammer position based on the mouse position
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            self.hammer.setPos((mpos[0] * self.camRatio,0,mpos[1]))
        return task.again

    def moleFirstHit(self):
        if self.moleUp==None:
            return
        moleAnim = self.moles[self.moleUp].getMoleAnim()
        moleAnim.play(0,3)

    def moleSecondHit(self):
        if self.moleUp==None:
            return
        moleAnim = self.moles[self.moleUp].getMoleAnim()
        moleAnim.play(3,5)
        #self.hideMole()

    def moleThirdHit(self):
        if self.moleUp==None:
            return
        moleAnim = self.moles[self.moleUp].getMoleAnim()
        moleAnim.play(5,6)

    def hammerDown(self):
        cam = self.config.world.getCamera()
        w,h = map(float,(base.win.getXSize(),base.win.getYSize()))

        if self.hammerAnim.getFrame()!=0:
            return
        self.hammerAnim.play()

        if self.moleUp!=None:
            # the hammer is a SPRITE!
            bounds = self.hammer.getTightBounds()
            topY = bounds[1].getZ()
            bottomY = bounds[0].getZ()
            pos = self.hammer.getPos()
            pos[2] = (topY - (topY - bottomY)*0.35)
            molePos = self.moles[self.moleUp].moleHole.getPos()
            # is the hammer hitting the mole ?
            dist = (pos - molePos).length()
            if dist > 0.05:
                return
            else:
                # there was a hit!
                # this is the first hit
                if self.moleUpHitCount == 0:

                    calibPoint = ( (molePos[0]+(w/h)) / (2*(w/h)) , -0.5 * molePos[2] + 0.5)
                    print calibPoint
                    # normalize calibration point, screen is in 2D.
                    # width in [ -w/h, w/h ]
                    # height in [ 1, -1 ]
                    # Eye-tracker is top left (0,0), bottom right (1,1)
                    self.lastCalibPointSent = calibPoint
                    # ONLY ADD CALIBRATION POINT ON THE FIRST HIT
                    # TODO: If there was an error adding the calibration point, I do not really
                    # TODO: know here if that happened!!!!
                    self.eyeTracker.addCalibrationPoint(calibPoint[0], calibPoint[1])
                    self.moleFirstHit()
                # this is the second hit
                elif self.moleUpHitCount == 1:
                    self.moleSecondHit()
                elif self.moleUpHitCount == 2:
                    self.moleThirdHit()
                # more than 2 hits
                else:
                    pass
                self.moleUpHitCount+=1

#====================================================================

    def showElement(self):
        pass
        #self.imageNodeA.show()
        #self.imageNodeB.show()

    def hideElement(self):
        self.hudNP.hide()

    def enterState(self):
        Element.enterState(self)
        self.hudNP.show()
        self.config.world.hideMouseCursor()
        taskMgr.add(self.hammerMouse, "hammerController", sort=2)
        taskMgr.add(self.updateGame,'whack-a-mole')
        self.config.world.accept('moleUp', self.moleMoved,['up'])
        self.config.world.accept('moleDown', self.moleMoved,['down'])
        try:
            # save current calibration with participant id as normal calibration
            # save is SYNCHRONOUS ON THE TOBII
            self.eyeTracker.saveCalibration( str(self.config.world.participantId) + '_tobii' + '.cal' )
            time.sleep(0.1)
            # START IS ASYNC ON THE TOBII SIDE
            self.eyeTracker.startCalibration()
        except Exception,e:
            print e

    def moleMoved(self, where):
        if where == 'down':
            self.moleIsDown = True
        else:
            self.moleIsDown = False

    def updateGame(self, task):
        if len(self.calibPoints)==0 and self.moleIsDown:
            taskMgr.doMethodLater(2.0, self.sendMessage, 'calibration finished', extraArgs=['calibrationFinished'])
            return task.done
        # if None it means there is no mole up
        elapsed = time.time()-self.lastTime
        if self.moleUp != None:
            if (self.moleUpHitCount > 2 or elapsed > self.waitForDown):
                self.moles[self.moleUp].moleDown()
                if (self.moleUpHitCount>2):
                    # remove element at index moleUp
                    self.calibPoints.remove(self.moleUp)
                self.moleUpHitCount = 0
                self.moleUp = None
                self.lastTime=time.time()
            return task.cont
        else:
            # no mole is up
            # should we put a mole up ?
            if (elapsed > self.randomWaitForUp):
                # update for next iteration the randomWait
                self.randomWaitForUp = random.randint(3,5)
                # moleUp is an INDEX into the Moles list, and calibPoints contains indices!
                self.moleUp = random.choice(self.calibPoints)
                self.moles[self.moleUp].moleUp()
                self.lastTime = time.time()
            return task.cont

    def exitState(self):
        self.unregisterKeys()
        try:
            self.config.world.showMouseCursor()
            self.eyeTracker.stopCalibration()
            time.sleep(1.0)
            self.eyeTracker.saveCalibration( str(self.config.world.participantId) + '_mole' + '.cal' )
            #self.eyeTracker.stopTracking()
        except Exception,e:
            print e
        Element.exitState(self)

