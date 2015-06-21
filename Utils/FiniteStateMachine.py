__author__ = 'Francholi'

from Element import Element
from Debug import printOut
from Utils import *

FSM_RES = enum(FSM_KEY_ERROR=0, FSM_INCOMPLETE=1, FSM_OK=2)

"""
This finiteStateMachine allows for concurrent
states, so it is a bit more complex when transitioning
from one state to another
The transitions are encoded as follows:
{'currentState':{'event':['dest1','dest2'] } }
"""

# splits a transition string into a tuple of strings (fromState,toState,event)
def splitTransitionString(transition):
    try:
        if ':' in transition:
            evt = transition.split(':')[1].strip()
        else:
            evt = 'auto'
        # parse the transition "fromA @ toB : whenEvt"
        fromState, toState = transition.split('@')
        fromState = fromState.strip()
        toState = toState.split(':')[0].strip()
        return (fromState, toState, evt)
    except:
        printOut("Malformed transition: " + transition, 0)
        printOut("fix the file and press ctrl+R")


class FiniteStateMachine(object):
    def __init__(self, newTransitions, elements):
        self.transitions = newTransitions
        self.states = elements
        # fix end transition to do nothing
        self.transitions['end'] = {}
        # check that the FSM is correct, meaning at least
        # that all states mentioned in the transitions exist.
        missing = [ el for el in self.transitions.keys() if el not in self.states.keys()]
        if len(missing) > 0:
            printOut("Fatal error, the FSM has names that are not defined",0)
            printOut("Missing elements: %s" % missing,0)
            self.valid = False
        else:
            self.valid = True

    def isValid(self):
        return self.valid

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
