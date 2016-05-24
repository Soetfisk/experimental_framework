__author__ = 'Francholi'
__author__ = 'Francholi'

# panda imports
from Element import *

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
        textureName = getattr(self.config,'fname_image', 'common/images/not_found.png')

        texture = loader.loadTexture(textureName)
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

        #self.hideElement()

    def enterState(self):
        # super class enterState
        Element.enterState(self)
        #self.showElement()

    def exitState(self):
        # super class exitState
        Element.exitState(self)

    def getConfigTemplate(self):
        elementDict = Element.getConfigTemplate()
        return elementDict
        
