# panda imports
from direct.gui.DirectGui import *
from direct.task.Task import *
from panda3d.core import *
from Element import *
from direct.gui.OnscreenImage import OnscreenImage

#sys utils
import sys

class SideBySideImage(Element):
    """
    Class to display a two images side by side
    Will get some configuration from the corresponding JSON node.
    """

    def __init__(self, **kwargs):
        """
        world is a reference to the main class
        text: is the name of the node in the XML config
        """
        # build basic element  
        # self.sceneNP and self.hudNP are defined here
        super(SideBySideImage,self).__init__(**kwargs)

        urlA = getattr(self,'s_urlA',None)
        urlB = getattr(self,'s_urlB',None)
        if (urlA is None or urlB is None):
            print "Missing references of images to compare"
            sys.exit()

        sx,sz = getattr(self,'f_scale',[1.0,1.0])

        # load textures
        try:
            self.imageNodeA = OnscreenImage( image = urlA , scale = Vec3(sx,1.0,sz))
            self.imageNodeA.setTransparency(TransparencyAttrib.MAlpha)
            self.imageNodeA.setX(-0.5)

            self.imageNodeB = OnscreenImage( image = urlB , scale = Vec3(sx,1.0,sz))
            self.imageNodeB.setTransparency(TransparencyAttrib.MAlpha)
            self.imageNodeB.setX(0.5)

            #planeNP = loader.loadModel("models/plane")
            #planeNP.setName(name)
            #planeNP.setTexture(t)
            #planeNP.setTransparency(1)
            #planeNP.setScale(1.0, 1.0, 1.0)
            #planeNP.reparentTo(self.hudNP)
        except:
            print "Fatal error, could not load texture file or model in models/plane"
            print "Check the file path"

        self.hideElement()

    def showElement(self):
        self.imageNodeA.show()
        self.imageNodeB.show()

    def hideElement(self):
        self.imageNodeA.hide()
        self.imageNodeB.hide()

    def enterState(self):
        print "entering FullScreenImage"
        # super class enterState
        Element.enterState(self)
        # self.registerKeys()

    def exitState(self):
        print "leaving state FullScreenImage"
        Element.exitState(self)
        self.unregisterKeys()
        self.imageNodeA.destroy()
        self.imageNodeB.destroy()

