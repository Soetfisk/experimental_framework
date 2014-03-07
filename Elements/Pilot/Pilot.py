# panda imports
from direct.gui.DirectGui import *
from direct.task.Task import *
from panda3d.core import *

#sys utils
from time import ctime
import sys
from random import *

#game imports
from World import *
from Element import *
from Utils.Debug import printOut, verbosity

from direct.directtools.DirectGrid import DirectGrid


from PilotParachute import PilotParachute

class Pilot(Element):
    """This class implements the functionality
    of the pilot for the study, showing parachutes side
    by side and recording the selections of which one
    looks better"""

    def __init__(self, **kwargs):
        """Constructor, calls super constructor for common
        initialization, writes to outfile a mark for a new
        participant and timestamp, then loads the introduction
        screen and sets some basic keys to start the pilot"""
        
        # call super (Element) constructor
        super(Pilot,self).__init__(**kwargs)

        # create BASIC LOG
        ts = time.time()

        l = getattr(self, 's_pilotlog', 'nolog,w').split(',')
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

    def setupParachutes(self):
        """Creates parachutes objects needed for the pilot, loads textures and all..."""
        # references to all the Parachute objects created
        self.parachutes = {}    # dict of PilotParachute objects
        self.textures = {}
        parConfNode = self.config.parachutes
        # common to all parachute objects
        falltime = parConfNode.falltime
        # model name of the parachute
        modelName = parConfNode.modelname
        # texture for the parachute
        parachuteTex = parConfNode.parachuteTex
        # adjust scale factor
        scale = parConfNode.scale

        # only setup the default COLOUR
        # p contains ALL the textures available.
        p = parConfNode.textures[parConfNode.defaultIdx]
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

        #printOut("Total memory used by textures in Mbytes: %s\n" % str(totalMemory/(1024*1024)), 1)
        #printOut("Aspect ratio: %f" % base.getAspectRatio(), 0)
        # load texture for the actual parachute
        texture = loader.loadTexture(parachuteTex)
        texture.setMinfilter(Texture.FTLinearMipmapLinear)
        texture.setAnisotropicDegree(2)

        text128 = loader.loadTexture("PilotData/textures/red128.png")
        text64  = loader.loadTexture("PilotData/textures/red64.png")

        for n in ['left', 'right']:
            # empty node!
            node = NodePath(n + "_parachute")
            node.setTransparency(1)
            node.setScale(float(scale))
            node.setPos(Vec3(-1000, 40, 0))

            cam = self.world.camera
            Ypos = cam.pos[1] + cam.parDistCam
            if n == 'left':
                node.setPos(-20, Ypos, 100)
            else:
                node.setPos(20, Ypos, 100)

            # parachute model
            #paraModel  = loader.loadModel(modelName)
            #paraModel.setScale(Vec3(0.3, 0.000001, 0.2))
            #paraModel.setPos(Vec3(0, 0.15, 1.2))
            #paraModel.setName("parachute")
            #paraModel.setTexture(texture)
            #paraModel.reparentTo(node)

            # bill board (plane) model
            bodyModel = loader.loadModel("Elements/Game/models/plane")
            bodyModel.setName("body")
            bodyModel.setPos(Vec3(0, 0, -0.5))
            bodyModel.setScale(1.05)
            bodyModel.setTransparency(1)
            if n == 'left':
                bodyModel.setTexture(text64)
            else:
                bodyModel.setTexture(self.textures[19])
            #bodyModel.setTexture(self.textures[len(self.textures)],1)
            if n == 'left':
                bodyModel.reparentTo(node)
            node.reparentTo(self.sceneNP)
            if n == 'left':
                self.leftModel = node
            #grid = DirectGrid( parent=render, planeColor=(0.5, 0.5, 0.5, 0.5) )
            self.parachutes[n] = PilotParachute(self.world, node, self.textures, parConfNode)

    def printSize(self):
        (width,height) = self.onScreenSize(self.leftModel)
        print "Parachute takes (%s,%s) pixels" % (width,height)

    def move(self, x,y,z):
        self.leftModel.setPos( self.leftModel.getPos()+Point3(x,y,z))
        self.printSize()

    def adjustScale(self, size):
        # rescale the object so it takes the closest value to size
        # in pixels with an error of +-2 pixels
        while(True):
            current = max(self.onScreenSize(self.leftModel))
            if int(current) - size > 2:
                self.leftModel.setScale(self.leftModel.getScale()*0.90)
            elif int(current) - size < -2:
                self.leftModel.setScale(self.leftModel.getScale()*1.10)
            else:
                return

    def onScreenSize(self, node):
        """Returns the screen size in pixels for a given node that
        projects on the screen (is in front of the camera)"""
        nodeMin = Point3()
        nodeMax = Point3()
        node.showTightBounds()
        if node.calcTightBounds(nodeMin, nodeMax):
            #print nodeMin, nodeMax
            # from local to camera coordinates
            camMin = base.camera.getRelativePoint(render, nodeMin)
            camMax = base.camera.getRelativePoint(render, nodeMax)
            print camMin,camMax

            render2dMin = Point2()
            render2dMax = Point2()
            base.camLens.project(camMin, render2dMin)
            base.camLens.project(camMax, render2dMax)

            print render2dMin, render2dMax

            aspectMin = aspect2d.getRelativePoint(render2d,
                                                  Point3(render2dMin[0],0,render2dMin[1]))
            aspectMax = aspect2d.getRelativePoint(render2d,
                                                  Point3(render2dMax[0],0,render2dMax[1]))

            print aspectMax, aspectMin

            nodeWidth = abs(aspectMax[0] - aspectMin[0])
            nodeHeight = abs(aspectMax[2] - aspectMin[2])

            print nodeWidth
            print nodeHeight

            pixWidth = nodeWidth * (self.world.camera.screenHeight / 2.0)
            pixHeight= nodeHeight * (self.world.camera.screenHeight / 2.0)

            return (pixWidth ,pixHeight)

    def setupTerrain(self):
        """Sets terrain model, attaching it to the scene nodepath"""
        # transform to position the ground model
        self.groundTransform = NodePath("groundTransform")
        self.groundTransform.setHpr(120, 0, 0)
        # ground model
        self.ground = loader.loadModel("Elements/Game/models/terrain/master")
        self.ground.setPos(78, -100, 0)
        self.ground.reparentTo(self.groundTransform)
        # ground model is only shown in the gamePlay tree.
        self.groundTransform.reparentTo(self.sceneNP)
        return

    def qualityButtonPressed(self, extraArgs):
        # print "calling qualityButton %s\n" %extraArgs
        # this is a workaround the GUI of panda, which I don't
        # fully understand yet.
        if (self.buildingPilot):
            self.buildingPilot = False
            return

        # selection made
        self.optionMade = True
        self.qualitySelected = extraArgs
        # this will set the button on
        self.nextButton["state"]=DGG.NORMAL
        #print "selected: %s" % extraArgs "L" or "R"

    def nextButtonPressed(self):
        #print "calling nextButtonPressed\n"
        
        # invalidate other buttons (left right)
        if (self.optionMade):
            for b in self.buttons:
                b["state"] = DGG.DISABLED

        # set updateQualityPilot flag so the
        # texture changes on the next round
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
        comando = self.qualityButtonPressed
        # DirectGui objects are parented by default to aspect2d!!
        parentNP = self.hudNP

        # create a "next button" to go for the next comparison
        nextPressed = self.nextButtonPressed
        self.nextButton = DirectButton(  parent=parentNP, text="Next --> ",
                                    pad=pad0, scale=0.05,
                                    pos=(1.0, 0, -0.9), command=nextPressed
                                    )
        self.nextButton["state"] = DGG.DISABLED

        self.buttons = []
        for i in range(2):
            self.buttons.append(
                DirectRadioButton(  parent=parentNP, text=texto[i],
                                    pad=pad0, variable=self.radioSelected,
                                    value=[i],scale=0.05,
                                    pos=(posX[i],0,posY),command=comando,
                                    extraArgs=[textoMsg[i]])
                                  )
        # tell each button about the rest of the guys (panda3d internal)
        for b in self.buttons:
            b.setOthers(self.buttons)
            b.uncheck()
        return

    def startPilot(self):
        # set qualities, HQ is reference, and Qi is lower
        self.HQ = self.parachutes['left']
        self.Qi = self.parachutes['right']
        self.updateQualityPilot = False
        
        # all qualities but not the maximum quality
        #self.listOfQualities = range(1,len(self.HQ.textures))
        #self.listPositions = []
        # mix the qualities just once, and then grab always one from
        # the head of the list. 
        #shuffle(self.listOfQualities)
        
        # force maximum texture quality on HQ
        #self.HQ.forceTexture(0)
        # pick a random quality and set it
        #self.currentHi = self.listOfQualities.pop()
        #self.Qi.forceTexture(self.currentHi)
        
        # set keyboard
        #self.hideAllNodes()
        #self.setupKeys("pilot")
        #self.showNode("terrainScene")
        #self.showNode("pilot")
        
        self.setParachutesTop(True)
    #=============================================
    def enterState(self):
        # call super first
        Element.enterState(self)
        # specifics keyboard
        self.setupKeys()
    #=============================================
    def exitState(self):
        # call super first
        Element.exitState(self)
        self.pilotLog.stopLog()
    #=============================================
    def setupKeys(self):
        # clear global setup keys
        pass

    def finishPilot(self):
        """ final screen to say thanks!"""
        self.sendMessage("exitPilot")

    def setParachutesTop(self, flip):
        return
        # setup two models, initial quality comparison
        # Ypos is the DISTANCE FROM THE CAMERA, in DEPTH
        cam = self.world.camera
        #Ypos = self.cameraDict['pos'][1] + self.cameraDict['parDistCam']
        Ypos = cam.pos[1] + cam.parDistCam
        # HEIGHT, in World coordinates
        #minZ = self.cameraDict['minZ']
        minZ = cam.minZ
        
        #when r == 1 the HQ goes on the right, when is -1 goes on the left
        r = 1
        if flip:
            # create a random -1 or a 1
            r = (randint(0,1)*2)-1
        
        self.HQ.newPos(0, r* 20, Ypos, -minZ + 60, True)
        self.Qi.newPos(0, r*-20, Ypos, -minZ + 60, True)
        
        # start fall animation, exactly the same for both
        self.HQ.start()
        self.Qi.start()
        
        # simple task that checks if the parachutes reached the bottom and need
        # to be re-launched from the top
        taskMgr.add(self.updatePilotParachutes, "updatePilotParachutes")

#    def setupGame(self):
#        """ sets the game basic elements """
#        self.setupTerrain()
#        # generates ALL the parachutes, and some extra stuff
#        self.setupParachutes()
#        return
    def updatePilotParachutes(self,t):
        """This task checks if it's necessary to drop again the
        two parachutes from the top, and change their quality
        and drop the new pair"""

        # if the HQ parachute is falling, just leave till next frame
        if (self.HQ.falling):
            return Task.cont

        self.setParachutesTop(True)
        return Task.cont

        # by default, don't swap the falling parachutes 
        flip = False

        """ is it necessary to update the quality, because 
            the user pressed the Next button ?? """
        if (self.updateQualityPilot):
            # save choice to ouput file
            if ( self.HQ.node.getX() < 0 ):
                l = self.HQ.currentQ
                r = self.Qi.currentQ
            else:
                l = self.Qi.currentQ
                r = self.HQ.currentQ

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
        return Task.cont
 
