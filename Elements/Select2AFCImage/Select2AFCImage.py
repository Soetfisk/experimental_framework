# panda imports
from direct.gui.DirectGui import *
from direct.gui.OnscreenImage import OnscreenImage

from Elements.Element.Element import *
# os module to list filenames in a directory
import os,itertools
import random
from Utils.Debug import printOut
from Utils.Logger import Logger

class Select2AFCImage(Element):
    """
    Class to display two images and allow the user to select one or the other
    This object CANNOT be re-entered in the same execution, because the list
    of images is destroyed after the user has made the choices.
    Other copies of the Element can be defined in the experiment with different
    names without any issue.
    """

    def __init__(self, **kwargs):
        """
        Class constructor
        """
        # call parent constructor
        super(Select2AFCImage,self).__init__(**kwargs)

        # scale is used to change the size of the images
        sx, sz = getattr(self.config,'image_scale',[1.0,1.0])

        self.voffset = getattr(self.config,'image_voffset', -0.5)
        self.showReference = getattr(self.config,'show_reference')

        # in this DICTIONARY we will hold all the image Nodes
        self.imageNodes={}
        # for golden images
        self.imageRefNodes={}

        self.setupListPairs()

        postfix = getattr(self.config,'image_postfix','')
        prefix = getattr(self.config,'image_prefix','')

        try:
           # load every image into a Panda node and attach it to the
           # special hudNP node for 2d stuff
           # image pairs in the bottom
            for pair in self.image_pairs:
                for image in pair:
                    if image not in self.imageNodes.keys():
                        fullname = prefix + image + postfix
                        printOut("loading %s" % fullname, 0)
                        cm = CardMaker('card')
                        cm.setFrame(0,0.95,0,0.95)
                        self.imageNodes[image] = self.hudNP.attachNewNode(cm.generate())

                        tex = loader.loadTexture( fullname )
                        tex.setMagfilter(SamplerState.FT_nearest)
                        tex.setMinfilter(SamplerState.FT_nearest)

                        self.imageNodes[image].setTexture(tex)

                        self.imageNodes[image].setTransparency(TransparencyAttrib.MAlpha)
                        self.imageNodes[image].hide()
                        self.imageNodes[image].setName(image)
                        self.imageNodes[image].reparentTo(self.hudNP)
            # reference image if present
            for ref in self.image_pairs_refs:
                if ref not in self.imageRefNodes.keys():
                    fullname = prefix + ref + postfix
                    printOut("loading %s" % fullname, 0)
                    cm = CardMaker('card')
                    cm.setFrame(0,0.95,0,0.95)
                    self.imageRefNodes[ref] = self.hudNP.attachNewNode(cm.generate())
                    tex = loader.loadTexture( fullname )
                    tex.setMagfilter(SamplerState.FT_nearest)
                    tex.setMinfilter(SamplerState.FT_nearest)
                    self.imageRefNodes[ref].setTexture(tex)
                    #self.imageRefNodes[ref] = OnscreenImage( image=fullname, scale=Vec3(sx,1.0, sz) )
                    self.imageRefNodes[ref].setTransparency(TransparencyAttrib.MAlpha)
                    self.imageRefNodes[ref].hide()
                    self.imageRefNodes[ref].setName(ref)
        except Exception,e:
            printOut("Fatal error, could not load texture file",0)
            printOut(str(e), 0)
            return

#        # label text
        if getattr(self.config, 'choice_text', None):
            label = OnscreenText( text = self.config.choice_text,
                              pos = (0,-0.8,0), scale = .05,
                              fg= [1.0,1.0,1.0,1.0],
                              align=TextNode.ACenter,
                              wordwrap=15.0,
                              mayChange=0 )
        label.reparentTo(self.hudNP)
