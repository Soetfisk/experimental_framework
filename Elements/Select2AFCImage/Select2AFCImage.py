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
    """

    def __init__(self, **kwargs):
        """
        Class constructor
        """
        # call parent constructor
        super(Select2AFCImage,self).__init__(**kwargs)

        # scale is used to change the size of the images
        sx, sz = getattr(self.config,'tuple_scale',[1.0,1.0])

        # in this DICTIONARY we will hold the images
        self.imageNodes={}

        # check if explicit list of pairs has been provided.
        tempImagePairs = getattr(self.config,'imagePairs',None)

        # if tempImagePairs does not exist, read file names from directory
        if not tempImagePairs:
            try:
                files = os.listdir(self.config.imagePath)
                # remove extension from filename
                files = [ x.rsplit('.',1)[0] for x in files]
                # compute all pairs as a result of a combination of filenames
                tempImagePairs = list(itertools.combinations(files,2))
            except AttributeError,e:
                printOut("Attribute imagePath in config file does not exist!")
                self.config.world.quit()
            except WindowsError,e:
                printOut("Directory %s with images does not exist!" % self.config.imagePath)
                self.config.world.quit()

        # check if mirrors are desired, and append them.
        if getattr(self.config,'genMirrorPair',None):
            for i in range(len(tempImagePairs)):
                a,b = tempImagePairs[i]
                tempImagePairs.append((b,a))

        if getattr(self.config,'randomizePairs',False):
            # shuffle the image pairs before start
            random.shuffle(tempImagePairs)

        self.imagePairs = tempImagePairs

        # if extension has been set use it, otherwise assume PNG
        imageExtension = getattr(self.config,'imageExtension','.png')

        try:
            # load every image into a Panda node and attach it to the
            # special hudNP node for 2d stuff
            for pair in self.imagePairs:
                for p in pair:
                    if p not in self.imageNodes.keys():
                        finalname = self.config.imagePath + p + imageExtension
                        printOut("loading %s" % finalname)
                        self.imageNodes[p] = OnscreenImage(
                            image=finalname,
                            scale=Vec3(sx,1.0, sz))
                        self.imageNodes[p].setTransparency(TransparencyAttrib.MAlpha)
                        self.imageNodes[p].hide()
                        self.imageNodes[p].setName(p)
                        self.imageNodes[p].reparentTo(self.hudNP)
        except Exception,e:
            printOut("Fatal error, could not load texture file",0)
            printOut(str(e), 0)
            self.config.world.quit()

        # label text
        label = OnscreenText( text = "Which path feels most SAFE?",
                              pos = (0,0.9,0),
                              scale = .08,
                              fg= [1.0,1.0,1.0,1.0],
                              align=TextNode.ACenter,
                              mayChange=0 )
        label.reparentTo(self.hudNP)
        # place holder to write

        # file output to store the results
        outputDir = getattr(self.config,'logOutputDir','run')
        self.logResults = Logger(self.baseTime, outputDir+"/userAnswers_"+self.config.world.participantId+".log",mode='w')
        #self.currentPair = None

    def hidePair(self, pair):
        left, right = pair
        self.imageNodes[left].hide()
        self.imageNodes[right].hide()
        # remove the first pair from the list
        self.imagePairs.pop(0)

    def imageSelected(self,args):

        currPair = self.imagePairs[0]
        selection = None
        if (args == 'right'):
            selection = currPair[1]
        elif args == 'left':
            selection = currPair[0]
        else:
            printOut('invalid message passed to imageSelected!!!')
            self.config.world.quit()

        answerText = "Selected {s} from {p[0]} -- {p[1]}".format(p = currPair, s=selection)

        self.logResults.logEvent(answerText)

        #hide pair
        self.imageNodes[currPair[0]].hide()
        self.imageNodes[currPair[1]].hide()

        # remove the first pair from the list
        self.imagePairs.pop(0)

        # display new pair only if there are more...
        if len(self.imagePairs):
            self.displayPair(self.imagePairs[0])
        else:
            # exit the state sending the signal endComparison
            self.sendMessage('endComparison')

    def displayPair(self, pair):
        # UNHIDE the images, and displace them on left and right
        # they could also be randomized here, so that not always
        # a goes left and b goes right
        # TUPLES CANNOT BE SHUFFLED, BECAUSE THEY ARE INMUTABLE.
        self.imageNodes[pair[0]].show()
        self.imageNodes[pair[0]].setPos(-0.8, 1.0, 0.0)
        self.imageNodes[pair[1]].show()
        self.imageNodes[pair[1]].setPos(0.8, 1.0, 0.0)

    def enterState(self):
        Element.enterState(self)
        self.logResults.startLog()
        # display always the first one, because they have
        # been randomized in the constructor anyway...
        self.displayPair(self.imagePairs[0])

    def exitState(self):
        # we could unload the images here...
        Element.exitState(self)
        self.logResults.stopLog()


