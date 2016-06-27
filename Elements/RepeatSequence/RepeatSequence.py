__author__ = 'Francholi'
__author__ = 'Francholi'

# panda imports
from Elements.Element.Element import *
import random

class RepeatSequence(Element):
    """
    Set up a global variable name, set one value to it when entering
    to the Element, then set a new value every time until all values
    have been set.
    This Element has to remember if it has been called already before.
    """
    def __init__(self, **kwargs):
        """
        See the Element class to find out what attributes are available
        from scratch
        """
        super(RepeatSequence, self).__init__(**kwargs)
        self.hideElement()

    def enterState(self):
        # super class enterState
        Element.enterState(self)
        varName = self.config.variable
        # FIRST TIME, THE KEY DOES NOT EXIST.
        if varName not in self.config.world.globals.keys():
            # take the list of values, save it, randomize if necessary.
            self.values = self.config.values
            if self.config.random:
                random.shuffle(self.values)
        # ALWAYS DO THIS
        if len(self.values):
            self.config.world.globals[varName] = self.values.pop()
            self.sendMessage('repeat')
        else:
            self.sendMessage('end')

    def exitState(self):
        # super class exitState
        Element.exitState(self)


