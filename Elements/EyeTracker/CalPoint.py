from panda3d.core import *
from direct.interval.IntervalGlobal import *

class calStimuli(object):
    """A callibration point is a 2d rectangle with some image
    textured covering the whole are"""

    def __init__(self, node, zplane=0.0):
        """
        Constructs a calibration stimuli.
        @node is the parent node in the scene graph
        @zplane the base z distance for all the planes
        """
        self.zplane = zplane
        # references to textures
        self.textures = []
        # references to NodePaths to the nodes that have the texture
        self.models = []
        # shrink factor when reached the destination
        self.shrink = []
        # scale factor beforehand when creating the textured quad.
        self.scales = []

        # parent of all
        parent = NodePath('calStimuli')

        # depth test in this node (and all the children)
        parent.setDepthTest(True)
        parent.setDepthWrite(True)
        parent.reparentTo(node)
        self.parent = parent


    def addTexture(self, name, texture, scale, order, shrink=None):
        """
        Adds a plane and a texture on top of it
        @texture: an already loaded texture object
        @scale: a rescaling factor for the plane
        @order: if there are more than one textures, with alpha
                blending, then they can be ordered.
                order n is IN FRONT of order (n+1)
        """
        # texture setting
        texture.setMinfilter(Texture.FTLinearMipmapLinear)
        texture.setAnisotropicDegree(2)
        self.textures.append(texture)

        # load a rectangle to map the texture
        model = loader.loadModel("models/plane")
        model.setName(name)
        model.setScale(scale)
        self.scales.append(scale)
        # this will set how the planes are going to be drawn on the screen,
        # so if alpha layers are present we can overlay textures
        model.setY(-order)
        
        # opaque
        model.setTransparency(1)
        # set texture (rectangular UVs coming from the plane model)
        model.setTexture(self.textures[-1])
        model.reparentTo(self.parent)

        self.shrink.append(shrink)
        self.models.append(model)

    def createScaleIntervals(self, fixationTime):
        # for each node that has to be shrinked, we create a scaleInterval
        downSI=[]
        upSI=[]
        for shrink,scale,node in zip(self.shrink,self.scales, self.models):
            if (shrink is not None):
                downSI.append(node.scaleInterval(  fixationTime, Point3(shrink,shrink,shrink)) )
                                                #,blendType=animationCurve))
                upSI.append(node.scaleInterval( fixationTime, Point3(scale,scale,scale)) )
                                             #,blendType=animationCurve))

        # Parallel accepts a list of Sequences, Intervals or Parallels.
        self.shrinkParallel = Parallel( *downSI, name='shrink parallel' )
        self.scaleParallel  = Parallel( *upSI,   name='scale parallel'  )


    def setPosition(self,x,y):
        """Sets position FOR ALL THE NODES, using Aspect2d dimensions"""
        self.parent.setX(x)
        self.parent.setZ(y)

    def moveTo(self,newX,newY,animationCurve, time):
        """
        Moves ALL THE NODES from the current position to the
        new position.
        In addition, scales down the nodes that have the shrink property
        different from None.
        @newX,newY are the new positions
        @animationCurve is how to animate (look in the config file!)
        @time is the time from the current pos to the next one.
        """
        # we move the parent node (all children)
        posInt = self.parent.posInterval(   time, 
                                            Point3(newX,self.zplane,newY),
                                            blendType=animationCurve)

        self.moveSequence = Sequence(posInt, self.shrinkParallel, self.scaleParallel )
        self.moveSequence.start()
        return


