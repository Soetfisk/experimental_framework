# panda imports

# utility to load options from file or strings
from pandac.PandaModules import loadPrcFileData
# pandaConfig defines a list of options to setup Panda3D
import pandaConfig
for o in pandaConfig.options:
    loadPrcFileData('', o)

from Utils.Utils import getColors

# rest of config files are stored in JSON format
try:
    import json
except ImportError:
    import simplejson as json
import yaml

from Utils.FiniteStateMachine import *

# basic Panda3D imports
import direct.directbase.DirectStart
from direct.showbase.DirectObject import DirectObject
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode
from panda3d.core import WindowProperties
from panda3d.core import Vec4

# for finite state machines
from direct.fsm.FSM import FSM

# python imports
from math import sin, cos, pi, ceil
import sys, os
import time
from time import ctime

# python threading for Eye-tracker
from Tracker import Tracker

# own classes imports
# logger class
from Logger import Logger
# debug class
from Utils.Debug import printOut
# services management class
# from ServiceMgr import *

# some misc useful functions
from Utils.Utils import *

# simple keyboard class that wraps around Panda messenger
from Keyboard import Keyboard

class World(DirectObject):
    """Main class with all the setup and interaction configuration"""

    def __init__(self, experiment):
        """
        Constructor for World class, the configuration is read
        from the config files and the experiment file
        """
        # first timestamp since the whole application started
        self.baseTime=time.time()

        # Dictionary to store the elements (nodes) that will be part of
        # an experimentation, will construct a Finite State Machine 
        # with them
        self.elements={}

        # list to hold events from the FSM
        self.eventQueue = []

        # get global keys configuration
        # this keys are always available application wide
        # self.json_keys = json.load(open("config/globalKeys.json"))
        self.keyConfig = yaml.load(open("config/globalKeys.yaml"))

        # This class inherits from DirectObject, and Keyboard
        # will get a reference to the messenger from us
        self.keyboard = Keyboard(self)
        # will use a dictionary to hold keys and text objects to
        # display attached to Aspect2D
        self.screenText = {}
        # set very basic keys, and removes any event hook
        printOut("Reseting keys", 3)
        self.resetKeys()

        # do some basic setup common to the whole framework
        self.generalSetup()

        # for the Eye-tracker
        self.tracker = Tracker()

        # build FSM of the experiment
        self.fsm = self.setupFSM(experiment)

        # enter into the START state
        self.elements['start'].enterState()



