__author__ = 'Francholi'
__author__ = 'Francholi'

# panda imports
from direct.interval.IntervalGlobal import *
from Elements.Element.Element import *
from direct.interval.FunctionInterval import *

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

        temp = getattr(self.config,'tuple_imageScale', (0.1,0.1))
        imgScale = Vec3(temp[0],1.0,temp[1])
        imgNode = loader.loadModel("common/models/plane")
        imgNode.reparentTo(self.hudNP)
        imgNode.setScale(imgScale)
        imgNode.setTransparency(1)
        imgNode.setTexture(texture)
        imgNode.setPos(0,0,0)
        self.imgNode = imgNode

        self.randomize = getattr(self.config, 'randomPoints', False)
        self.animate = getattr(self.config, 'animate', True)
        self.points = getattr(self.config,'tuple_points', [(0,0),(0,1)])
        delay = getattr(self.config,'restDelay', 2.0)
        speed = getattr(self.config,'speed', 2.0)

        if self.randomize:
            random.shuffle(self.points)
        # add current position of the node to the list
        self.points.insert(0,(0,0,0))

        # sequence of animations
        blend = 'easeInOut'
        self.moveSequence = Sequence()
        # create animations at constant speed
        # take pairs of points using zip and shifting the list by one

        for p0,p1 in zip(self.points[:-1],self.points[1:]):
            v0 = Point3(p0[0],0,p0[2])
            v1 = Point3(p1[0],0,p1[2])
            dist = (v0-v1).length() * int(self.animate) # bool True==1, False==0
            self.moveSequence.append( self.imgNode.posInterval( delay, v0 , blendType=blend))
            self.moveSequence.append( self.imgNode.posInterval( dist / speed, v1 , blendType=blend))

        self.moveSequence.append( self.imgNode.scaleInterval( 2, imgScale ) )

        cam = self.config.world.getCamera()
        self.width, self.height = map(float,(base.win.getXSize(),base.win.getYSize()))
        self.hideElement()
        self.imgNode.setPos(Vec3(0,0,0))
        self.moveSequence.setDoneEvent('end_animation')

    def nop(self):
        pass

    def getCenterPos(self):
        return self.imgNode.getPos()

    def enterState(self):
        # super class enterState
        Element.enterState(self)
        self.config.world.hideMouseCursor()

        self.logFile.writeln("# time, targetPos, mousePos, eyePos")
        taskMgr.add( self.logData, 'logData' )
        self.moveSequence.start()

        # set calibration in the eye-tracker
        try:
            self.eyeTracker.loadAndSetCalibration(self.repeatRandom.variable)
            self.eyeTracker.startTracking()
        except:
            printOut("Warning, no eyetracker found")

    def exitState(self):
        # super class exitState
        try:
            self.eyeTracker.stopTracking()
        except:
            pass
        self.config.world.showMouseCursor()
        Element.exitState(self)
        taskMgr.remove('logData')

    def logData(self, t):
        """
        :param t: Panda3d task
        :return: task.cont or task.done
        """
        mouseX,mouseY = (0.0,0.0)
        eyeX,eyeY = (0,0)
        pos = self.imgNode.getPos()
        if self.config.trackMouse and base.mouseWatcherNode.hasMouse():
            mouseX,mouseY = map(float,base.mouseWatcherNode.getMouse())
        if self.config.trackEye:
            try:
                eyeX,eyeY = self.eyeTracker.getLastSample()
            except:
                pass
        # targetPos, mousePos, eyePos
        outString = "%.4f %.4f, %.4f %.4f, %.4f %.4f" %\
        (
         pos.getX(),pos.getZ(),  # tile center
         (self.width / self.height)*mouseX, mouseY,     # mouse pos
         eyeX,eyeY                                   # gaze pos
        )
        self.logFile.logEvent(outString)
        return t.cont




