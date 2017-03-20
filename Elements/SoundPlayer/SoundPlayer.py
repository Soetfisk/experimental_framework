__author__ = 'Francholi'
__author__ = 'Francholi'

# panda imports
from Elements.Element.Element import *

class SoundPlayer(Element):
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
        super(SoundPlayer, self).__init__(**kwargs)

        self.audiofile = getattr(self.config, 'file_sound',None)
        self.loopCount = getattr(self.config, 'loop', 1)
        self.playrate = getattr(self.config, 'speed', 1.0)

        if self.audiofile:
            self.audio = base.loader.loadSfx(self.audiofile)
            if self.audio.status() != AudioSound.READY:
                self.audio = None
            else:
                self.audio.setLoopCount(self.loopCount)
                self.audio.setPlayRate(self.playrate)
        else:
            self.audio = None

        self.hideElement()

    def play(self, args=[]):
        if self.audio:
            self.audio.play()

    def stop(self, args=[]):
        if self.audio:
            self.audio.stop()

    def setSpeed(self, newSpeed):
        self.audio.setPlayRate(newSpeed)

    def setVolume(self, newVol):
        """volume between 0 and 1"""
        self.audio.setVolume(newVol)

    def decVolume(self):
        """decrease volume by 10%"""
        newVol = self.audio.getVolume() - 0.1
        newVol = 0.0 if newVol<0.0 else newVol
        self.audio.setVolume(newVol)

    def incVolume(self):
        """increase volume by 10%"""
        newVol = self.audio.getVolume() + 0.1
        newVol = 1.0 if newVol>1.0 else newVol
        self.audio.setVolume(newVol)

    def enterState(self):
        # super class enterState
        Element.enterState(self)

    def exitState(self):
        # super class exitState
        try:
            self.audio.stop()
        except:
            pass
        Element.exitState(self)