#=========================================================================================
#========== FSM HANDLING =================================================================
#=========================================================================================

    # splits a transition string into a tuple of strings (fromState,toState,event)
    def splitTransitionString(self, transition):
        try:
            if ':' in transition:
                evt = transition.split(':')[1].strip()
            else:
                evt = 'auto'
            # parse the transition "fromA @ toB : whenEvt"
            fromState, toState = transition.split('@')
            fromState = fromState.strip()
            toState = toState.split(':')[0].strip()
            return (fromState,toState,evt)
        except:
            printOut("Malformed transition: "+ transition, 0)
            self.quit()

    def setupFSM(self, experiment):
        """
            Constructs a FSM where each node is one element in the
            experiment. Based on events, the FSM can be non-deterministic,
            and it can also allow for SIMULTANEOUS transitions, meaninng that
            the FSM will have concurrent states executing.
            See experiments/exp_XXX.yaml, where transitions are defined as
            A@B:event to specify a transition from A to B when event event
            has happened. If no event is specified an "auto" event is created.
        """

        # experiment configuration
        # dictionary form
        printOut("Loading yaml experiment: %s" %experiment,2)
        #if ('json' in experiment):
        #    exp = json.load(open(experiment))
        if ('yaml' in experiment):
            exp = yaml.load(open(experiment))

        fsmTransitions = {}

        # parse transitions from YAML file
        try:
            transitions = exp['transitions']
            printOut("Custom transitions defined for this experiment",2)
        except KeyError, a:
            printOut("You have to define the transitions in the YAML file",0)
            self.quit()



        # list of Elements to load when the transitions have been processed.
        toLoad = []
        # stack to perform a tree traversal, HAS to have 'start' transition
        transitionsStack = ['start']
        # while the stack is not empty
        while (transitionsStack):
            fromNode = transitionsStack.pop()
            if (fromNode in toLoad):
                continue
            else:
                toLoad.append(fromNode)
                fsmTransitions[fromNode] = {}

            for t in transitions:
                (fromState,toState,evt) = self.splitTransitionString(t['trans'])
                if (fromState == fromNode):
                    # add child to stack
                    transitionsStack.append(toState)
                    fsmTransitions[fromState][evt] = fsmTransitions[fromState].get(evt,[]) + [toState]
                    # notify the FSM when the event happens
                    self.accept(evt, self.FsmEventHandler)


        # for t in transitions:
        #
        #     (fromState,toState,evt) = self.splitTransitionString(t['trans'])
        #
        #     # is this the first time this element is seen in the FSM
        #     if fromState not in fsmTransitions.keys():
        #         fsmTransitions[fromState] = {}
        #
        #     if evt not in fsmTransitions[fromState].keys():
        #         # this is a list, because we want to support concurrent
        #         # state changes.
        #         fsmTransitions[fromState][evt] = []
        #
        #     # this is a list, because we want to support concurrent
        #     fsmTransitions[fromState][evt] += [toState]
        #     # accept a message with the event evt to jump to end
        #     self.accept(evt, self.FsmEventHandler)
        #     #if evt is not 'auto':
        #         # the event handler will jump to the right state in the FSM

        for el in exp['elements']:
            try:
                name = el['name']
                if name not in toLoad:
                    continue

                className = el['className']
                module = el.get('module',className)
                if 'module' in el.keys():
                    module = el['module']
                else:
                    module = className

                # load the Python Module for this element
                mod = __import__('Elements.'+module+'.'+className,
                                 globals(), locals(), [className], -1)
                # get a reference to the class based on className
                myElementClass = getattr(mod, className)
                # build dictionary with ALL the arguments for this element
                # INCLUDING a reference to SELF (World) object to access Panda3d.
                # Default arguments:
                kwargs = dict(el.items() + {"world": self}.items())
                # create an instance of this Class
                printOut("Building from class %s with arguments: " % className, 2)
                printOut(str(kwargs), 2)
                state_obj = myElementClass(**kwargs)
                printOut("Instance of class "+ className + " created", 2)

                # pass keyboard reference so it can register its own keyboard
                # events
                state_obj.setKeyboard(self.keyboard)

                # dinamically add the enter/exit methods on the FSM
                # for this element. These methods "enterState", "exitState"
                # have to exist in the class we are constructing.
                # we use 'name' so each element is unique even if the
                # class is re-used.
                #
                #setattr(fsm, 'enter'+name, state_obj.enterState)
                #setattr(fsm, 'exit'+name, state_obj.exitState)
                # keep a reference to the element by its unique NAME

                self.elements[name] = state_obj

                # if no CUSTOM transitions were defined
                # add automatic transitions as a simple sequence from the file
                #if len(transitions) == 0:
                #    fsmTransitions[next] = {'auto': name}
                #    next = name
                #    # if last, add exit
                #    if len(exp['elements']) == n+1:
                #        fsmTransitions[next] = {'auto': 'end'}

            except ImportError, i:
                printOut("Error importing module, missing file or wrong className",0)
                print className
                print i
                sys.exit()
            except ValueError, v:
                # if the name cannot be split in two pieces by the dot
                #printOut("Missing or extra dots in the name of :" + s,0)
                print v
                sys.exit()
            except AttributeError, e:
                printOut("Attribute error when building " + el['name'],0)
                printOut("Most likely there is a mismatch between the code and the config file",0)
                printOut("%s" % e, 0)
                self.quit()
            except Exception, e:
                printOut("Exception building state: " + el['name'], 0)
                print str(e.__class__)
                print e
                self.quit()
        return FiniteStateMachine(fsmTransitions, self.elements)

    def advanceFSM(self, event):
        self.fsm.processEvent(event)
        self.createTextKeys()
        if self.fsm.hasDone():
            # the simulation has finished.
            self.quit()

    def advanceFSM2(self):
        """
        In order to advance to the next state, we check the state we are currently,
        and the queue of events in case the FSM is not deterministic. If no event
        matching a valid transition is found, then the default transition is used.
        Events are UNIQUE for a given element instance, so 2 elements cannot generate
        the same event!.
        """
        # shortname
        trans = self.fsm.getTransitions()

        # current node
        curr = self.fsm.state
        if (curr == 'Off'):
            printOut("Starting the FSM..., moving to first node",2)
            curr = 'start'

        self.log.logEvent("Leaving state %s\n"%curr,time.time())

        if (curr != 'start' and curr!='Off'):
            element = self.elements[curr]
            if (element.needsToSaveData()):
                element.saveUserData()
                t = time.time()
                self.log.logEvent("User data: %s\n"%element.name,t)
                d = element.getUserData()
                for k,v in d.items():
                    self.log.logEvent("%s:%s\n"%(k,str(v)), t)

        # retrieve possible events at this node
        events = trans[curr].keys()
        printOut("advancing FSM:",2)
        printOut("current state: %s" % curr, 2)
        printOut("possible events: %s " % str(events),2)
        printOut("event queue %s" % str(self.eventQueue),2)
        # go through each event in the queue
        for e in self.eventQueue:
            # event matching ?
            if e in events:
                # remove THE FIRST occurence, set new state for transition
                del self.eventQueue[self.eventQueue.index(e)]
                nextState = trans[curr][e]
                break # so the else: below does not execute

        # if we looped through all the events, and found no matching
        # transition, then do the auto transition
        else:
            nextState = trans[curr]['auto']

        if nextState == 'end':
            printOut("Finished FSM, next state is 'end'",2)
            printOut("Quitting and closing files",2)
            # no more states!
            self.fsm.request("Off")
            self.log.logEvent("Entering state Off\n",time.time())
            self.quit()
        else:
            # nextState=self.elementsNames[pos+1]
            printOut("Entering STATE %s" % nextState, 2)
            self.log.logEvent("Entering state %s\n"%nextState,time.time())
            self.fsm.request(nextState)

    def FsmEventHandler(self, event):
        """This method is used to capture events triggered by
        any state in the FSM"""
        self.advanceFSM(event)
        # at this stage, we can't really do anything, an event has
        # to be queued because the FSM could have a loop farther away
        # from this point in the FSM therefore this event cannot be
        # handled right now...It will be handled in the advanceFSM method
        #printOut("Received event at FsmEventHandler: %s"%event,2)
        #self.eventQueue.append(event)


