from Utils.Debug import printOut

class Keyboard():
    """trivial wrapper around the panda messenger focused on keyboard handling"""

    def __init__(self, msn):
        """ Receives a reference to the messenger object in Panda3D,
        and uses it to register/remove keyboard callbacks"""
        self.msn = msn
        self.data = {}
        self._keysOrder = []

    def registerKey(self, key, registrant, callback,
                    comment="", once=False,  arguments=[], display=True):
        """ registers a key with the messenger, to call a callback with
        arguments when something happens,
        it also remembers the order in which keys has been added, and if display is True
        it will show the key when the help is shown (using key h)"""
        try:
            if key in self.data:
                printOut("Key %s from: '%s', has been already registered" %
                         (key, registrant), 0)
                printOut("The key is registered under: %s" % str(self.data[key]), 0)
                printOut("Change your binding, ignoring for now")
                return False

            if once:
                self.msn.acceptOnce(key, callback, arguments)
            else:
                self.msn.accept(key, callback, arguments)

            self.data[key] = (registrant, callback, comment, display)
            self._keysOrder.append(key)
            printOut("Registering key: %s to callback %s for %s" %
                     (key, str(callback), registrant) + "with args:" + str(arguments), 2)
            return True
        except Exception, e:
            print e
            return False

    def getKeys(self):
        """Returns registered keys"""
        # only return those that are displayable!
        # as keys are stored in a tuple like:  (registrant, callback, comment, display)
        return [k for k in self._keysOrder[:] if self.data[k][3]]

    def getTextKey(self, key):
        """for a given key, returns the comment that explains what it does"""
        printOut("getTextKey with %s" % key, 2)
        # keys are stored in a tuple like:  (registrant, callback, comment, display)
        return "Key %s: %s" % (key, self.data[key][2])

    def unregKey(self, key):
        try:
            del(self.data[key])
            self._keysOrder.remove(key)
            self.msn.ignore(key)
            return True
        except Exception, e:
            printOut("Error unregistering key %s" % key, 0)
            print e
            return False

    def clearKeys(self):
        """Removes ALL keys and callbacks"""
        [self.unregKey(k) for k in self.data.keys()]


