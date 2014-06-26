# panda imports
from panda3d.core import *
from math import *
import time
import cPickle
from random import *
import sys

from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import *
from direct.interval.MetaInterval import *
from direct.interval.FunctionInterval import *
from direct.interval.IntervalGlobal import *
from direct.particles.ParticleEffect import ParticleEffect

from Utils.Debug import printOut

# utility classes
from PositionGenerator import PositionGenerator

# How to generate the parachutes during the game:
# - We have one possible target at any time.
# - Plus other parachutes (names) distracting the user
# - at most 6-7 parachutes all the time
# - We have to RENEW parachutes that reach the
#   floor:
#       - if it's the target, it has to appear up again
#       - if it's not, add a new random.

class Parachute(DirectObject):
    # class attribute to store textures
    texDict = {}
    parachuteTex = None
    # name: name for this instance of Parachute
    # parConf: config coming from YAML
    def __init__(self, world = None, name = "",
                 textureName = None, conf = None, collisions=True):
        # grab a reference to the class!, to use
        # class attributes, this is python :|
        cls = self.__class__

        if (world is None or textureName is None or
            conf is None):
            printOut("Bad call to create parachutes",0)
            sys.exit()

        self.name = name
        self.game = world
        self.posGen = world.posGen
        self.speed = conf.speed
        self.changeStep = conf.blendtype.blendfunction
        self.collisions = collisions

        self.forced = False
        self.falling = False
        # self.textures = {}
        # load textures for this model, unless it was loaded
        # before. All textures go to a class attribute.

        if (textureName not in cls.texDict):
            t = loader.loadTexture(textureName)
            t.setWrapU(Texture.WMClamp)
            t.setWrapV(Texture.WMClamp)
            t.setMinfilter(Texture.FTLinearMipmapLinear)
            t.setAnisotropicDegree(2)
            #self.textures[int(tex.level)] = t
            self.texture = t
            cls.texDict[textureName] = t
        else:
            self.texture = cls.texDict[textureName]
            #self.textures[int(tex.level)] = cls.texDict[tex.name]
        # when set to True, it will change it's resolution
        # depending on delay, immediately or after it gets
        # a new position.
        #self.delayLodChange  = True
        #self.lowerResolution = False
        #self.nextLod = 0

        self.isTarget = False

        # this is used when we don't wont bullets to hit him
        self.ignoreHit = False
        self.currentQ = 0

        # empty nodepath
        self.modelNP = NodePath("parachute_" + name)
        self.modelNP.setTransparency(1)

        # particle node to hold the particle system later.
        # self.particleNode = NodePath("dust_"+name)
        # self.particleNode.reparentTo(self.modelNP)

        # manual adjustments...
        # self.modelNP.setScale(self.game.rescaleFactor)

        # put the model anywhere hidden from the camera!!!
        self.modelNP.setPos(Vec3(-1000, 40, 0))

        # parachuteTex is a class attribute!
        if cls.parachuteTex is None:
            cls.parachuteTex = loader.loadTexture("PilotData/models/textures/para_tex.png")
            cls.parachuteTex.setMinfilter(Texture.FTLinearMipmapLinear)
            cls.parachuteTex.setAnisotropicDegree(2)

        self.paraModel = loader.loadModel("PilotData/models/para02.egg")
        self.paraModel.setScale(Vec3(0.3, 0.2, 0.2))
        self.paraModel.setPos(Vec3(0, 0.15, 1.2))

        # generate automatically UV coordinates:
        #self.paraModel.setTexGen(TextureStage.getDefault(), TexGenAttrib.MWorldPosition)
        #self.paraModel.setTexProjector(TextureStage.getDefault(), render, self.paraModel)

        # assign texture
        self.paraModel.setTexture(cls.parachuteTex)
        self.paraModel.reparentTo(self.modelNP)

        # parachute is a billboard
        self.model = loader.loadModel("Elements/Game/models/plane")
        # pos actual model below the modelNP
        # away from the view until it gets a random position.
        self.model.setPos(Vec3(0, 0, -0.5))
        #self.model.setBillboardAxis()
        self.model.setTransparency(1)
        # set texture with maximum quality.
        #self.model.setTexture(self.textures[self.currentQ], 1)
        self.model.setTexture(self.texture, 1)

        #self.game.replayLog.logEvent("Q:[\'"+self.config.name+"\',"+str(self.currentQ)+"]\n", 0.0)
        self.model.reparentTo(self.modelNP)

        if self.collisions:
            # add collision sphere to modelNP
            colSolid = CollisionSphere(0, 0, 0, 0.5)
            colNP = self.modelNP.attachNewNode(CollisionNode(self.name))
            colNP.setPos(0, 0 ,-0.5)
            colNP.setCollideMask(BitMask32(0x80))
            colNP.node().addSolid(colSolid)

            # react to event of collision events
            self.accept('hit-'+self.name, self.hit)
        #self.accept('b', self.decreaseQ)
        #self.accept('m', self.increaseQ)

    """
    def updateLod(self, anEvent):
        # specifc code for each type of event
        if (anEvent.getEventType == "CYCLE"):
            if (anEvent.cycleNumber == self.lodConfig.cycles):
                # change from Qi to Qj in time t
                self.setTexture(-1,int(self.lodConfig.change2Lod),1)
    """


    def setTexture(self,toQ,inTime):

        if ((toQ >= len(self.textures)) or (toQ < 0)): return


        # if the change has to happen when the model
        # its renewing it's possition.
        if (not self.lowerResolution and self.delayLodChange):
            self.lowerResolution = True
            self.nextLod = toQ
            return

        self.lowerResolution = False
        self.model.setTexture(self.textures[toQ], 1)
        self.currentQ = toQ
        self.game.replayLog.logEvent("Q:[\'"+self.name+"\',"+str(toQ)+"]\n", time.time())

    def forceTexture(self,quality):
        if (quality < 0 or quality >= len(self.textures)):
            printOut("Warning, trying to set invalid quality: %s" % quality, 0)
            return
        self.model.setTexture(self.textures[quality], 1)
        self.currentQ = quality
        return

    # increase texture quality by 1
    def increaseQ(self):
        self.setTexture( self.currentQ-1, 1)

    # decrease texture quality by 1
    def decreaseQ(self):
        self.setTexture( self.currentQ+1, 1)

    def hit(self,entry):
        """ this function is called automatically by the collision
        detection algorithm, so if we actually want to ignore the hit
        we have to do it here."""

        # do we care about hits in this parachute?
        if (self.ignoreHit):
            return

        # are we the current target to shoot at?
        if (self.game.validHit(self.name) != True):
            return
        else:
            self.hitted = True
            self.ignoreHit = True
            taskMgr.doMethodLater(0.4,self.modelNP.hide,'hideParachute',extraArgs=[])
            taskMgr.doMethodLater(0.5,self.fallInterval.finish,'finishInterval',extraArgs=[])
            fadeOut = LerpFunctionInterval(self.modelNP.setAlphaScale,
                    toData=0.0,fromData=1.0,duration=0.3)
            fadeOut.start()
            #self.falling = False

    def swingTheThing(self,t):
        self.modelNP.setR((self.maxangle*t - self.maxangle/2.0) *
                           self.modelNP.getZ()/self.maxHeight)
        return

    def pauseFall(self):
        if self.falling:
            self.fallInterval.pause()

    def unPauseFall(self):
        if self.falling:
            self.fallInterval.start()

    def newPos(self, d = 0, x = 0, y = 0, z = 0, forced = False):
        self.forced = forced

        # check if need to lower the texture
        #if (not self.forced and self.lowerResolution):
        #    self.setTexture(self.nextLod,1)

        # swipe time
        self.modelNP.show()
        self.time = 2.0
        self.maxangle = 30.0
        self.groundHeight = -35

        # fall setup
        # grab a random position
        #if (self.isTarget):
        #    d = 0
        #else:
        #    d = 135

        if (not self.forced):
            pos = self.posGen.getNewPos(d)
            if pos is None:
                return -1
        # for the pilot
        else:
            pos = Vec3(x, y, z)

        self.modelNP.setPos(pos)
        self.maxHeight = self.modelNP.getZ()

        swing0 = LerpFunc(self.swingTheThing,
                          fromData=0.0,
                          toData=1.0,
                          duration=self.time,
                          blendType='easeInOut',
                          name="right_"+self.name)
        swing1 = LerpFunc(self.swingTheThing,
                          fromData=1.0,
                          toData=0.0,
                          duration=self.time,
                          blendType='easeInOut',
                          name="left_"+self.name)
        self.swingSeq = Sequence(swing0,swing1)
        self.swingSeq.loop()
        if not self.forced:
            self.swingSeq.setT(uniform(0, 1))

        # set fall time, interval and callback after fall
        #adjustedDuration = (self.modelNP.getZ() * self.falltime) / self.posGen.topLeft[2]
        adjustedDuration = (self.modelNP.getZ() - self.groundHeight) / self.speed
        printOut("Adjusted Duration of speed: %f" % adjustedDuration, 0)
        self.fallInterval = self.genFallDownInterval(adjustedDuration, self.groundHeight)

        self.fallInterval.setDoneEvent("finishedPreFall_" + self.name)

        self.acceptOnce("finishedPreFall_" + self.name, self.finishedPreFall)

        # rotation setup, creates a simple swing, and then a callback to keep
        # swinging
        #try:
        #    self.rotation.finish()
        #except(AttributeError):
        #    pass

        # all this crap is to have a random rotation position
        angle = uniform(0, self.maxangle) - self.maxangle / 2.0
        self.modelNP.setHpr(Vec3(0, 0, angle))
        #self.rot0 = LerpHprInterval(self.modelNP,
        #                           self.time - self.time *
        #                           abs((2 * angle) / self.maxangle),
        #                           Vec3(0, 0, self.maxangle / 2),
        #                           blendType='easeOut')
        #self.rot0.setDoneEvent("swing_" + self.name)
        #self.acceptOnce("swing_" + self.name, self.swing)

        # adjusts a bit the parachute so it looks exactly behind the robot when
        # the parachute is in one of either sides.
        self.paraModel.setX(self.modelNP.getX() * 0.001)
        # start swing:
        #self.rot0.start()
        return 1


    def finishedPreFall(self):
        # dissapear!
        printOut("Node position: %f,%f,%f" %(self.modelNP.getX(),self.modelNP.getY(),self.modelNP.getZ()),0)
        printOut("Node scale: %f" % (self.modelNP.getScale()[0]), 0)
        fadeOut = LerpFunctionInterval(self.modelNP.setAlphaScale,
                toData=0.0,fromData=1.0,duration=1.0)
        fadeOut.start()

        self.fallInterval2 = self.genFallDownInterval(2.0, self.groundHeight - 5.0)
        self.fallInterval2.setDoneEvent("lastBitFall_" + self.name)
        self.acceptOnce("lastBitFall_" + self.name, self.lastBitFall)
        self.fallInterval2.start()
        self.swingSeq.pause()

    def restoreAlpha(self):
        fadeOut.finish()
        self.modelNP.setAlphaScale(1.0)

    def lastBitFall(self):
        """
        Gets executed when the parachutes finishes the very last movement and
        dissapears.
        """
        #self.particleDust.cleanup()
        self.falling = False
        #if (not self.isTarget):
        #    self.newPos()
        #    self.start()
        #self.modelNP.setAlphaScale(1.0)