#=========================================================================================
#========== SETUP ========================================================================
#=========================================================================================

    def generalSetup(self):
        """
        common functionality and basic setup used by all the states/elements
        """
        # general configuration lies in this JSON file
        # such as camera settings, etc.
        configDict = yaml.load(open("config/config.yaml"))

        # create an object from dictionary to simplify usage
        self.config = objFromDict(configDict)

        # file describing all the service templates available
        # self.services = objFromDict(json.load(open('config/services.json')))
        # create Service manager
        # self.serviceMgr = ServiceMgr(self.services)
        # printOut("Service Manager created",1)

        # create general log file
        genLog = self.config.simulationLog
        self.log = Logger(genLog.outfile,genLog.mode)
        self.log.startLog(self.baseTime)
        t = time.time()
        printOut("==== Application started ====\n", 2)
        self.log.logEvent("==== Application started ====\n", t)
        self.log.logEvent("date: " +  ctime() + "\n", t)
        self.log.logEvent("loading Elements\n", t)

        self.setupCamera()
        self.setupPandaCamera()

        base.win.setClearColor(getColors()['dark_grey'])

        # dictionary with key values for Elements to communicate.
        # between each other.
        # They can save values here and use them, ideally using
        # writeToGlobals and readFromGlobals in the configuration file.
        self.globals = {}
        return

    def logEvent(self, message):
        t = time.time()
        self.log.logEvent(message, t)

