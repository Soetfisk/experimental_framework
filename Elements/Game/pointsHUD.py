from panda3d.core import *

class pointsHUD(object):
    """Hud with the points that the player accumulates over
    the game"""

    def __init__(self, configNode, position):
        """ configNode to set some properties
        gameHudNP is a NP hanging somewhere below the aspect2d node """
        font = loader.loadFont(configNode.font)
        self.points = 0
        scale = configNode.size

        #hudNP = gameHudNP.attachNewNode("statsHUD")
        hudNP = NodePath("statsHUD")
        hudNP.setPos(position)
        hudNP.setScale(scale)

        textNodeList = {}
        textNPList = {}

        textNodeList['pointsTit'] = TextNode('textPointsTittle')
        textNodeList['pointsTit'].setText('POINTS')
        textNodeList['points'] = TextNode('textPoints')

        for k,v in textNodeList.items():
            v.setFont(font)
            v.setTextColor(0.0,0.0,0.0,1)
            textNPList[k + 'NP'] = hudNP.attachNewNode(v)

        textNPList['pointsTitNP'].setPos(Vec3(0,0,0))
        textNPList['pointsNP'].setPos(Vec3(0,0,-0.05  / scale))

        self.textNodeList = textNodeList
        self.hudNP = hudNP
        self.font = font

    def getNP(self):
        return self.hudNP

    def show(self):
        self.hudNP.show()

    def hide(self):
        self.hudNP.hide()

    def setPoints(self,points):
        self.points = points
        prechar = "+"
        if (points < 0): prechar = ""
        self.textNodeList['points'].setText(prechar + str(self.points))

