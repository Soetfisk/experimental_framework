__author__ = 'Francholi'

from Debug import printOut
from Utils import *

FSM_RES = enum(FSM_KEY_ERROR=0, FSM_INCOMPLETE=1, FSM_OK=2)

"""
This finiteStateMachine allows for CONCURRENT states,
so it is a bit more complex when transitioning
from one state to another

The transitions in YAML are defined as follows:
{'currentState':{'event':['dest1','dest2'] } }
Meaning, from currentState I can go to dest1 and dest2 if 'event' happens
"""

# splits a transition string into a tuple of LISTS of strings
# ([fromStates],[toStates],[events])
def splitTransitionString(transition):
    try:
        if ':' in transition:
            events = transition.split(':')[1].strip()
            events = events.split(',')
        else:
            events = ['auto']

        # parse the transition "fromA,fromB @ toA,toB : whenEvt"
        temp = transition.split('@')
        temp[1] = temp[1].split(':')[0]

        fromStates = [f.strip() for f in temp[0].strip().split(',')]
        toStates = [f.strip() for f in temp[1].strip().split(',')]

        return (fromStates, toStates, events)
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
            if s.isActive():
                sName = s.config.name
                if sName in self.transitions.keys():
                    accepts = self.transitions[sName].keys()
                    if event in accepts:
                        # list of states to which transition.
                        updateLast += self.transitions[sName][event]
                        print "%s(%s) ---> %s" % (sName, event, self.transitions[sName][event])
                        # exit state, and enter in one or many more.
                        s.exitState()
        for newState in list(set(updateLast)):
            self.states[newState].enterState()

    def forceState(self, state):
        """Force the state machine to 'jump' to the given state, by exiting any current
        state, and entering a SINGLE state. The main purpose of this is for debugging."""
        # brute force exit (even possibly 'state')
        [ s.exitState() for s in self.states.values() if s.isActive() ]
        # enter if state exists
        if self.states.get(state,None): self.states[state].enterState()

    def getTransitions(self):
        return self.transitions
