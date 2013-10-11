from panda3d.core import *
import sys
from Utils.Debug import printOut, verbosity
from Utils.Utils import *
try:
    import json
except ImportError:
    import simplejson as json


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

        for k,v in kwargs.items():
          # convert to string
          # this sets the world attribute, which is a reference to the World object.
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
        c = getattr(self,'s_config_json',None)
        if (c is not None):
          try:
            # parse json to a dictionary, and convert to plain object
            dictionary = json.load(open(c))
            self.jsonConfig = objFromDict(dictionary)
            printOut("JSON CONFIG LOADED FOR %s" % self.name, 1)
          except Exception,e:
            print e
            print "Fatal error loading config file "+ c
            print "Check experiments.json"
            self.world.quit()

    #def convertValue(self,key,value):
    #    """
    #     helper function to map from string values to datatypes!
    #     This defines the convention used to read the XML keys
    #    """
    #    if (key[0] not in ['i','f','s','b','r']):
    #        print "invalid key name!, please follow the convention"
    #        sys.exit()
#
#        # scalars must start with i or f.
#        scalar={'i':int,'f':float}
#        v = value.split(',')
#        # is it a scalar?
#        if (key[0] in scalar.keys()):
#            v = map(scalar[key[0]], v)
#            # is it a single value?
#            if len(v)==1: v = v[0]
#        # if not, then string, bool or rating
#        else:
#            if (key[0]=='s'): v = str(value)
#            if (key[0]=='r'): v = v
#            if (key[0]=='b'): v = value=='True'
#        return v

    def setKeyboard(self, keyboard):
        self.kbd = keyboard

    def setTimeOut(self,time):
        # this method can be used to exit this state
        # after a given time out
        # print "Setting timeout of %f for state %s" % (time, self.name)
        taskMgr.doMethodLater(time, self.world.advanceFSM, 'timeout', extraArgs=[])

#===============================================================================
    def registerKeys(self):
        """Try to setup some keys to callbacks using the JSON file
        specific for this element, if the JSON is not defined then 
        simply skip this method"""

        # is there a specific configuration ?
        config = getattr(self, "jsonConfig", None)
        if (config):
            printOut("Custom config file for element %s" % self.name,1)
            # does it contain a list called 'keys' made of
            # of dicts {'key':'a','comment':'comment','callback':method} 
            json_keys = getattr(config,'keys',None)
            if (json_keys):
                printOut("Registering keys for the current element",1)
                for k in json_keys:
                    comment = getattr(k, 'comment','')
                    cb = getattr(self, k.callback, None)
                    key = getattr(k, 'key', None)
                    once = getattr(k,'once',False)
                    args = getattr(k,'args',[])
                    # force args to be a list...
                    if (not isinstance(args,list)):
                        args = [args]
                    if (key is None or cb is None):
                        printOut('Error!, key or callback missing in %s'%k,0)
                        self.world.quit()
                    self.kbd.registerKey(key,cb,comment,once,args)
            else:
                printOut("No keys added by element %s"%self.name,1)

    def unregisterKeys(self):
        printOut("De-registering keys for the current element",1)
        config = getattr(self, "jsonConfig", None)
        if (config):
            keys = getattr(config,'keys',None)
            if (keys):
                for k in keys:
                    try:
                        self.kbd.unregKey(k.key)
                    except:
                        printOut("Error unregistering key %c" % k.key, 0)
    #===============================================================================

    def hideElement(self):
        #print "HIDE ELEMENT IN Element.py " + self.name
        self.hudNP.hide()
        self.sceneNP.hide()

    def showElement(self):
        printOut("SHOW ELEMENT IN Element.py",3)
        self.hudNP.show()
        self.sceneNP.show()

    def enterState(self):
        """
        This method will be executed when the Finite State Machine
        enters into this state
        """
        printOut("Entering state %s" % self.name,2)
        self.showElement()
        self.registerKeys()

        # is there a timeout set for this state ?
        t = getattr(self,'f_timeout',None)
        if (t is not None):
            try:
                t = float(t)
                if (t):
                    taskMgr.doMethodLater(t, self.world.advanceFSM,
                    'timeout'+self.name, extraArgs=[])
            except:
                printOut("error converting timeout value %s in %s "%(str(t),self.name),0)
                self.world.quit()
        self.world.createTextKeys()

    def exitState(self):
        """
        This method will be executed when the Finite State Machine
        exits from this state
        """
        self.hideElement()
        taskMgr.remove('timeout'+self.name)
        self.unregisterKeys()
        printOut("Leaving state %s" % self.name,2)
        self.world.createTextKeys()

    def createService(self, serverName, serviceName, callback):
       """ Creates and registers a service in the ServiceMgr to handle
       queries of data obtained in the data form """
       service = self.world.serviceMgr.createFromTemplate( serviceName )
       service.setServerName(serverName)
       service.setServiceImp( self.getUserData )
       # register service
       self.world.serviceMgr.registerService ( service )