#=========================================================================================
#========== INPUT HANDLING ===============================================================
#=========================================================================================

    def hideMouseCursor(self):
        """Hides mouse cursor in Panda3D"""
        props = WindowProperties()
        props.setCursorHidden(True)
        base.win.requestProperties(props)

    def showMouseCursor(self):
        """Hides mouse cursor in Panda3D"""
        props = WindowProperties()
        props.setCursorHidden(False)
        base.win.requestProperties(props)

    def toggleMouseCursor(self):
        """shows or hides mouse cursor"""
        self.cursorHidden = not self.cursorHidden
        props = WindowProperties()
        props.setCursorHidden(self.cursorHidden)
        base.win.requestProperties(props)
        return

#=========================================================================================
#========== CAMERA HANDLING ==============================================================
#=========================================================================================

    def setupPandaCamera(self):
        """Using the object cam with some basic properties about the
        the camera, setup the Panda camera through the object base
        from panda API"""
        # handy reference
        #cam = self.camera

        # drive mode to position the camera
        # base.useDrive()

        # no mouse interaction
        # fix the camera!
        base.disableMouse()

        # set Panda basic camera
        #base.camera.setPos(cam.pos[0], cam.pos[1], cam.pos[2])
        #base.camera.lookAt(cam.lookAt[0], cam.lookAt[1], cam.lookAt[2])
        #base.camLens.setFov(cam.fov)
        #base.camLens.setNear(10)# equiv to:
        #base.cam.node().getLens().setNear()
        #base.camLens.setFar(200)

        #wp = WindowProperties()
        #wp.setFullscreen(True)
        #wp.setSize(cam.screenWidth, cam.screenHeight)
        #base.win.requestProperties(wp)
        #print "Size: %d x %d\n" %(wp.getXSize(),wp.getYSize())
        # return this dictionary

        #render.explore()

    def setupCamera(self):
        """
        Attributes:
        screenWidth, screenHeight
        pos, lookAt, fov, ratio
        """
        # setup the camera based purely on the JSON configuration

        self.camera = self.config.cameraConfig

        # ==========================================================
        # override screenWidth,screenHeight
        # from pandaConfig.py if they have been defined
        for o in pandaConfig.options:
            if 'win-size' in o:
                # "win-size 1280 800"
                w, h = o.split(' ')[1:]
                printOut("Saving window config: %s %s" % (w, h), 4)
                self.config.cameraConfig.screenWidth = int(w)
                self.config.cameraConfig.screenHeight = int(h)
        # ===========================================================

        setattr(self.camera, 'ratio', self.camera.screenWidth / float(self.camera.screenHeight))
        # fovRads = (self.camera.fov * pi / 180.0)

        # make a triangle rectangle, from camera pos to the plane
        # where the parachutes fall. The hiphotenuse is the length of the
        # line from the camera to the top of this plane
        # hip = camera.parDistCam / cos(fovRads / 2)

        # (sine(fov/2) * length) is the minX
        # setattr(camera, 'minX', -hip*sin(fovRads/2.0) )

        # the heigth is simply derived from the aspect ratio
        # of the screen, should match assuming a perspective frustrum
        #setattr( camera, 'minZ', -hip*sin(fovRads/2.0) )
        # setattr(camera, 'minZ', camera.ratio-hip*sin(fovRads/2.0))

    def windowEventHandler(self, window=None):
        """Function to handle window resize events"""
        #const_wp = window.getProperties()
        #w = const_wp.getXSize()
        #h = const_wp.getYSize()

        #wp = WindowProperties()
        #wp.setSize(w, int(w/h))
        #base.win.requestProperties(wp)
        # trying to keep the same size in objects regardless of the size of the window
        # or the size of the screen.
        #base.camLens.setFov(w * 65.0 / 1280.0)
        #taskMgr.doMethodLater(0.1, self.realignTextKeys, 'realign text', extraArgs=[])

    def addNode(self, npath, place='3d'):
        """
        Attach node to "render" or to "aspect2d"
        and adds it to the scenes dictionary
        :rtype : does not return anything
        :param npath: nodepath to attach
        :param place: place where to attach, can be 3d or HUD
        """
        parent = render
        if place == 'HUD':
            parent = aspect2d
        npath.reparentTo(parent)

