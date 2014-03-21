from panda3d.core import *
import sys
from Utils.Debug import printOut
from Utils.Utils import *
try:
    import json
except ImportError:
    import simplejson as json

import yaml

class Element(object):
    """ Base class for the Elements in the experiment.
    Each element represents ONE stage in the experiment,
    for example, one image, a text message, a timer,
    a game!, a pilot...
    """
    def __init__(self,**kwargs):
        """
        The constructor does a lot of work already, adding all the
        kwargs keys to attributes to this object. Setting basic members
        for the subclases such as the world (DirectObject), the name,
        the 3d node in the scene and a hud node in the scene.
    """
        # this changes when the states is activated.
        self.active = False

        for k,v in kwargs.items():
          # make every argument from the config file an attribute, including a reference
          # to world through self.world
          setattr(self, str(k), v)

        # add the basic 2D and 3D nodepaths in the scenegraph for this element
        self.sceneNP = NodePath(self.name)
        self.sceneNP.hide()
        self.hudNP   = NodePath(self.name+'_hud')
        self.hudNP.hide()
        # these are basic nodepaths to attach the specific stuff of this
        # element. (text,graphics,anything else)
        self.world.addNode(self.sceneNP,place='3d')
        self.world.addNode(self.hudNP,place='HUD')

        # load an additional config file for the element, and leave it
        # available for the subclass to do whatever it wants.
        # TODO: PORTING FROM JSON TO YAML
        c = getattr(self,'config_json',None)
        if (c is None):
            c = getattr(self,'config_yaml',None)

        # TODO: PORTIG FROM JSON TO YAML
        try:
            if (c is not None):
                if 'yaml' in c:
                    dictionary = yaml.load(open(c))
                elif 'json' in c:
                    dictionary = json.load(open(c))
                else:
                    printOut("config file format not supported!", 0)
                    self.world.quit()
                self.config = objFromDict(dictionary)
                printOut("CONFIG LOADED FOR %s" % self.name, 4)
        except Exception,e:
            print e
            printOut("Fatal error loading config file "+ c, 0)
            self.world.quit()

        self.registeredKeys = []

    def setKeyboard(self, keyboard):
        self.kbd = keyboard

    def log(self, message):
        self.world.logEvent(message)

    def setTimeOut(self,time):
        # after 'time' a message 'timeout' will be send to the message manager,
        # and if anyone registered to listen for 'timeout' messages they will
        # react
        taskMgr.doMethodLater(time, self.world.advanceFSM, 'timeout', extraArgs=[])

#===============================================================================
    def registerKeys(self):
        """Try to setup some keys to callbacks using the YAML file
        specific for this element, or the keys dictionary key if exists
        in the Element description"""

        # Keys defined in the EXPERIMENT FILE, when the Element is created
        temp_keys = getattr(self,"keys",[])
        exp_keys = []
        for k in temp_keys:
            exp_keys.append(objFromDict(k))

        # Keys defined in the specific configuration file for this
        # instance of the element
        config = getattr(self, "config",None)
        if config:
            config_keys = getattr(config, 'keys',[])
        else:
            config_keys = []
        # add both lists of keys, first one will prevail if they repeat.
        keys = exp_keys + config_keys

        printOut("Registering keys for the current element", 4)
        for k in keys:
            comment = getattr(k, 'comment', '')
            cb = getattr(self, k.callback, None)
            key = getattr(k, 'key', None)
            once = getattr(k, 'once', False)
            args = getattr(k, 'args', [])
            # force args to be a list...
            if not isinstance(args, list):
                args = [args]
            if key is None or cb is None:
                printOut('Error!, key or callback missing in when '
                         'setting up %s' % self.name, 0)
                printOut('Ignoring that keybinding', 0)
                self.world.quit()
            # this will give us back a [] even if no 'commas' are found
            for eachKey in key.split(','):
                # this could return false in case the key has already been registered
                if self.kbd.registerKey(eachKey, self.name, cb, comment, once, args):
                    self.registeredKeys.append(eachKey)
        else:
            printOut("No keys added by element %s" % self.name, 1)

    def unregisterKeys(self):
        printOut("De-registering keys for the current element", 4)
        for k in self.registeredKeys:
            if self.kbd.unregKey(k):
                printOut("Unregistered key from %s: %s" % (self.name, k), 4)
            else:
                printOut("Unable to unregister key from %s: %s" % (self.name, k), 0)

    def needsToSaveData(self):
        return False

    def saveUserData(self):
        return

    def hideElement(self):
        #print "HIDE ELEMENT IN Element.py " + self.name
        self.hudNP.hide()
        self.sceneNP.hide()

    def showElement(self):
        self.hudNP.show()
        self.sceneNP.show()

    def sendMessage(self, message):
        messenger.send(message,[message])

    def enterState(self):
        """
        This method will be executed when the Finite State Machine
        enters into this state
        """
        printOut("Entering state %s" % self.name, 1)
        #self.world.resetKeys()
        self.showElement()
        self.registerKeys()

        # is there a timeout set for this state ?
        t = getattr(self, 'timeout', None)
        if t is not None:
            try:
                t = float(t)
                if t:
                    taskMgr.doMethodLater(t, self.world.advanceFSM,
                    'timeout'+self.name, extraArgs=['auto'])
            except:
                printOut("error converting timeout value %s in %s " % (str(t), self.name), 0)
                self.world.quit()
        #self.world.createTextKeys()
        self.active = True

        # check if we need to load values from globals! or set them
        # to the defaults specified in the configuration of the Element
        # check the experiment!
        globals = getattr(self, 'readFromGlobals', None)
        if globals:
            for g in globals:
                if g in self.world.globals:
                    setattr(self, g, self.world.globals[g])
                else:
                    setattr(self, g, globals[g])


    def exitState(self):
        """
        This method will be executed when the Finite State Machine
        exits from this state
        """
        self.hideElement()
        taskMgr.remove('timeout'+self.name)
        self.unregisterKeys()
        printOut("Leaving state %s" % self.name,2)
#        self.world.createTextKeys()
        self.active = False

        # save globals if we have them.
        globals = getattr(self, 'saveGlobals', None)
        if globals:
            for g in globals:
                localValue = getattr (self, g, globals[g])
                self.world.globals[g] = localValue

    def isActive(self):
        return self.active

#    def createService(self, serverName, serviceName, callback):
#       """ Creates and registers a service in the ServiceMgr to handle
#       queries of data obtained in the data form """
#       service = self.world.serviceMgr.createFromTemplate( serviceName )
#       service.setServerName(serverName)
#       service.setServiceImp( self.getUserData )
#       # register service
#       self.world.serviceMgr.registerService ( service )

