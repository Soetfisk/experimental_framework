__author__ = 'Francholi'
__author__ = 'Francholi'

# panda imports
from direct.gui.DirectGui import *
from direct.task.Task import *
from panda3d.core import *
from Element import *

#sys utils
import sys

class EmptyState(Element):
    """
    As the name indicates, it's an empty state. It does nothing.
    """

    def __init__(self, **kwargs):
        """
        world is a reference to the main class
        """
        super(EmptyState, self).__init__(**kwargs)
        self.hideElement()

    def enterState(self):
        # print "entering ScreenText"
        # super class enterState
        Element.enterState(self)

    def exitState(self):
        # print "leaving state ScreenText"
        Element.exitState(self)

