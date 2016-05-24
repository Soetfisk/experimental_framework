__author__ = 'Francholi'
__author__ = 'Francholi'

# panda imports
from direct.interval.IntervalGlobal import *
from Element import *

import random
import math

class VisualTarget(Element):
    """
    As the name indicates, it's an empty state. It does nothing.
    It can react to timeout events using:
    timeout: float

    """
    def __init__(self, **kwargs):
        """
        See the Element class to find out what attributes are available
        from scratch
        """
        super(VisualTarget, self).__init__(**kwargs)

        # load image or default "not_found.png"
        not_found = 'common/images/not_found.png'
        textureName = getattr(self.config,'fname_image', not_found )
        try:
            texture = loader.loadTexture(textureName)
        except:
            printOut("File not found!, putting default image now")
            texture = loader.loadTexture(not_found)

        texture.setMinfilter(Texture.FTLinearMipmapLinear)
        texture.setAnisotropicDegree(2)

        imgScale = getattr(self.config,'tuple_imageScale', (0.1,0.1))
        imgNode = loader.loadModel("common/models/plane")
        imgNode.reparentTo(self.hudNP)
        imgNode.setScale(imgScale[0],1.0,imgScale[1])
        imgNode.setTransparency(1)
        imgNode.setTexture(texture)
        imgNode.setPos(0,0,0)
        self.imgNode = imgNode

        self.randomize = getattr(self.config, 'randomPoints', False)
        self.animate = getattr(self.config, 'animate', True)
        self.points = getattr(self.config,'tuple_points', [(0,0),(0,1)])
        delay = getattr(self.config,'pointsDelay', 2.0)
        speed = getattr(self.config,'secondsBetweenPoints', 2.0)

        if self.randomize:
            random.shuffle(self.points)
        # add current position of the node to the list
        self.points.insert(0,(0,0,0))

        # sequence of animations
        self.moveSequence = Sequence()
        # create animations at constant speed
        # take pairs of points using zip and shifting the list by one
        for p0,p1 in zip(self.points[:-1],self.points[1:]):
            print p0,p1
            v0 = Point3(p0[0],0,p0[2])
            v1 = Point3(p1[0],0,p1[2])
            dist = (v0-v1).length()
            if not self.animate:
                dist = 0

            blend = 'easeInOut'
            self.moveSequence.append( self.imgNode.posInterval( delay, v0 , blendType=blend))
            self.moveSequence.append( self.imgNode.posInterval( speed, v1 , blendType=blend))
            self.moveSequence.append( self.imgNode.posInterval( delay, v1, blendType=blend))
        self.hideElement()


    def enterState(self):
        # super class enterState
        Element.enterState(self)
        self.moveSequence.start()
        #self.showElement()

    def exitState(self):
        # super class exitState
        Element.exitState(self)

    def getConfigTemplate(self):
        elementDict = Element.getConfigTemplate()
        return elementDict
        
