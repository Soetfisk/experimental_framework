from panda3d.core import *
from direct.showbase import DirectObject

import sys
from Utils.Debug import printOut
from Utils.Utils import *
from Logger import Logger
from collections import OrderedDict
import os.path

import external.yaml as yaml

class Element(object):
    """
    The simulation is based on a Finite State Machine of
    States/Elements, but with the exception that MORE than one
    element can be active at a particular time...I know, sounds
    horrible.
    Each element represents some stimuli/functionality in the experiment,
    for example, one image, a text message, a timer, a game!, a pilot...
    It is a very flat hierarchy, and simplistic design.
    """
    def __init__(self, **kwargs):
        '''
        Element constructor. When the element is constructed is passed the YAML
        configuration that is defined in the experiment file. Those kwargs will be
        added as attributes. It also saves some useful attributes to give access
        to the World, and also to the different scene parts (2d, 3d)
        To allow for basic 2D transformations, each element can be manipulated in
        run-time if the attribute "locked_xform" is defined as false.

        If "locked_xform" is false, the user will be able to interact with the mouse and
        keys <ctrl-1> for translation, <ctrl-2> for rotation, <ctrl-3> for scale
        After the interaction, the tweaks will be saved in a file named after the experiment
        name and the element name as: 'expXY_elName_xform.yaml'.
        If the file exists, it will be overwritten.

        :param kwargs: dict
        :return: None
        '''
        # this changes when the state is activated.
        self.active = False

        # baseTime for the experiment, from the World object.
        self.baseTime = kwargs['world'].baseTime
        # some colours constants to share among all elements
        self.colours = getColors()

        self.mouseListener = DirectObject.DirectObject()

        dictionary = {}
        # configuration can be in the experiment file or in a special file
        # just for this element.
        if 'fname_config' in kwargs:
            try:
                dictionary = yaml.load(open(kwargs['fname_config']))
            except Exception, e:
                print e
                printOut("Fatal error loading config file " + kwargs['fname_config'], 0)
                kwargs['world'].quit()

        # ALL atributes are under "self.config"
        for k, v in kwargs.items():
            # make every argument from the fname_config file an attribute, including a reference
            # to world through self.config.world
            if k in dictionary:
                printOut("Warning, same key found in config file and in experiment file",0)
                if 'dict' in str(type(v)):
                    printOut("I will try to join both dictionaries, but if more keys are found they"
                             "will be overriden",0)
                    for k2 in v:
                        dictionary[k][k2] = v[k2]
                if 'list' in str(type(v)):
                    for e in v:
                        dictionary[k].append(e)
            else:
                dictionary[k] = v

        # make everything in the config file a simple object.
        self.config = objFromDict(dictionary)
        printOut("CONFIG LOADED FOR %s" % self.config.name, 4)

        # all configuration options have been loaded.
        # check if this Element can be moved around in run-time, and
        # check if there is a xform file already in the filesystem.
        #xform_file = None
        #try:
        #    xform_file = open('exp_' + self.config.name + '_xform_yaml')
        #    xform_dict = yaml.load(xform_file)
        #except:
        #    xform_dict = None
        #finally:
        #    if xform_file:
        #        xform_file.close()
        #setattr(self.config,'xform_dict',xform_dict)

        # keep a reference to the original YAML config
        self.yaml_config = dictionary


        # try to set some default values, each Element subclass can define
        # a set of default values that if not present in the config file are
        # set here. To know the names of these values, check the constructor
        # of each Element, the attribute "defaults"
        if getattr(self,"defaults",False):
            for k,v in self.defaults.items():
                if not hasattr(self.config, k):
                    printOut("Using default value for "+self.config.name+": "+k+" : "+str(v),0)
                    setattr(self.config, k, v)


        # add the basic 2D and 3D nodepaths in the scenegraph for this element
        self.sceneNP = NodePath(self.config.name)
        self.sceneNP.hide()
        self.hudNP = NodePath(self.config.name+'_hud')
        # set a special BIN for the hudNP
        self.hudNP.setBin('fixed',5)
        self.hudNP.hide()
        # these are basic nodepaths to attach the specific stuff of this
        # element. (text,graphics,anything else)
        self.config.world.addNode(self.sceneNP, place='3d')
        self.config.world.addNode(self.hudNP, place='HUD')

        # load an additional config file for the element, and leave it
        # available for the subclass to do whatever it wants.
        #c = getattr(self,'config_json',None)
        #if (c is None):

        self.registeredKeys = []

    def getConfigTempate(self):
        return OrderedDict({
            'className': 'className',
            'module': 'moduleName',
            'name': 'uniqueName',
            'timeout': 0.0,
            'keys': [
                {
                 'key': '',
                 'callback': '',
                 'tuple_args': ()
                }
            ]
        })


    def setKeyboard(self, keyboard):
        self.kbd = keyboard

    def log(self, message):
        self.config.world.logEvent(message)

    def setTimeOut(self,time):
        # after 'time' a message 'timeout' will be send to the message manager,
        # and if anyone registered to listen for 'timeout' messages they will
        # react
        taskMgr.doMethodLater(time, self.config.world.advanceFSM, 'timeout', extraArgs=[])