#=========================================================================================
#========== KEYBOARD - KEYS HANDLING =====================================================
#=========================================================================================

    def stopKeyboard(self):
        self.keyboard.clearKeys()

    def resetKeys(self):
        """clears all key bindings and links the global keys specified
        in config/globalKeys.json"""
        # shorter name
        k = self.keyboard
        # clean up events (ALL EVENTS) on World
        k.clearKeys()
        # add a basic key to display/toggle help

        if not k.registerKey('control-h', 'World', self.toggleTextKeys, "Shows/Hides this help"):
            self.fatal("Error registering key h for World, check you are not using this key"
                  "for any purpose as it is reserved")

        for key_record in self.keyConfig['global_keys']:
            try:
                # try and see if the callback exists
                method = getattr(self, key_record['callback'])
                args = []
                comment = ""
                if key_record.has_key('args'):
                    args = key_record['args']
                if key_record.has_key('comment'):
                    comment = key_record['comment']
                if not k.registerKey(key_record['key'], 'World', method, comment, False, args):
                    self.fatal("Error registering key h for World, check you "
                               "are not using this key for any purpose as it "
                               "is reserved")

            except Exception, e:
                print e
                printOut("Error, no method found for callback: %s" % key_record['callback'], 0)
                printOut("Ignoring this key binding", 0)

        self.cursorHidden=False
        # called when resizing the Panda window.
        self.accept('window-event', self.windowEventHandler)
        self.createTextKeys()
        return

    def fatal(self, message):
        printOut(message,0)
        self.quit()

    def createTextKeys(self):
        """Shows/hides keyboard bindings"""

        # destroy previous text nodes
        for val in self.screenText.values():
            val.destroy()
        self.screenText = {}

        # create new text nodes
        keys = self.keyboard.getKeys()
        for (pos,k) in enumerate(keys):
            text = self.keyboard.getTextKey(k)
            self.screenText[k] = OnscreenText(text,pos=(base.a2dLeft,.95-0.06*pos),fg=(1,1,0,1),
                    align=TextNode.ALeft,scale=.05)
            self.screenText[k].hide()

    def realignTextKeys(self):
        """Realign the text keys if the window has been resized"""
        #printOut("Realign text on window resize",0)
        for (key,val) in self.screenText.items():
            val.setX(base.a2dLeft)

    def toggleTextKeys(self):
        """Hides/shows all key texts. Should be consistent about "ALL" """
        for (key,val) in self.screenText.items():
            if val.isHidden():
                val.show()
            else:
                val.hide()


    def toggleVerbose(self):
        messenger.toggleVerbose()

    def quit(self):
        self.log.logEvent("Simulation finished\n",time.time())
        self.log.stopLog()
        self.tracker.stopTrack()
        sys.exit()

#    def _quit(self):
        # this will implicitly quit, but each state will have
        # the opportunity to clear out the logs
        #self.fsm.request("Off")
#        self.quit()
        #while(True):
        #    self.advanceFSM()


