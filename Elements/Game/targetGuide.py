from panda3d.core import *
from ColorMapper import ColorMapper

class targetGuide(object):
    """Hud with the colours and arrow indicating
    the next target to shoot at"""

    def __init__(self, sequence = [],
                 pos = 'right', label = ''):
        """ sequence is a list of colours,
        gameHudNP is a NP hanging somewhere below the aspect2d node """
        self.seq = sequence
        self.colorMapper = ColorMapper()

        targetsNP = NodePath("targetsNP")

        font = loader.loadFont('Elements/Game/models/textures/komikax.egg')
        textNode = TextNode('GroupLabel')
        textNode.setFont(font)
        textNode.setShadow(0.05,0.05)
        textNode.setShadowColor(0.0,0.0,0.0,1.0)
        textNode.setText(label)
        textNode.setTextColor(0.8,0.8,0.8,1)

        textNP = targetsNP.attachNewNode(textNode)
        textNP.setScale(0.08)
        textNP.setPos(-0.45,0 ,-0.15)

        #self.currentTarget = 0
        #self.nextThree = self.seq[0:3]
        #self.cycles = 0

        #targetGuideHUD = gameHudNP.attachNewNode("targetGuideHUD")

        targetsGui = targetsNP.attachNewNode("targetsGui")
        targetsGui.setShaderAuto()

        # baseline height to position objects
        h = -0.80 # aspect2d ranges from [-1,1] in Y
        if pos == 'right':
            targetsNP.setPos(1.6, 0, h)
        elif pos == 'left':
            targetsNP.setPos(-1.0, 0, h)

        # light the balls
        dlight = DirectionalLight('HUD_LIGHT')
        #plight = PointLight('HUD_PLIGHT')
        lightNP = targetsGui.attachNewNode(dlight)
        #plightNP = self.HUD.attachNewNode(plight)
        lightNP.setPos(0, -1, 0)
        #plightNP.setPos(0,0,0)
        targetsGui.setLight(lightNP)
        #targetGuideHUD.setLight(plightNP)

        # texture created with xaralx
        t = loader.loadTexture('Elements/Game/models/textures/bar.png')
        #t.setMinfilter(Texture.FTLinearMipmapLinear)
        #t.setAnisotropicDegree(2)

        rat = t.getXSize()/t.getYSize()

        # in aspect2D the screen goes from [-ratio,ratio] in width and
        # [-1, 1] in height
        width = len(sequence) * 0.08
        height = 0.8 / rat

        # if we have only ONE colour, do not set
        # the rectangle to separate colours.
        if len(sequence) > 1:
            self.HudNP = loader.loadModel("Elements/Game/models/plane")
            self.HudNP.reparentTo(targetsGui)
            self.HudNP.setScale(width, 1.0, height)
            self.HudNP.setTransparency(1)
            self.HudNP.setTexture(t)
            self.HudNP.setPos(-0.3,0.0,0.0)

        t2 = loader.loadTexture('Elements/Game/models/textures/circleOut.png')
        #t2.setMinfilter(Texture.FTLinearMipmapLinear)
        #t2.setAnisotropicDegree(2)

        pos = 0.4
        try:
            space = width / (len(self.seq) - 1)
        except ZeroDivisionError,z:
            space = width
        self.HudOC = []
        self.ArrowPos = []
        self.Colors = []
        for i in range(len(self.seq)):
            self.ArrowPos.append(-pos + i*space)
            self.HudOC.append(loader.loadModel("Elements/Game/models/plane"))
            self.HudOC[-1].setScale(0.13, 1.0, 0.13)
            #self.HudOC[-1].reparentTo(aspect2d)
            self.HudOC[-1].reparentTo(targetsGui)
            self.HudOC[-1].setPos(-pos+(i*space), 0, 0)
            self.HudOC[-1].setTexture(t2)
            self.HudOC[-1].setTransparency(1)

            self.Colors.append(loader.loadModel("Elements/Game/models/ball"))
            #self.Colors[-1].reparentTo(aspect2d)
            self.Colors[-1].reparentTo(targetsGui)
            self.Colors[-1].setScale(0.1, 0.1, 0.1)
            self.Colors[-1].setPos(-pos + i*space, 0.0, 0.0)
            self.Colors[-1].setColor(self.colorMapper.c[self.seq[i].upper()])

        # t3 = loader.loadTexture('Elements/Game/models/textures/tri.png')
        #t3.setMinfilter(Texture.FTLinearMipmapLinear)
        #t3.setAnisotropicDegree(1)
        # self.ArrowNP = loader.loadModel("Elements/Game/models/plane")
        #self.ArrowNP.reparentTo(aspect2d)
        # self.ArrowNP.reparentTo(targetsNP)
        # self.ArrowNP.setPos(self.ArrowPos[0], 0.0, -0.1)
        # self.ArrowNP.setTransparency(1)
        # self.ArrowNP.setScale(0.05, 1.0, 0.05)
        # self.ArrowNP.setTexture(t3)

        self.targetsNP = targetsNP

    def show(self):
        self.targetsNP.show()

    def hide(self):
        self.targetsNP.hide()

    def advanceArrow(self):
        """ advances the row indicator """
        # no Arrow!
        return

        nextTarget = (self.currentTarget + 1) % len(self.seq)
        # did we reach a cycle in the targets!
        newPos = self.ArrowNP.getPos()
        newPos[0] = self.ArrowPos[nextTarget]
        posInt = self.ArrowNP.posInterval(1.0, newPos, blendType='easeInOut')
        posInt.start()
        self.currentTarget = nextTarget
        return

    def forceArrow(self, pos):
        # no Arrow!
        return
        self.ArrowNP.setPos(self.ArrowPos[pos], self.ArrowNP.getPos()[1], self.ArrowNP.getPos()[2])

