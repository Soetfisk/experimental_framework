from Utils.Debug import printOut, verbosity

class Keyboard():
    """trivial wrapper around the panda messenger focused on keyboard handling"""

    def __init__(self, msn):
        """ Receives a reference to the messenger object in Panda3D,
        and uses it to register/remove keyboard callbacks"""
        self.msn = msn
        self.data = {}
        self._keysOrder = []

    def registerKey(self,key, callback, comment="", once=False, arguments=[], display=True):
        """ registers a key with the messenger, to call a callback with
        arguments when something happens,
        it also remembers the order in which keys has been added!"""
        printOut("Registering key: %s to %s" % (key,str(callback)),2)
        try:
            if (once):
                self.msn.acceptOnce(key,callback,arguments)
            else:
                self.msn.accept(key,callback,arguments)
            self.data[key] = (callback, comment, display)
            self._keysOrder.append(key)
        except Exception, e:
            print e

    def getKeys(self):
        """Returns registered keys"""
        # only return those that are displayable!
        return [k for k in self._keysOrder[:] if self.data[k][2]]

    def getTextKey(self,key):
        """for a given key, returns the text that explains what it does"""
        printOut("getTextKey with %s"%key,2)
        return "Key %s: %s" % (key,self.data[key][1])

    def unregKey(self,key):
        self.msn.ignore(key)
        del(self.data[key])
        self._keysOrder.remove(key)

    def clearKeys(self):
        """Removes ALL keys and callbacks"""
        [self.unregKey(k) for k in self.data.keys()]


