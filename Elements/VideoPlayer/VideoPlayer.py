__author__ = 'Francholi'
__author__ = 'Francholi'

# panda imports
from Elements.Element.Element import *
from pandac.PandaModules import CardMaker, TextureStage

class VideoPlayer(Element):
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
        super(VideoPlayer, self).__init__(**kwargs)

        self.videofile = getattr(self.config, 'file_video',None)
        self.loopCount = getattr(self.config, 'loop', 1)
        #self.playrate = getattr(self.config, 'speed', 1.0)

        if self.videofile:
            movieTexture = loader.loadTexture(self.videofile)
            cm = CardMaker("video_card")
            # cm.setFrameFullscreenQuad()
            cm.setUvRange(movieTexture)
            card = NodePath(cm.generate())
            card.reparentTo(self.hudNP)
            card.setTexture(movieTexture)
            card.setTexScale(TextureStage.getDefault(), movieTexture.getTexScale())
            self.movie = movieTexture
            self.stop()


        self.hideElement()

    def play(self, args=[]):
        self.movie.play()
        print 'play'

    def stop(self, args=[]):
        self.movie.stop()
        print 'stop'

    def rewind(self):
        print 'rewind'

    def forward5(self):
        print 'forward'

    def backward5(self):
        print 'backward'

    def setVolume(self, newVol):
        """volume between 0 and 1"""
        pass
        # self.audio.setVolume(newVol)

    def decVolume(self):
        """decrease volume by 10%"""
        # newVol = self.audio.getVolume() - 0.1
        # newVol = 0.0 if newVol<0.0 else newVol
        # self.audio.setVolume(newVol)
        pass

    def incVolume(self):
        """increase volume by 10%"""
        # newVol = self.audio.getVolume() + 0.1
        # newVol = 1.0 if newVol>1.0 else newVol
        # self.audio.setVolume(newVol)
        pass

    def enterState(self):
        # super class enterState
        Element.enterState(self)

    def exitState(self):
        # super class exitState
        try:
            self.stop()
        except:
            pass
        Element.exitState(self)


