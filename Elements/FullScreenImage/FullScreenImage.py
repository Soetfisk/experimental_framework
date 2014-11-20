# panda imports
from direct.gui.DirectGui import *
from direct.task.Task import *
from panda3d.core import *
from Element import *
from direct.gui.OnscreenImage import OnscreenImage

#sys utils
import sys
from Utils.Debug import printOut

class FullScreenImage(Element):
    """
    Class to display a full screen image
    Will get some configuration from the corresponding XML node.
    """

    def __init__(self, **kwargs):
        """
        Class constructor
        """
        # build basic element  
        super(FullScreenImage,self).__init__(**kwargs)
        # this defines:
        # self.sceneNP and self.hudNP

        url = getattr(self.config,'s_url',None)
        if (url is None):
            print "Missing url of image to display"
            sys.exit()

        sx,sz = getattr(self.config,'f_scale',[1.0,1.0])

        # this is used when we EXIT the state, so we already displayed
        # once the image.
        self.i_count = getattr(self.config,'i_count', None)
        if (self.i_count):
            self.i_count-=1;

        # load texture
        try:
            self.imageNode = OnscreenImage( image = url , scale = Vec3(sx,1.0,sz))
            self.imageNode.setTransparency(TransparencyAttrib.MAlpha)
            #planeNP = loader.loadModel("models/plane")
            #planeNP.setName(name)
            #planeNP.setTexture(t)
            #planeNP.setTransparency(1)
            #planeNP.setScale(1.0, 1.0, 1.0)
            #planeNP.reparentTo(self.hudNP)
        except Exception,e:
            print "Fatal error, could not load texture file or model in models/plane"
            print "Check the file path"
            print e
            sys.exit()

        self.hideElement()

    def showElement(self):
        self.imageNode.show()

    def hideElement(self):
        self.imageNode.hide()

    def enterState(self):
        # print "entering FullScreenImage"
        # super class enterState
        Element.enterState(self)
        # self.registerKeys()

    def exitState(self):
        # print "leaving state FullScreenImage"
        if (self.i_count):
            self.i_count -= 1
            print self.i_count
            if (self.i_count == 0):
                printOut("Sending event 'NoMoreImages' from exitState of %s"
                    % self.config.name, 2)
                messenger.send('NoMoreImages',['NoMoreImages'])

        Element.exitState(self)
        self.unregisterKeys()
        #self.imageNode.destroy()

