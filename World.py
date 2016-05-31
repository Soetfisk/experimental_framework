# python imports
import sys
import time
from time import ctime


# config files are in yaml
import yaml

# utility to load options from file or strings
from pandac.PandaModules import loadPrcFileData
# pandaConfig defines a list of options to setup Panda3D

import pandaConfig
for o in pandaConfig.options:
    loadPrcFileData('', o)

from Utils.FiniteStateMachine import *
from Utils.YamlTools import fixTuples

# basic Panda3D imports
from direct.showbase.DirectObject import DirectObject
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode
from panda3d.core import WindowProperties
import direct.directbase.DirectStart

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
    def __init__(self, experiment):
        """
        empty constructor
        just calls initialSetup(experiment)
        """
        if experiment:
            self.setNewExperiment(experiment)

    def testOne(self):
        test = {
            'className':'ScreenText',
            'name':'singleScreenText',
            'plain_text':'PilotData/finalText.txt'
        }
        self.cleanSimulation()
        self.initialSetup(test)

    def cleanSimulation(self):
        # clean up everything!
        if getattr(self,'elements',False):
            for e in self.elements.values():
                e.removeElement()
        self.ignoreAll()

    def restartSimulation(self):
        self.cleanSimulation()
        self.initialSetup()

    def setNewExperiment(self, fileName):
        self.experiment = fileName
        self.restartSimulation()

    # singleConfig can be a single module/element description, in dictionary form.
    def initialSetup(self, singleConfig = ''):
        if singleConfig:
            experiment = yaml.load(open("experiments/exp_empty.yaml"))
            experiment['elements'].append(singleConfig)
            for t in experiment['transitions']:
                t['trans'] = t['trans'].replace('dummy',singleConfig['name'])
        else:
            experiment = yaml.load(open(self.experiment))

        experiment = fixTuples(experiment)

        # register global values for use by any other part of the simulation
        self.globals = experiment['globals']

        print self.globals
        # first timestamp since the whole application started
        self.baseTime = time.time()

        # Dictionary to store the elements (nodes) that will be part of
        # an experimentation, will construct a Finite State Machine
        # with them
        self.elements = {}

        # list to hold events from the FSM
        self.eventQueue = []

        # get global keys configuration, always available application wide
        self.keyConfig = yaml.load(open("config/globalKeys.yaml"))
        # tuples are not supported by YAML

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

        # build FSM of the experiment
        self.fsm = self.setupFSM(experiment)
        if (not self.fsm.isValid()):
            printOut("Invalid FSM")
            self.quit()

        # enter into the START state
        self.elements['start'].enterState()

    def setupFSM(self, exp):
        """
            Constructs a FSM where each node is one element in the
            experiment. Based on events, the FSM can be non-deterministic,
            and it can also allow for SIMULTANEOUS transitions, meaninng that
            the FSM will have concurrent states executing.
            See experiments/exp_XXX.yaml, where transitions are defined as
            A@B:event to specify a transition from A to B when event event
            has happened. If no event is specified an "auto" event is created.
        """

        # experiment configuration, in YAML format
        #printOut("Loading yaml experiment: %s" % experiment, 2)
        #if 'yaml' in experiment:
        #    exp = yaml.load(open(experiment))

        fsmTransitions = {}

        # parse transitions from YAML file
        try:
            transitions = exp['transitions']
            printOut("Custom transitions defined for this experiment", 2)
        except KeyError, a:
            printOut("You have to define the transitions in the YAML file", 0)
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
                (fromState, toState, evt) = splitTransitionString(t['trans'])
                if (fromState == fromNode):
                    # add child to stack
                    transitionsStack.append(toState)
                    for event in evt.split(','):
                        fsmTransitions[fromState][event] = fsmTransitions[fromState].get(event, []) + [toState]
                        # notify the FSM when the event happens
                        self.accept(event, self.FsmEventHandler, [event])

        for el in exp['elements']:
            try:
                name = el['name']
                if name not in toLoad:
                    continue

                className = el['className']
                # get module name, or default to className
                module = el.get('module', className)
                # reload or import the Python Module for this element
                try:
                    reload(sys.modules['Elements.'+module])
                    reload(sys.modules['Elements.'+module+'.'+className])
                    mod = __import__('Elements.'+module+'.'+className,
                                    globals(), locals(), [className], -1)
                except Exception,e:
                    print e
                    mod = __import__('Elements.' + module + '.' + className,
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
                printOut("Instance of class " + className + " created", 2)

                # pass keyboard reference so it can register its own keyboard
                # events
                state_obj.setKeyboard(self.keyboard)
                self.elements[name] = state_obj

            except ImportError, i:
                printOut("Error importing module, missing file or wrong className", 0)
                print className
                print i
                sys.exit()
            except ValueError, v:
                # if the name cannot be split in two pieces by the dot
                #printOut("Missing or extra dots in the name of :" + s,0)
                print v
                self.quit()
            except AttributeError, e:
                printOut("Attribute error when building " + el['name'], 0)
                printOut("Most likely there is a mismatch between the code and the config file", 0)
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
        # general configuration lies in this YAML file
        # such as camera settings, etc.
        configDict = yaml.load(open("config/config.yaml"))

        # create an object from dictionary to simplify usage
        self.config = objFromDict(configDict)

        self.participantId = time.strftime("%y%m%d_%H%M%S")

        # create general log file
        genLog = self.config.simulationLog
        self.log = Logger(self.baseTime, genLog.outfile, genLog.mode)
        self.log.startLog()
        printOut("==== Application started ====\n", 2)
        self.log.logEvent("==== Application started ====\n")
        self.log.logEvent("date: " + ctime() + "\n")
        self.log.logEvent("participant id: %s\n" % self.participantId)
        self.log.logEvent("loading Elements\n")

        self.setupCamera()
        self.setupPandaCamera()

        base.win.setClearColor(getColors()['dark_grey'])

        # dictionary with key values for Elements to communicate.
        # between each other.
        # They can save values here and use them, ideally using
        # writeToGlobals and readFromGlobals in the configuration file.
        # self.globals = {}
        return

    def logEvent(self, message):
        self.log.logEvent(message)

    #=========================================================================================
    #========== INPUT HANDLING ===============================================================
    #=========================================================================================

#    def hideMouseCursor(self):
#        """Hides mouse cursor in Panda3D"""
#        props = WindowProperties()
#        props.setCursorHidden(True)
#        base.win.requestProperties(props)

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

    def toggleFullScreen(self):
        #const WindowProperties oldp = window->get_graphics_window()->get_properties();
        #WindowProperties newp;
        #if (oldp.get_fullscreen())
        #    newp.set_fullscreen(false);
        #else
        #    newp.set_fullscreen(true);
        #window->get_graphics_window()->request_properties(newp);
        new_wp = WindowProperties()
        old_wp = base.win.getProperties()
        if old_wp.getFullscreen():
            new_wp.setFullscreen(False)
        else:
            new_wp.setFullscreen(True)
        base.win.requestProperties(new_wp)


    def getCamera(self):
        return self.camera

    def setupCamera(self):
        """
        Attributes:
        screenWidth, screenHeight
        pos, lookAt, fov, ratio
        """
        # setup the camera based purely on the YAML configuration

        self.camera = self.config.cameraConfig

        # ==========================================================
        # override screenWidth,screenHeight
        # from pandaConfig.py if they have been defined
        for o in pandaConfig.options:
            if 'win-size' in o:
                # "win-size 1280 800"
                w, h = o.split(' ')[1:]
                printOut("Saving window config: %s %s" % (w, h), 4)
                self.camera.screenWidth = int(w)
                self.camera.screenHeight = int(h)
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
        pass

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

        mapNode={'3D':render,'HUD':aspect2d}
        if place.upper() in mapNode.keys():
            npath.reparentTo(mapNode[place])
        else:
            printOut("ERROR: trying to add a node to an invalid place: %s"%place,0)

    #=========================================================================================
    #========== KEYBOARD - KEYS HANDLING =====================================================
    #=========================================================================================

    def resetKeys(self):
        """clears all key bindings and links the global keys specified in config/globalKeys.yaml"""
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
                if key_record.has_key('tuple_args'):
                    args = key_record['tuple_args']
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

        self.cursorHidden = False
        # called when resizing the Panda window.
        self.accept('window-event', self.windowEventHandler)
        self.createTextKeys()
        return

    def fatal(self, message):
        printOut(message, 0)
        self.quit()

    def createTextKeys(self):
        """Shows/hides keyboard bindings"""

        # destroy previous text nodes
        for val in self.screenText.values():
            val.destroy()
        self.screenText = {}

        # create new text nodes
        keys = self.keyboard.getKeys()
        for (pos, k) in enumerate(keys):
            text = self.keyboard.getTextKey(k)
            self.screenText[k] = OnscreenText(text, pos=(base.a2dLeft, .95 - 0.06 * pos), fg=(1, 1, 0, 1),
                                              align=TextNode.ALeft, scale=.05)
            self.screenText[k].hide()

    def realignTextKeys(self):
        """Realign the text keys if the window has been resized"""
        #printOut("Realign text on window resize",0)
        for (key, val) in self.screenText.items():
            val.setX(base.a2dLeft)

    def toggleTextKeys(self):
        """Hides/shows all key texts. Should be consistent about "ALL" """
        for (key, val) in self.screenText.items():
            if val.isHidden():
                val.show()
            else:
                val.hide()


    def toggleVerbose(self):
        messenger.toggleVerbose()

    def quit(self):
        try:
            self.log.logEvent("quiting simulation")
            self.log.logEvent("calling ExitState on any active element")
            for e in self.elements.values():
                if e.isActive():
                    e.exitState()

            self.log.logEvent("Simulation finished\n")
            self.log.stopLog()
        except Exception,e:
            printOut("Error whilst closing!")
            print e
        finally:
            # sleep 1 second of grace
            time.sleep(1)
            sys.exit()
