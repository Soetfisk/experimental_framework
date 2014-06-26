__author__ = 'Francholi'
# panda imports
from panda3d.core import *
from math import *
import time
import cPickle
from random import *
import sys

from direct.showbase.DirectObject import DirectObject
from direct.task.Task import *
from direct.interval.MetaInterval import *
from direct.interval.FunctionInterval import *
from direct.interval.IntervalGlobal import *

from Utils.Debug import printOut


class PilotParachute(DirectObject):
    # class attribute to store textures
    def __init__(self, game, node, textures, parConfNode):
        # grab a reference to the class!, to use
        # class attributes, this is python :|
        cls = self.__class__

        self.name = node.getName()
        self.node = node
        self.game = game
        self.speed = parConfNode.speed

        self.forced = False
        self.falling = False
        self.textures = textures

        self.delayLodChange = True
        self.currentQ = 0
        self.nextLod = 0
        self.lowerResolution = False
        self.forced = False
        self.pilotPos = ''

    """
    def updateLod(self, anEvent):
        # specifc code for each type of event
        if (anEvent.getEventType == "CYCLE"):
            if (anEvent.cycleNumber == self.lodConfig.cycles):
                # change from Qi to Qj in time t
                self.setTexture(-1,int(self.lodConfig.change2Lod),1)
    """


    def setTexture(self, toQ):

        #if ((toQ >= len(self.textures)) or (toQ < 0)): return
        if toQ not in self.textures.keys():
            return

        # if the change has to happen when the model
        # its renewing it's possition.
        #if (not self.lowerResolution and self.delayLodChange):
        #    self.lowerResolution = True
        #    self.nextLod = toQ
        #    return

        #self.lowerResolution = False
        model = self.node.find("body")
        model.setTexture(self.textures[toQ], 1)
        self.currentQ = toQ
        #self.game.replayLog.logEvent("Q:[\'"+self.config.name+"\',"+str(toQ)+"]\n", time.time())

    def forceTexture(self, quality):
        if (quality < 0 or quality >= len(self.textures)):
            printOut("Warning, trying to set invalid quality: %s" % quality, 0)
            return
        self.model.setTexture(self.textures[quality], 1)
        self.currentQ = quality
        return

    # increase texture quality by offsetQuality
    def increaseQ(self, offsetQuality):
        self.setTexture(self.currentQ + offsetQuality, 1)

    # decrease texture quality by offsetQuality
    def decreaseQ(self):
        self.setTexture(self.currentQ - offsetQuality, 1)

    def swingTheThing(self, t):
        self.node.setR((self.maxangle * t - self.maxangle / 2.0) *
                       self.node.getZ() / self.maxHeight)
        return

    def newPos(self, d=0, x=0, y=0, z=0, forced=False):
        self.forced = forced

        # check if need to lower the texture
        if (not self.forced and self.lowerResolution):
            self.setTexture(self.nextLod, 1)

        # swipe time
        self.node.show()
        self.time = 2.0
        self.maxangle = 30.0
        self.groundHeight = -35

        pos = Vec3(x, y, z)

        self.node.setPos(pos)
        self.maxHeight = self.node.getZ()

        swing0 = LerpFunc(self.swingTheThing,
                          fromData=0.0,
                          toData=1.0,
                          duration=self.time,
                          blendType='easeInOut',
                          name="right_" + self.name)
        swing1 = LerpFunc(self.swingTheThing,
                          fromData=1.0,
                          toData=0.0,
                          duration=self.time,
                          blendType='easeInOut',
                          name="left_" + self.name)
        self.swingSeq = Sequence(swing0, swing1)
        self.swingSeq.loop()
        if (not self.forced):
            self.swingSeq.setT(uniform(0, 1))

        # set fall time, interval and callback after fall
        adjustedDuration = (z - self.groundHeight) / self.speed
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
        self.node.setHpr(Vec3(0, 0, angle))
        #self.rot0 = LerpHprInterval(self.modelNP,
        #                           self.time - self.time *
        #                           abs((2 * angle) / self.maxangle),
        #                           Vec3(0, 0, self.maxangle / 2),
        #                           blendType='easeOut')
        #self.rot0.setDoneEvent("swing_" + self.config.name)
        #self.acceptOnce("swing_" + self.config.name, self.swing)

        # adjusts a bit the parachute so it looks exactly behind the robot when
        # the parachute is in one of either sides.
        paraModel = self.node.find("parachute")
        #paraModel.setX(self.node.getX() * 0.001)
        return 1


    def finishedPreFall(self):
        # dissapear!
        printOut("Node position: %f,%f,%f" % (self.node.getX(), self.node.getY(), self.node.getZ()), 0)
        printOut("Node scale: %f" % (self.node.getScale()[0]), 0)
        fadeOut = LerpFunctionInterval(self.node.setAlphaScale, toData=0.0, fromData=1.0, duration=1.0)
        fadeOut.start()

        self.fallInterval2 = self.genFallDownInterval(2.0, self.groundHeight - 5)
        self.fallInterval2.setDoneEvent("lastBitFall_" + self.name)
        self.acceptOnce("lastBitFall_" + self.name, self.lastBitFall)
        self.fallInterval2.start()
        self.swingSeq.pause()

    def restoreAlpha(self):
        fadeOut.finish()
        self.node.setAlphaScale(1.0)

    def lastBitFall(self):
        self.falling = False
        #if (not self.isTarget):
        #    self.newPos()
        #    self.start()
        #self.modelNP.setAlphaScale(1.0)

    def start(self):
        #self.newPos()
        self.falling = True
        self.node.setAlphaScale(1.0)
        self.fallInterval.start()

    def updatePos(self, dt):
    #print dt
    #        self.model.setPos(self.model.getPos() - Vec3( 0, dt, 0) )
        pass

    def setPos(self, pos):
        """sets a Vec3 to the nodepath holding the parachute"""
        self.node.setPos(pos)

    def printPos(self):
        print self.node.getPos()

    def genFallDownInterval(self, duration, endHeight):
        # adjust duration based on the actual height of the parachute.
        return LerpPosInterval(self.node,
                               duration,
                               Vec3(self.node.getX(),
                                    self.node.getY(),
                                    endHeight))