#

    def setupListPairs(self):
         # check if explicit list of pairs has been provided.
        if getattr(self.config, 'tuple_image_pairs', None) is None:
            printOut("Error constructing " + self.config.name + ", attribute 'image_pairs' is missing'", 0)

        # copy list ...
        image_pairs = list(self.config.tuple_image_pairs)
        image_pairs_refs = []

        if self.showReference:
            for p in image_pairs:
                if len(p) != 3:
                    printOut("ERROR: All images must be triplets if 'show_reference' is True", 0)
                    return
            image_pairs_refs = [pair[0] for pair in image_pairs]
            image_pairs = [pair[1:3] for pair in image_pairs]

        # check if mirrors are desired, and append them.
        if getattr(self.config,'mirror_pairs',None):
            size = len(image_pairs)
            for i in range(size):
                a,b = image_pairs[i]
                image_pairs.append([b,a])
                if self.showReference:
                    image_pairs_refs.append(a)
#
        if getattr(self.config,'random_pairs',None):
#           # shuffle BOTH LISTS (pairs and references) so they are kept in sync
            if self.showReference:
                combined = list(zip(image_pairs, image_pairs_refs))
                random.shuffle(combined)
                image_pairs[:], image_pairs_refs[:] = zip(*combined)
            else:
                random.shuffle(image_pairs)

        # keep a reference to variables
        self.image_pairs = image_pairs
        self.image_pairs_refs = image_pairs_refs


    def imageSelected(self,args):
        """This method should be called when one choice is made."""
        if len(self.image_pairs) == 0:
            return

        direction={'left':0,'right':1}
        currPair = self.image_pairs[0]
        if self.showReference:
            currGolden = self.image_pairs_refs[0]

        selection = currPair[direction[args]]
        answer_text = "Selected %s from %s -- %s " % (selection, currPair[0], currPair[1])
        if self.showReference:
            answer_text = answer_text + "golden: " + self.image_pairs_refs[0]
            if selection == self.image_pairs_refs[0]:
                answer_text = answer_text + " CORRECT"
            else:
                answer_text = answer_text + " MISS"
        printOut(answer_text, 1)
        self.logResults.logEvent(answer_text)

        #hide pair
        self.imageNodes[currPair[0]].hide()
        self.imageNodes[currPair[1]].hide()

        if self.showReference:
            self.imageRefNodes[currGolden].hide()

        # remove the first pair from the list,
        # the logfile will have the history of how things were presented.
        self.image_pairs.pop(0)
        if self.showReference:
            self.image_pairs_refs.pop(0)

        # display new pair only if there are more...
        if len(self.image_pairs):
            self.displayFirstPair()
        else:
            # exit the state sending the signal endComparison
            self.sendMessage('end_'+self.config.name)
#
    def displayFirstPair(self):
        # UNHIDE the images, and displace them on left and right
        # TUPLES CANNOT BE SHUFFLED, BECAUSE THEY ARE INMUTABLE.
        pair = self.image_pairs[0]
        self.imageNodes[pair[0]].show()
        self.imageNodes[pair[0]].setPos(-1.7, 0.0, -0.95)
        self.imageNodes[pair[1]].show()
        self.imageNodes[pair[1]].setPos(0.7, 0.0, -0.95)
        # only when there is a golden reference at the top.
        if self.showReference:
            self.imageRefNodes[self.image_pairs_refs[0]].show()
            self.imageRefNodes[self.image_pairs_refs[0]].setPos(-0.5, 0.0, -0.1)

    def enterState(self):
        Element.enterState(self)

        #        # file output to store the results
        outputDir = getattr(self.config,'output_answers','run')
        logName = outputDir+"\\"+self.config.name+"_"+self.config.world.participantId+".log"
        self.logResults = Logger(self.baseTime, logName,mode='w')

        # display always the first one, because they have
        # been randomized in the constructor anyway...
        if len(self.image_pairs) == 0:
            self.setupListPairs()
        self.displayFirstPair()

    def exitState(self):
        # we could unload the images here...
        Element.exitState(self)
        self.logResults.stopLog()


