__author__ = 'Francholi'
__author__ = 'Francholi'

# panda imports
from Elements.Element.Element import *

class DecisionNode(Element):
    """
    This Element does a very simple task, checks a boolean expression,
    and sends a message.
    The message should match one of the transitions defined in the FSM.
    The variable names that can be used in the expression are the global
    variables, that any Element can read or write using readFromGlobals
    and writeFromGlobals.
    The expression can use the variable without any additional namespace
    """
    def __init__(self, **kwargs):
        """
        See the Element class to find out what attributes are available
        from scratch
        """
        super(DecisionNode, self).__init__(**kwargs)
        self.hideElement()

    def enterState(self):
        # super class enterState
        Element.enterState(self)

        # for each global variable defined so far by other elements,
        # create a local variable so that the expression can be
        # evaluated here without hassle.
        for v in self.config.world.globals.keys():
            # example:
            # var = self.config.world.globals['var']
            # python code to execute
            declareStr = '%s = self.config.world.globals[\'%s\']' % (v,v)
            # execute it!
            exec(declareStr)

        # TODO: add try/catch for the different errors that can happen here!
        # evaluate each condition and if true, send message and break.
        for cond in self.config.conditions:
            try:
                if eval(cond.cond):
                    printOut("(%s) is True, send message %s" % (cond.cond, cond.msg),0)
                    # apply any statement before sending the message.
                    self.sendMessage(cond.msg)
                    # exitState will be called automatically by the FSM
                    return
            except NameError,n:
                printOut("FATAL: Expression '%s' uses an undefined global variable: \"%s\"" % (cond.cond,n))
                self.config.world.quit()

    def exitState(self):
        # super class exitState
        Element.exitState(self)


