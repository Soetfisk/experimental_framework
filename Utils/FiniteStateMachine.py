__author__ = 'Francholi'

from Element import Element

"""
This finiteStateMachine allows for concurrent
states, so it is a bit more complex when transitioning
from one state to another
The transitions are encoded as follows:
{'currentState':{'event':['dest1','dest2'] } }
"""
class FiniteStateMachine(object):
    def __init__(self, newTransitions, elements):
        self.transitions = newTransitions
        self.states = elements

        # fix end transition to do nothing
        self.transitions['end'] = {}

    def hasDone(self):
        """
        Check if there are no active states.
        and the only active state is the "end" state
        """
        for s in self.states.values():
            if s.isActive() and s.config.name != 'end':
                return False
        else:
            if self.states['end'].isActive():
                return True

    def processEvent(self, event):
        updateLast = []

        for s in self.states.values():
            sName = s.config.name
            if sName in self.transitions.keys():
                accepts = self.transitions[sName].keys()
                if s.isActive() and event in accepts:
                    # list of states to which transition.
                    updateLast += self.transitions[sName][event]
                    print "%s(%s) ---> %s" % (sName, event, self.transitions[sName][event])
                    # exit state, and enter in one or many more.
                    s.exitState()
        for newState in list(set(updateLast)):
            self.states[newState].enterState()

    def getTransitions(self):
        return self.transitions
