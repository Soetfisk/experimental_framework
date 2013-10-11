from panda3d.core import *
from ColorMapper import ColorMapper

class targetGuide(object):
    """Hud with the colours and arrow indicating
    the next target to shoot at"""

    def __init__(self, sequence = []):
        """ sequence is a list of colours,
        gameHudNP is a NP hanging somewhere below the aspect2d node """
        self.seq = sequence
        print sequence
        self.colorMapper = ColorMapper()
        self.currentTarget = 0

        #self.nextThree = self.seq[0:3]
        #self.cycles = 0

        #gameHudNP = self.scenes['gamePlay']['HUD']
        targetsNP = NodePath("targetsNP")

        #targetGuideHUD = gameHudNP.attachNewNode("targetGuideHUD")

        # baseline height to position objects
        h = -0.85 # aspect2d ranges from [-1,1] in Y
        targetsNP.setPos(0.8, 0, h)
        targetsNP.setShaderAuto()

        # light the balls
        dlight = DirectionalLight('HUD_LIGHT')
        #plight = PointLight('HUD_PLIGHT')
        lightNP = targetsNP.attachNewNode(dlight)
        #plightNP = self.HUD.attachNewNode(plight)
        lightNP.setPos(0, -1, 0)
        #plightNP.setPos(0,0,0)
        targetsNP.setLight(lightNP)
        #targetGuideHUD.setLight(plightNP)

        # texture created with xaralx
        t = loader.loadTexture('Elements/Game/models/textures/bar.png')
        #t.setMinfilter(Texture.FTLinearMipmapLinear)
        #t.setAnisotropicDegree(2)

        rat = t.getXSize()/t.getYSize()

        # in aspect2D the screen goes from [-ratio,ratio] in width and
        # [-1, 1] in height
        width = 0.8
        height = width / rat

        self.HudNP = loader.loadModel("Elements/Game/models/plane")
        self.HudNP.reparentTo(targetsNP)
        self.HudNP.setScale(width, 1.0, height)
        self.HudNP.setTransparency(1)
        self.HudNP.setTexture(t)

        t2 = loader.loadTexture('Elements/Game/models/textures/circleOut.png')
        #t2.setMinfilter(Texture.FTLinearMipmapLinear)
        #t2.setAnisotropicDegree(2)

        pos = 0.4
        space = 0.8 / (len(self.seq) - 1)
        self.HudOC = []
        self.ArrowPos = []
        self.Colors = []
        for i in range(len(self.seq)):
            self.ArrowPos.append(-pos + i*space)

            self.HudOC.append(loader.loadModel("Elements/Game/models/plane"))
            self.HudOC[-1].setScale(0.13, 1.0, 0.13)
            #self.HudOC[-1].reparentTo(aspect2d)
            self.HudOC[-1].reparentTo(targetsNP)
            self.HudOC[-1].setPos(-pos+(i*space), 0, 0)
            self.HudOC[-1].setTexture(t2)
            self.HudOC[-1].setTransparency(1)

            self.Colors.append(loader.loadModel("Elements/Game/models/ball"))
            #self.Colors[-1].reparentTo(aspect2d)
            self.Colors[-1].reparentTo(targetsNP)
            self.Colors[-1].setScale(0.1, 0.1, 0.1)
            self.Colors[-1].setPos(-pos + i*space, 0.0, 0.0)
            self.Colors[-1].setColor(self.colorMapper.c[self.seq[i]])

        t3 = loader.loadTexture('Elements/Game/models/textures/tri.png')
        #t3.setMinfilter(Texture.FTLinearMipmapLinear)
        #t3.setAnisotropicDegree(1)
        self.ArrowNP = loader.loadModel("Elements/Game/models/plane")
        #self.ArrowNP.reparentTo(aspect2d)
        self.ArrowNP.reparentTo(targetsNP)
        self.ArrowNP.setPos(self.ArrowPos[0], 0.0, -0.1)
        self.ArrowNP.setTransparency(1)
        self.ArrowNP.setScale(0.05, 1.0, 0.05)
        self.ArrowNP.setTexture(t3)

        self.targetsNP = targetsNP

    def show(self):
        self.targetsNP.show()

    def hide(self):
        self.targetsNP.hide()

    def advanceArrow(self):
        """ advances the row indicator """
        nextTarget = (self.currentTarget + 1) % len(self.seq)
        # did we reach a cycle in the targets!
        newPos = self.ArrowNP.getPos()
        newPos[0] = self.ArrowPos[nextTarget]
        posInt = self.ArrowNP.posInterval(1.0, newPos, blendType='easeInOut')
        posInt.start()
        self.currentTarget = nextTarget
        return

    def forceArrow(self, pos):
        self.ArrowNP.setPos(self.ArrowPos[pos], self.ArrowNP.getPos()[1], self.ArrowNP.getPos()[2])

