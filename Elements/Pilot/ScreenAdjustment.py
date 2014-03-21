import sys
from random import *
from time import ctime

# panda imports
from direct.gui.DirectGui import *
from panda3d.core import *
from World import *
from PilotParachute import PilotParachute

class ScreenAdjustment(Element):
    """This class used to just to adjust the scaling factor for the
    scene so objects of interest take a particular amount of centimeters
    in front of the user. For this, as we do not know the resolution and
    size of the user screen, we will ask the user to adjust physically
    one object's dimensions on the screen until it reaches certain size in centimeters """
    def __init__(self, **kwargs):
        # call super (Element) constructor
        super(ScreenAdjustment,self).__init__(**kwargs)
        self.setupParachutes()

    def setupParachutes(self):
        """Creates one parachute object, loads textures and all..."""
        # references to all the Parachute objects created
        # YAML config
        parConfNode = self.config.parachute
        #----------------------------
        robotTex = loader.loadTexture(parConfNode.texture[0].textureName)
        robotTex.setWrapU(Texture.WMClamp)
        robotTex.setWrapV(Texture.WMClamp)
        robotTex.setMinfilter(Texture.FTLinearMipmapLinear)
        robotTex.setAnisotropicDegree(2)
        #----------------------------
        paraTex = loader.loadTexture(parConfNode.parachuteTex)
        paraTex.setMinfilter(Texture.FTLinearMipmapLinear)
        paraTex.setAnisotropicDegree(2)
        #----------------------------
        baseNode = NodePath("parachute")
        baseNode.setTransparency(1)
        baseNode.setScale(float(parConfNode.scale))

        cam = self.world.camera
        camLookAt = Vec3(cam.lookAt[0]-cam.pos[0],
                         cam.lookAt[1]-cam.pos[1],
                         cam.lookAt[2]-cam.pos[2])
        camLookAt.normalize()
        camLookAt = camLookAt * self.parDistCam

        # in Panda by default Y points away from the camera
        #Ypos = cam.pos[1] + cam.parDistCam
        # base node at cam.parDistCam distance from the camera
        baseNode.setPos(camLookAt[0],camLookAt[1],camLookAt[2])

        # this is the PARACHUTE part
        paraModel = loader.loadModel(parConfNode.modelname)
        paraModel.setScale(Vec3(0.3, 0.000001, 0.2))
        paraModel.setPos(Vec3(0, 0.15, 1.2))
        paraModel.setName("parachute")
        paraModel.setTexture(paraTex)
        paraModel.reparentTo(baseNode)
        #----------------------------
        # bill board (plane) model, the actual robot
        robotModel = loader.loadModel("PilotData/models/plane")
        robotModel.setName("body")
        robotModel.setPos(Vec3(0, 0, -0.5))
        robotModel.setTransparency(1)
        robotModel.setTexture(robotTex, 1)
        robotModel.reparentTo(baseNode)
        #----------------------------
        baseNode.setBillboardPointEye()
        baseNode.reparentTo(self.sceneNP)
        self.baseNode = baseNode

    def printSize(self):
        #left = self.parachutes['left'].node
        #parConfNode = self.config.parachutes
        #(width, height) = self.onScreenSize(left)
        #print "Parachute takes (%s,%s) pixels" % (width, height)
        #self.adjustScale(parConfNode.targetScreenSize)
        #(width, height) = self.onScreenSize(left)
        #print "Parachute takes (%s,%s) pixels" % (width, height)
        pass

    def scale(self, amount):
        newScale = self.baseNode.getScale()[0]*amount
        self.baseNode.setScale(newScale)
        # scaling is UNIFORM, so any component will work
        printOut("Scaling to: %f" % newScale)
        self.rescaleFactor = newScale

    #=============================================
    def enterState(self):
        Element.enterState(self)
    #=============================================
    def exitState(self):
        Element.exitState(self)
    #=============================================