#===============================================================================
    def registerKeys(self):
        """Try to setup some keys to callbacks using the YAML file
        specific for this element, or the keys dictionary key if exists
        in the Element description"""

        # Keys defined in the EXPERIMENT FILE, when the Element is created
        #temp_keys = getattr(self.config,"keys",[])
        #exp_keys = []
        #for k in temp_keys:
        #    exp_keys.append(objFromDict(k))

        # Keys defined in the specific configuration file for this
        # instance of the element
        config_keys = getattr(self.config, "keys", [])

        #keys = exp_keys + config_keys
        keys = config_keys

        printOut("Registering keys for the current element", 4)
        for k in keys:
            comment = getattr(k, 'comment', '')
            # support for references using dot notation only!
            # for example:
            # callback: anotherObject.attribute.method
            tokens = k.callback.split('.')
            prevToken = self
            for t in tokens:
                cb = getattr(prevToken, t, None)
                prevToken = cb

            key = getattr(k, 'key', None)
            # in case is the letter 1,2,3..., or even a number 123
            key = str(key)
            once = getattr(k, 'once', False)
            args = getattr(k, 'tuple_args', [])
            # force args to be a list...
            if not isinstance(args, list):
                args = [args]
            if key is None or cb is None:
                printOut('Error!, key or callback missing in when '
                         'setting up %s' % self.config.name, 0)
                printOut('Ignoring key binding', 0)
                self.config.world.quit()
            # this will give us back a [] even if no 'commas' are found

            for eachKey in key.split(','):
                # this could return false in case the key has already been registered
                # in that case the method registerKey from the kbd will warn about that.
                if self.kbd.registerKey(eachKey, self.config.name, cb, comment, once, args):
                    self.registeredKeys.append(eachKey)
        else:
            printOut("No keys added by element %s" % self.config.name, 1)

    def unregisterKeys(self):
        printOut("De-registering keys for the current element", 4)
        for k in self.registeredKeys:
            if self.kbd.unregKey(k):
                printOut("Unregistered key from %s: %s" % (self.config.name, k), 4)
            else:
                printOut("Unable to unregister key from %s: %s" % (self.config.name, k), 0)
        self.registeredKeys = []

    def needsToSaveData(self):
        return False

    def saveUserData(self):
        return

    def hideElement(self):
        #print "HIDE ELEMENT IN Element.py " + self.config.name
        self.hudNP.hide()
        self.sceneNP.hide()

    def showElement(self):
        self.hudNP.show()
        self.sceneNP.show()

    def sendMessage(self, message):
        # messenger.send(message,[message])
        messenger.send(message)

    def enterState(self):
        """
        This method will be executed when the Finite State Machine
        enters into this state
        """
        # WE CREATE THE logFile HERE BECAUSE AN ELEMENT CAN BE EXECUTED MORE THAN ONCE.
        # THIS IMPLIES THAT THIS AUTOMATIC LOGFILE CANNOT BE USED IN THE CONSTRUCTOR OF THE
        # ELEMENT.
        # create a logfile using the name of the Element, and the logFilePath if defined,
        # otherwise create the logfile in the default 'run' directory
        # If the logFile with the exact same name exists, it means that the same
        # element has been already executed, and it is being repeated.
        # Add a counter to the last part of the name to account for this.

        if getattr(self.config,'log',False):
            logFilePath = getattr(self.config, "logFilePath", 'run')
            fileCounter = 1
            fname = '%s/%s_%s_0.txt' % (logFilePath,self.config.name,self.config.world.participantId)
            # repeat until a filename is found
            while os.path.isfile(fname):
                fname = fname[:fname.rfind('_')+1]+str(fileCounter)+'.txt'
                fileCounter+=1
        else:
            # nolog is special name to disable logging
            fname = 'nolog'
        self.logFile = Logger(self.baseTime, fname, 'w')

        self.logFile.startLog()
        printOut("Entering state %s" % self.config.name, 1)

        # log all global variables before anything into the log file.
        self.logFile.logEvent("Global state:")
        for name,value in self.config.world.globals.items():
            self.logFile.logEvent("%s: %s" % (name, value))

        self.showElement()

        # is there a timeout set for this state ?
        # a timeout automatically sends an event after the time, with the name of the
        # element prepended with the word "timeout_"
        t = getattr(self.config, 'timeout', None)
        if t is not None:
            try:
                t = float(t)
                if t:
                    taskMgr.doMethodLater(t, self.sendMessage,
                    'timeout_'+self.config.name, extraArgs=['timeout_'+self.config.name])
            except:
                printOut("error converting timeout value %s in %s " % (str(t), self.config.name), 0)
                self.config.world.quit()
        #self.config.world.createTextKeys()

        # THIS IS OVER COMPLICATED, FOR NOW ANY ELEMENT CAN READ AND WRITE FROM
        # GLOBALS BY HAND...
        ## globals are variables that are accessible experiment wise.
        ## check if we need to load values from globals! or set them
        ## to the defaults specified in the configuration of the Element
        ## check the experiment!
        #try:
        #    globals = self.yaml_config['readFromGlobals']
        #except KeyError, e:
        #    #print e
        #    globals = None

        #if globals:
        #    for g in globals.keys():
        #        if g in self.config.world.globals:
        #            setattr(self, g, self.config.world.globals[g])
        #        else:
        #            setattr(self, g, globals[g])

        # finally, there is a refsto attribute in the config file, which allows to provide a reference from
        # one Element to another, provided that the target reference exists.
        refs = getattr(self.config, "refsto", [])
        el = None
        for ref in refs:
            if ref in self.config.world.elements:
                el = self.config.world.elements[ref]
                setattr(self,ref, el)
            else:
                printOut("ERROR: Element %s trying to set a reference to non-existent element %s!" %
                         (self.config.name, ref ),0)

        # set clear color if it has been explicitly stated in the config
        c = getattr(self.config,'color_background',None)
        if c:
            base.win.setClearColor(Vec4(*c))

        # lastly, register keys.
        self.registerKeys()

        self.active = True

    def removeElement(self):
        self.sceneNP.detachNode()
        self.hudNP.detachNode()

    def exitState(self):
        """
        This method will be executed when the Finite State Machine
        exits from this state
        """
        self.hideElement()
        taskMgr.remove('timeout_'+self.config.name)
        self.unregisterKeys()
        printOut("Leaving state %s" % self.config.name,2)
#        self.config.world.createTextKeys()
        self.active = False

        # DO NOT USE readFromGlobals or writeFromGlobals in config file.
        # save globals if we have them.
        #try:
        #    globals = self.yaml_config['writeToGlobals']
        #except KeyError, e:
        #    #print e
        #    globals = None
        #if globals:
        #    for g in globals.keys():
        #        # read value or assign default from config!
        #        newValue = getattr (self, g, globals[g])
        #        self.config.world.globals[g] = newValue

        if self.logFile:
            self.logFile.stopLog()

    def isActive(self):
        return self.active

#    def createService(self, serverName, serviceName, callback):
#       """ Creates and registers a service in the ServiceMgr to handle
#       queries of data obtained in the data form """
#       service = self.config.world.serviceMgr.createFromTemplate( serviceName )
#       service.setServerName(serverName)
#       service.setServiceImp( self.getUserData )
#       # register service
#       self.config.world.serviceMgr.registerService ( service )
