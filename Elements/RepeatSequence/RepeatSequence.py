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
        self.variable = ''
        self.hideElement()

    def enterState(self):
        # super class enterState
        Element.enterState(self)

        # if the attribute values has not been defined, it means it is the first time we iterate in
        # the loop
        if (getattr(self, 'values',None) is None):
            self.values = [ s.replace('$pid$', self.config.world.participantId) for s in self.config.values ]
            if self.config.random:
                random.shuffle(self.values)

        #if varName not in self.config.world.globals.keys():
            # take the list of values, save it, randomize if necessary.
            # replace string $pid$ with real pid of the participant

        if len(self.values):
            # both names can be used "variable" or the value in the config file.
            self.variable = self.values.pop()
            setattr(self, self.config.variable, self.variable)
            self.sendMessage('repeat')
        else:
            self.sendMessage('end')

    def getVariable(self):
        return self.variable

    def exitState(self):
        # super class exitState
        Element.exitState(self)


