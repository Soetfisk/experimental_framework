# panda imports
from direct.gui.DirectGui import *
from direct.task.Task import *
from panda3d.core import *

#sys utils
from time import ctime
import sys
from random import *

#game imports
from Element import *
from CalPoint import calStimuli

from Debug import printOut
class Calib(Element):
    """This class will implement a calibration Scene, displaying some
    targets and performing the calibration with the eye-tracker.
    It will read all the config details from the calibration config file,
    such as how many points, what type of calibration stimulus, and where
    to save the calibration"""

    def __init__(self,**kwargs):
        # build basic element  
        # this sets all the attributes specified in the generic XML
        super(Calib,self).__init__(**kwargs)

        # window ratio set during World constructor.
        window_ratio = self.config.world.camera.ratio

        # speed from point to point
        self.moveSpeed = float(self.xmlConfig.moveSpeed)
        # fixation time
        self.fixTime = float(self.xmlConfig.fixationTime)

        # load background for calibration if exists
        if (self.xmlConfig.backTexture is not "None"):
            node = loader.loadModel("models/plane")
            node.setName("background")
            try:
                texture = loader.loadTexture(self.xmlConfig.backTexture)
                #texture.setMinfilter(Texture.FTLinearMipmapLinear)
                #texture.setAnisotropicDegree(2)
                node.setTexture(texture)
                node.reparentTo(aspect2d)

                # in Aspect2D, the size is 2*ratio in width and 2 in height
                node.setScale(2 * window_ratio,1.0,2.0)
                node.reparentTo(self.hudNP)
            except:
                printOut("Failed to load texture: "+self.xmlConfig.backTexture,
                        2)
                sys.exit()
       
        # creates an empty calibration point 
        calPoint = calStimuli(self.hudNP)

        # loads textures for the stimuli: (check out the XML calconfig.xml)
        textures = self.xmlConfig.stimuliTex.texture
        for t in textures:
            # load textures
            texture = loader.loadTexture(t.name)
            scale = float(t.scale)
            order = int(t.order)
            name = t.nodename
            if (t.shrink == 'None'): 
                shrink = None
            else:
                shrink = float(t.shrink)
            if (texture):
                calPoint.addTexture(name,texture,scale,order,shrink)

        # once textured have been loaded, create scale (up/down) intervals
        # and store them in the calPoint class. They can be used regardless of
        # the movement.
        calPoint.createScaleIntervals(self.fixTime)

        # keep a reference
        self.calPoint = calPoint
        
        # read calibration points from config file
        self.calPositions = []
        self.calPositions.append(Vec2(0,0))

        # On how to use EVAL safely: http://lybniz2.sourceforge.net/safeeval.html
        try:
            randomCalPoints = eval(self.calConfig.calPoints.random)
        except:
            # if it's not True then default to False
            randomCalPoints = False

        if (not randomCalPoints):
            xmlPos = self.xmlConfig.calPoints.calPoint
            # convert to floats and append to list
            # also rescale them
            # Rescale width from 0..1 to -ratio..ratio
            # Rescale height from 0..1 to -1..1
            for p in xmlPos:
                p = map(float, p.pos.split(','))
                p[0] = (p[0] * 2 * window_ratio) - window_ratio
                p[1] = 1 - (p[1] * 2)
                self.calPositions.append(Vec2(p[0],p[1]))

        # animation string when moving from one calib point to another
        self.animCurve = self.xmlConfig.animation

        # initial position for the calibration point (centre ?)
        pos = self.calPositions[0]
        self.calPoint.setPosition(pos.x,pos.y)
        self.currCalPoint = 1

    def setupKeys(self):
        # global setup keys
        k = self.kbd
        k.registerKey('o','EyeTracker', self.advanceCalTarget, False, [])
        # calibration
    #    if (s == "calibrationScreen"):
    #        self.accept("m", self.moveTarget)

    def advanceCalTarget(self):
        #print self.currCalPoint
        if (self.currCalPoint == len(self.calPositions)):
            print "no more moves!?"
            return
        else:
            print "moving..."
            pos = self.calPositions[self.currCalPoint]
            self.currCalPoint+=1
            self.calPoint.moveTo(pos.x,pos.y,self.animCurve, self.moveSpeed)
            


