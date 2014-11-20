# panda imports
from direct.gui.DirectGui import *
from direct.task.Task import *
from panda3d.core import *
from Element import *
from direct.gui.OnscreenImage import OnscreenImage

#sys utils
import sys

class ImageChoice(Element):
    """
    Class to display several images and offer a rating 
    option for the user to clasify
    Will get some configuration from the corresponding XML node.
    """

    def __init__(self, **kwargs):
        """
        world is a reference to the main class
        """
        # build basic element  
        # self.sceneNP and self.hudNP are created here
        super(ImageChoice,self).__init__(**kwargs)

        s = getattr(self.config,'i_slots',None)
        rating = getattr(self.config,'r_scale',None)
        rating = rating.strip().split(',')
        csv_path_prefix = getattr(self.config,'csv_path_prefix','')
        image_path_prefix = getattr(self.config,'images_path_prefix','')

        if (not s):
            print "Missing i_slots property in ImageChoice, can't continue"
            sys.exit()
        if (not rating):
            print "Missing rating property in ImageChoice, can't continue"
            sys.exit()
        if (s != len(rating)):
            print "Error, rating is different from number of slots (i_slots), can't continue"
            sys.exit()
        
        # load list of images to compare from a CSV file
        # the number of files per line has to match the i_slots value
        csvFile = getattr(self.config,'s_images',None)
        if (csvFile):
            try:
                f = open(csv_path_prefix + csvFile)
                self.imagesToCompare = [ lines.replace(' ','').strip().split(',') for lines in f.readlines()  ]
                # Unique images (avoid loading twice the same tex)
                imageSet = set( image for i in range(len(self.imagesToCompare)) for image in self.imagesToCompare[i] )
                print imageSet
                self.nodePaths = dict((k,self.loadImage(image_path_prefix + k)) for k in imageSet  )
            except Exception,e:
                print "Exception building ImageChoice, line 42"
                print e

        self.setupRatingGui()
        # hide all until the node is activated.
        self.hideElement()

    def loadImage(self,imageUrl):
        """Loads ONE image from imageUrl into a nodepath to display as a texture image"""
        sx,sz = getattr(self.config,'f_scale',[1.0,1.0])
        horGap = getattr(self.config,'f_horgap',0.1)
        vertGap = getattr(self.config,'f_vertgap',0.1)
        # the screen x coord in 2D goes from -1.6 to 1.6 (left to right horizontally)
        # the screen z coord in 2D goes from -1 to 1 (top-down vertically)
        nodepath = OnscreenImage( image = imageUrl , scale = Vec3(sx,1.0,sz))
        nodepath.setTransparency(TransparencyAttrib.MAlpha)
        return nodepath

    def loadImages(self, urls):
        nodepaths=[]
        # z is the vertical axis in the 3D world
        sx,sz = getattr(self.config,'f_scale',[1.0,1.0])
        horGap = getattr(self.config,'f_horgap',0.1)
        vertGap = getattr(self.config,'f_vertgap',0.1)

        # for horizontal distribution
        # incX: distance between centers
        # inc = vertGap + 2.0*sx
        # startX is the first position (all the space / 2)
        incX = vertGap + 2.0*sx
        startX = - (len(urls)-1)*incX/2.0 

        # load each texture
        # the screen x coord in 2D goes from -1.6 to 1.6 (left to right horizontally)
        # the screen z coord in 2D goes from -1 to 1 (top-down vertically)
        try:
            for i in urls:
                # no need to reparent to render or aspect or anything!!!!
                nodepath = OnscreenImage( image = i , scale = Vec3(sx,1.0,sz))
                nodepath.setTransparency(TransparencyAttrib.MAlpha)
                nodepath.setX(startX)
                startX += incX
                nodepaths.append(nodepath)
        except:
            print "Fatal error, could not load texture file or model in models/plane"
            print "Check the file path"
            sys.exit()
        return nodepaths


    def setupRatingGui(self):
        pass

    def showElement(self):
        for i in self.nodePaths:
            i.show()

    def hideElement(self):
        for i in self.nodePaths:
            i.hide()

    def enterState(self):
        #print "entering FullScreenImage"
        # super class enterState
        Element.enterState(self)
        # self.registerKeys()

    def exitState(self):
        #print "leaving state FullScreenImage"
        Element.exitState(self)
        self.unregisterKeys()
        for i in self.nodePaths:
            i.destroy()

