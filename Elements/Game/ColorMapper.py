from panda3d.core import *

# helper class to map common colour names to Vec4 objects
class ColorMapper(object):
    def __init__(self):
        self.c = {}
        self.c['RED'] =     Vec4(1.0,0.0,0.0,1.0)
        self.c['BLUE'] =    Vec4(0.0,0.0,1.0,1.0)
        self.c['GREEN'] =   Vec4(0.0,1.0,0.0,1.0)
        self.c['YELLOW'] =  Vec4(0.0,1.0,1.0,1.0)
        self.c['MAGENTA'] = Vec4(1.0,0.0,1.0,1.0)
        self.c['dark_grey'] = Vec4(0.3,0.3,0.3,1.0)
        self.c['light_red'] = Vec4(0.5,0.0,0.0,1.0)
        return
    def getColors(self):
        return self.c


