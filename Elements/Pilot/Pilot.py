import sys
from random import *
from time import ctime

# panda imports
from direct.gui.DirectGui import *
from panda3d.core import *
from World import *
from PilotParachute import PilotParachute

class Pilot(Element):
    """This class implements the functionality
    of the pilot that compares two images side by side,
    picking from a range of a set of qualities defined
    in a config file (specified in the experiment file)"""

    def __init__(self, **kwargs):
        # call super (Element) constructor
        super(Pilot,self).__init__(**kwargs)

        # create BASIC LOG
        ts = time.time()
        l = getattr(self, 'pilotLog', 'nolog,w').split(',')
        if l is 'nolog,w':
            printOut("-- Warning -- logging for the Pilot disabled",0)
        self.pilotLog = Logger(l[0],l[1]) 
        self.pilotLog.startLog(ts)
        
        self.pilotLog.logEvent("==== new pilot participant ====\n",ts)
        self.pilotLog.logEvent("date: " +  ctime() + "\n",ts)
        self.pilotLog.logEvent("pilot start\n",ts)
        
        # sets some GUI elements on top of the main game scene, to select
        # which parachute has lower quality
        self.setupComparisonScreen()
        self.setupTerrain()
        self.setupParachutes()

        self.reversals = 0

    def setupParachutes(self):
        """Creates parachutes objects needed for the pilot, loads textures and all..."""
        # all textures for a given colour
        self.textures = {}
        # YAML config
        parConfNode = self.config.parachutes
        # common to all parachute objects
        speed = parConfNode.speed
        # model name of the parachute
        modelName = parConfNode.modelname
        # texture for the parachute
        parachuteTex = parConfNode.parachuteTex
        # adjust scale factor
        scale = parConfNode.scale

        # only setup ONE COLOUR
        # to know which is the default colour, check the config file
        # for "defaultIdx", which relates to the list of parachutes
        # (each of which has a colour)
        p = parConfNode.textures[parConfNode.defaultIdx]
        self.minQ = p.textureMinLevel
        self.maxQ = p.textureMaxLevel

        color = str(p.name.upper())

        # LOAD EVERY SINGLE TEXTURE IN THE SEQUENCE!
        # for the BILLBOARD
        totalMemory = 0
        for i in range(p.textureMinLevel, p.textureMaxLevel + 1):
            texName = p.texturePrefix + str(i) + p.texturePostFix
            t = loader.loadTexture(texName)
            totalMemory += t.estimateTextureMemory()
            t.setWrapU(Texture.WMClamp)
            t.setWrapV(Texture.WMClamp)
            t.setMinfilter(Texture.FTLinearMipmapLinear)
            t.setAnisotropicDegree(2)
            self.textures[i] = t

        #printOut("Total memory used by textures in Mbytes: %s\n" % str(totalMemory/(1024*1024)), 0)
        # load texture for the actual parachute
        texture = loader.loadTexture(parachuteTex)
        texture.setMinfilter(Texture.FTLinearMipmapLinear)
        texture.setAnisotropicDegree(2)

        paraModels = {}

        for n in ['QM', 'Qi']:
            node = NodePath(n + "_parachute")
            node.setTransparency(1)

            cam = self.config.world.camera
            Ypos = cam.pos[1] + self.config.parDistCam
            node.setPos(0, Ypos, 100)
            # parachute model
            paraModel  = loader.loadModel(modelName)
            # TODO: Make this scale a factor of the overall scale!
            paraModel.setScale(Vec3(0.3, 0.000001, 0.2))
            paraModel.setPos(Vec3(0, 0.15, 1.2))
            paraModel.setName("parachute")
            paraModel.setTexture(texture)
            paraModels[n] = paraModel
            # this is added at the very end of this function
            paraModel.reparentTo(node)

            # bill board (plane) model
            bodyModel = loader.loadModel("Elements/Game/models/plane")
            bodyModel.setName("body")
            bodyModel.setPos(Vec3(0, 0, -0.5))
            bodyModel.setScale(1.05)
            bodyModel.setTransparency(1)
            # both with the MAXIMUM quality to start with
            bodyModel.setTexture(self.textures[len(self.textures)-1], 1)
            bodyModel.reparentTo(node)

            node.reparentTo(self.sceneNP)
            # this is equivalent to
            # self.QM = ....
            # self.Qi = ....
            setattr(self, n, PilotParachute(self.config.world, node, self.textures, parConfNode))

    def printSize(self):
        parConfNode = self.config.parachutes
        (width, height) = self.onScreenSize(self.QM.node)
        print "Parachute takes (%s,%s) pixels" % (width, height)
        #self.adjustScale(parConfNode.targetScreenSize)
        #(width, height) = self.onScreenSize(left)
        #print "Parachute takes (%s,%s) pixels" % (width, height)

    def translate(self, x,y,z):
        self.QM.node.setPos(self.QM.node.getPos()+Point3(x,y,z))
        #self.printSize()