#    def createDust(self):
#        p = ParticleEffect()
#        p.loadConfig(Filename('dust.ptf'))
#        p.setPos(0,0,-1)
#        # draw last!
#        p.setBin("fixed",0)
#        p.reparentTo(self.particleNode)
#        self.particleDust = p
#        self.particleDust.start(self.particleNode)

    def start(self):
        #self.newPos()
        self.falling=True
        self.modelNP.setAlphaScale(1.0)
        self.fallInterval.start()
        self.ignoreHit = False
        self.hitted = False
        #self.rot0.start()

    def updatePos(self, dt):
        #print dt
#        self.model.setPos(self.model.getPos() - Vec3( 0, dt, 0) )
        pass

    def manualMove(self, axis, amount):
        print self.name, "\n"
        deltaV = Vec3(0, 0, 0)
        deltaV[axis] = amount
        self.modelNP.setPos(self.modelNP.getPos() + deltaV)

    def setPos(self,pos):
        """sets a Vec3 to the nodepath holding the parachute"""
        self.modelNP.setPos(pos)

    def printPos(self):
        print self.modelNP.getPos()

    def genFallDownInterval(self, duration, endHeight):
        # adjust duration based on the actual height of
        # the parachute.
        return LerpPosInterval(self.modelNP,
                               duration,
                               Vec3(self.modelNP.getX(),
                                     self.modelNP.getY(),
                                     endHeight))
                                     #-self.modelNP.getZ()-2))
                               # blendType='easeOut'
                               #)