#    def adjustScale(self, size):
#        # rescale the object so it takes the closest value to size
#        # in pixels with an error of +-2 pixels
#        scale = self.adjustScaleNodes([self.QM.node, self.Qi.node], size)

#    def adjustScaleNodes(self, nodes, size):
#        adjustScale = 1.0
#        while(True):
#           current = max(self.onScreenSize(nodes[0]))
#           # 2 pixels difference!
#           if int(current) - size > 2:
#               scale = 0.9
#           elif int(current) - size < -2:
#               scale = 1.10
#           else:
#               adjustScale = nodes[0].getScale()
#               break
#           for n in nodes:
#               n.setScale(n.getScale()*scale)
#        return adjustScale

    def onScreenSize(self, node):
        """Returns the screen size in pixels for a given node that
        projects on the screen (is in front of the camera)"""
        nodeMin = Point3()
        nodeMax = Point3()
        #node.showTightBounds()
        if node.calcTightBounds(nodeMin, nodeMax):
            # from local to camera coordinates
            camMin = base.camera.getRelativePoint(render, nodeMin)
            camMax = base.camera.getRelativePoint(render, nodeMax)
            render2dMin = Point2()
            render2dMax = Point2()
            # from camera to project space
            base.camLens.project(camMin, render2dMin)
            base.camLens.project(camMax, render2dMax)
            # from screen to aspect2d range (aspect,-aspect,1,-1)
            aspectMin = aspect2d.getRelativePoint(render2d,
                                                  Point3(render2dMin[0],0,render2dMin[1]))
            aspectMax = aspect2d.getRelativePoint(render2d,
                                                  Point3(render2dMax[0],0,render2dMax[1]))
            # measure width and height
            nodeWidth = abs(aspectMax[0] - aspectMin[0])
            nodeHeight = abs(aspectMax[2] - aspectMin[2])

            # calculate pixels on screen using the size of the screen
            pixWidth = nodeWidth * self.config.world.camera.screenHeight * 0.5
            pixHeight = nodeHeight * self.config.world.camera.screenHeight * 0.5

            return (pixWidth ,pixHeight)

    def setupTerrain(self):
        """Sets terrain model, attaching it to the scene nodepath"""
        # transform to position the ground model
        self.groundTransform = NodePath("groundTransform")
        self.groundTransform.setHpr(130, 7, 7)
        # ground model
        self.ground = loader.loadModel("Elements/Game/models/terrain/master")
        self.ground.setPos(213, -179, -5)
        self.ground.reparentTo(self.groundTransform)
        # ground model is only shown in the gamePlay tree.
        self.groundTransform.reparentTo(self.sceneNP)
        return

    def leftRightButtonPressed(self, extraArgs):
        # print "calling qualityButton %s\n" %extraArgs
        # this is a workaround the GUI of panda, which I don't
        # fully understand yet.
        if (self.buildingPilot):
            self.buildingPilot = False
            return

        # selection made
        self.optionMade = True
        if extraArgs == 'L':
            pass
        self.qualitySelected = extraArgs
        # this will set the button on
        self.nextButton["state"]=DGG.NORMAL
        #print "selected: %s" % extraArgs "L" or "R"

    def nextButtonPressed(self):
        # invalidate other buttons (left right)
        if (self.optionMade):
            # disable LEFT and RIGHT buttons
            for b in self.buttons:
                b["state"] = DGG.DISABLED

        # set updateQualityPilot flag so the
        # texture changes on the next fall
        self.updateQualityPilot = True
        
        # disable NEXT so the decision is FINAL
        self.nextButton["state"] = DGG.DISABLED
        self.optionMade = False

    def setupComparisonScreen(self):
        # radio button state shared by all, which indicates
        # which one is selected
        self.radioSelected = [0]
        self.optionMade = False
        self.buildingPilot = True

        # pad0 is pad around the text in X and Y
        pad0 = (0.9,0.7)
        texto = ['<< Left','Right >>']
        textoMsg = ['L','R']
        posX = [-0.5, 0.5]
        posY = -0.9 # [0.7,0.5,0.3]
        # callback called, with "<< Left" or "Right >>"
        comando = self.leftRightButtonPressed
        # DirectGui objects are parented by default to aspect2d!!
        parentNP = self.hudNP

        # create a "next button" to go for the next comparison
        self.nextButton = DirectButton( parent = parentNP, text="Next --> ",
                                    pad = pad0, scale=0.05,
                                    pos = (1.0, 0, -0.9), command=self.nextButtonPressed
                                    )
        self.nextButton["state"] = DGG.DISABLED

        self.buttons = []
        for i in range(2):
            self.buttons.append(
                DirectRadioButton(parent=parentNP, text=texto[i],
                                  pad=pad0, variable=self.radioSelected,
                                  value=[i],scale=0.05,
                                  pos=(posX[i],0,posY),command=comando,
                                  extraArgs=[textoMsg[i]]) )
        # tell each button about the rest of the guys (panda3d internal)
        for b in self.buttons:
            b.setOthers(self.buttons)
            b.uncheck()
        return

    def startPilot(self):
        self.QM.setTexture(self.maxQ)
        self.Qi.setTexture(self.minQ)

        taskMgr.add(self.updatePilotParachutes, "updatePilotParachutes")

        # set qualities, QM is reference, and Qi is lower
        # self.updateQualityPilot = False

        # all qualities but not the maximum quality
        #self.listOfQualities = range(1,len(self.QM.textures))
        #self.listPositions = []
        # mix the qualities just once, and then grab always one from
        # the head of the list. 
        #shuffle(self.listOfQualities)
        
        # force maximum texture quality on QM
        #self.QM.forceTexture(0)
        # pick a random quality and set it
        #self.currentHi = self.listOfQualities.pop()
        #self.Qi.forceTexture(self.currentHi)
        
        # set keyboard
        #self.hideAllNodes()
        #self.setupKeys("pilot")
        #self.showNode("terrainScene")
        #self.showNode("pilot")
        
        #self.setParachutesTop(True)
    #=============================================
    def enterState(self):
        # call super first
        Element.enterState(self)
        # this rescale factor comes from another state that
        # probably sets it up, or from the default value in the
        # experiment setup.
        rescale = self.rescaleFactor

        self.QM.node.setScale(rescale)
        self.Qi.node.setScale(rescale)

        # simple task that checks if the parachutes reached the bottom and need
        # to be re-launched from the top
        self.startPilot()

    #=============================================
    def exitState(self):
        # call super first
        Element.exitState(self)
        self.pilotLog.stopLog()
    #=============================================
    def finishPilot(self):
        """ final screen to say thanks!"""
        self.sendMessage("exitPilot")

    def setParachutesTop(self, flip):
        # setup two models, initial quality comparison
        cam = self.config.world.camera

        # field of view in RADIANS
        fovRads = (cam.fov * pi / 180.0)
        # HIPOTHENUSE of the triangle from camera to parDistCam
        hip = self.config.parDistCam / cos(fovRads / 2.0)
        # Minimum X value within the viewing volume
        minX = -hip*sin(fovRads/2.0)
        minZ = cam.ratio-hip*sin(fovRads/2.0)

        Ypos = cam.pos[1] + self.config.parDistCam

        #when r == 1 the QM goes on the right, when is -1 goes on the left
        r = 1
        if flip:
            # create a random -1 or a 1
            r = (randint(0,1)*2)-1
        
        self.QM.newPos(0, r* 20, Ypos, -minZ, True)
        self.Qi.newPos(0, r*-20, Ypos, -minZ, True)
        
        # start fall animation, exactly the same for both
        self.QM.start()
        self.Qi.start()
        

    def updatePilotParachutes(self,t):
        """This task checks if it's necessary to drop again the
        two parachutes from the top, and change their quality
        and drop the new pair"""

        # if the QM parachute is falling, just leave till next frame
        if (self.QM.falling):
            return t.cont

        #self.setParachutesTop(True)
        #return t.cont

        # by default, don't swap the falling parachutes 
        flip = True

        """ did the user press Next ?, change quality """
        if (self.updateQualityPilot):

            if (self.qualitySelected):
                pass

            if ( self.QM.node.getX() < 0 ):
                l = self.QM.currentQ
                r = self.Qi.currentQ
            else:
                l = self.Qi.currentQ
                r = self.QM.currentQ

            ts = time.time()
            self.pilotLog.logEvent("left  : " + str(l)+"\n",ts)
            self.pilotLog.logEvent("right : " + str(r)+"\n",ts)
            self.pilotLog.logEvent("choice: " + self.qualitySelected + "\n",ts)

            # do we still have more qualities to test ?
            if (len(self.listOfQualities) >= 1):
                flip = True
                self.currentHi = self.listOfQualities.pop()
                self.Qi.forceTexture(self.currentHi)
                self.updateQualityPilot = False
             
                # clear buttons state (enable them)
                for b in self.buttons:
                    b.setOthers(self.buttons)
                    b.uncheck()
                    b["state"] = DGG.NORMAL
            else:
                # FINISH PILOT
                self.finishPilot()
                return None

        # set new position (at the top) for the falling
        # parachutes
        self.setParachutesTop(flip)
        return t.cont
 
