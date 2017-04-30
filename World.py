# python imports
import os
import sys
import time

import external.yaml as yaml
# utility to load options from file (panda3d config files) or strings
from pandac.PandaModules import *

# Panda Engine Options
# "undecorated 1"
options = [ "win-size 1280 800",
            "win-fixed-size #f",
            "fullscreen #f",
            "sync-video 1",
            "multisamples 4",
            "audio-library-name p3openal_audio",
            "cursor-hidden #f",
            "show-frame-rate-meter #f",
            "undecorated 0"]

for o in options: loadPrcFileData('', o)

# basic finite state machine
from Utils.FiniteStateMachine import *

# TODO: REMOVE THIS
# In YamlTools I have a few functions that massage the YAML
# files so I can use them in the pyqtgraph for the property
# editor
from Utils.YamlTools import fixTuples

# basic Panda3D imports
from direct.showbase.DirectObject import DirectObject
from direct.gui.OnscreenText import OnscreenText
import direct.directbase.DirectStart

from UI.ContextMenu import ScrolledButtonsList

from panda3d.core import TextNode
from panda3d.core import WindowProperties

# logger class
from Utils.Logger import Logger
# debug class
from Utils.Debug import printOut

# some misc useful functions
from Utils.Utils import *

# simple keyboard class that wraps around Panda messenger
from Keyboard import Keyboard

class World(DirectObject):

    def __init__(self, test_mode, experiment_file = ''):
        """
        create socket and a task to wait for remote commands,
        or start right away an experiment from a file.
        """
        if (os.path.isfile(experiment_file)):
            self.experiment_file = experiment_file
        else:
            printOut("FILE DOES NOT EXIST: %s" % experiment_file, 0)
            self.quit()

        self.testMode = test_mode
        self.watchFiles = {}
        self.coldStart = True
        self.restartSimulation()

        # function called when the window is closed.
        base.exitFunc = self.quit
        # function to watch for file changes
        base.taskMgr.doMethodLater(0.2, self.watchFSTask, "watch file")
        return

    def cleanSimulation(self):
        # clean up everything
        # TODO: delete all nodes that were created (*_hud, ...)
        self.forceFSM('start')
        if getattr(self,'elements',False):
            for e in self.elements.values():
                e.removeElement()
        self.ignoreAll()

    def restartSimulation(self, extraArg = None):
        """This can be called at the beginning, not a real "restart", or after the simulation
        started."""

        if not self.coldStart:
            # this is used to remember and come back to the actual element after reloading!
            if getattr(self,'menu',False):
                if self.menu.getSelected():
                    self.lastActiveElementIdx = self.menu.getSelectedIndex()
                else:
                    self.lastActiveElementIdx = 0
                self.menu.destroy()
        else:
            self.lastActiveElementIdx = 0
            self.coldStart = False

        # reload yaml file
        with open(self.experiment_file) as f:
            self.watchFile(self.experiment_file)
            self.experiment = yaml.load(f)
        try:
            self.cleanSimulation()
            self.initialSetup(self.experiment)
            if self.testMode:
                self.createContextMenuElements()
                self.menu.deselect()
                # either select 'start', or selects the last one selected in the list
                self.menu.select(self.lastActiveElementIdx)
                self.forceFSM(self.menu.getSelected()['text'])
                self.accept('t', self.menu.toggleVisibility)
                self.accept('r', self.restartSimulation)
        except Exception, e:
            printOut("General error whilst loading simulation: " + str(e), 0)

    def createContextMenuElements(self):
        """Menu with all the loaded elements"""
        menu = ScrolledButtonsList(
            parent=None, # attach to this parent node
            frameSize=(.8,1.2), buttonTextColor=(1,1,1,1),
            font=None, itemScale=.045, itemTextScale=1, itemTextZ=0,
            # font=transMtl, itemScale=.05, itemTextScale=1, itemTextZ=0,
            command=self.cmElementClicked, # user defined method, executed when a node get selected,
            # receiving extraArgs (which passed to addItem)
            contextMenu=self.cmElementRightClicked, # user defined method, executed when a node right-clicked,
            # receiving extraArgs (which passed to addItem)
            autoFocus=0, # initial auto view-focus on newly added item
            colorChange=1,
            colorChangeDuration=.7,
            newItemColor=(0,1,0,1),
            rolloverColor=(1,.8,.2,1),
            suppressMouseWheel=1,  # 1 : blocks mouse wheel events from being sent to all other objects.
            #     You can scroll the window by putting mouse cursor
            #     inside the scrollable window.
            # 0 : does not block mouse wheel events from being sent to all other objects.
            #     You can scroll the window by holding down the modifier key
            #     (defined below) while scrolling your wheel.
            modifier='control'  # shift/control/alt
        )

        # make an ordered list of elements to put in the menu...
        # a bit cumbersome, walk through the transitions, in breadth first order,
        # make a list of transitions and at the end (finalList) clean up repeated
        # elements
        self.menu = menu
        finalList = []
        listElements = []
        # start is always!
        listElements.append('start')
        while (listElements):
            top = listElements.pop()
            finalList.append(top)
            trans = self.fsm.transitions[top].values()
            for tl in trans:
                for t in tl:
                    if not t in finalList:
                        listElements.append(t)
        for i,x in enumerate(finalList):
            if x not in finalList[i+1:]:
                self.menu.addItem(x, extraArgs=x)
        menu.select(idx=0)
        self.menu.hide()

    def cmElementClicked(self, item, index=None, button=None):
        self.forceFSM(item)

    def cmElementRightClicked(self, item, index, button):
        return
        #print item,index,button
        #p = PopupMenu(
        #    items=(
        #    ('Test', 'common/images/controller.png', self.testElement,'this'),
        #    0, # separator
        #    ('Reload (r)', 'common/images/reload.png', self.testElement,'this'),
        #    #('do that', 0, (
        #    #    ('submenu 1', 0, lambda:0),
        #    #    ('submenu 2', 0, lambda:0)
        #    #)),
        #    #('disabled option',0,[])
        #    ),
        #    )

    def initialSetup(self, experiment):
        yaml_experiment = fixTuples(experiment)
        # register global values for use by any other part of the simulation
        self.globals = yaml_experiment.get('globals',{})
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
        self.watchFile("config/globalKeys.yaml")
        # tuples are not supported by YAML

        # This class inherits from DirectObject, and Keyboard
        # will get a reference to the messenger from us
        self.keyboard = Keyboard(self)
        # will use a dictionary to hold keys and text objects to
        # display attached to Aspect2D
        self.screenText = {}
        # set very basic keys, and removes any event hook
        printOut("Resetting keys", 3)
        self.resetKeys()

        # do some basic setup common to the whole framework
        self.generalSetup()

        # build FSM of the experiment
        self.fsm = self.setupFSM(yaml_experiment)
        if (not self.fsm.isValid()):
            printOut("Invalid FSM, probably some states failed to build")
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

        fsmTransitions = {}

        # parse transitions from YAML file
        try:
            transitions = exp['transitions']
            printOut("Custom transitions defined for this experiment", 2)
        except KeyError, a:
            printOut("You have to define the transitions in the YAML file", 0)
            self.quit()

        # set of Elements to load when the transitions have been processed.
        toLoad = set(['start','end'])

        allTransitions = [ splitTransitionString(t['trans']) for t in transitions]
        for (fromStates, toStates, events) in allTransitions:
            for event in events:
                for f in fromStates:
                    toLoad.add(f)
                    if f not in fsmTransitions.keys():
                        fsmTransitions[f] = {}
                    fsmTransitions[f][event] = []
                    for to in toStates:
                        # set from,to,event values
                        fsmTransitions[f][event] = fsmTransitions[f][event] + [to]

                    # notify the FSM when the event happens
                    self.accept(event, self.FsmEventHandler, [event])

        # construct the element objects dynamically
        for el in exp['elements']:
            try:
                name = el['name']
                if name not in toLoad:
                    printOut("Ignored element not mentioned in the transitions: " % name, 0)
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

                fname = mod.__file__
                self.watchFile( fname.replace('.pyc','.py') )

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
                sys.quit()
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
            except KeyError, e:
                printOut("Exception building state: " + el['name'], 0)
                print "Key error:" , e
                self.quit()
            except Exception, e:
                printOut("Exception building state: " + el['name'], 0)
                print str(e.__class__)
                print e
                self.quit()
        return FiniteStateMachine(fsmTransitions, self.elements)

    def advanceFSM(self, event):
        """An event occured, move the FSM to the next step."""
        self.fsm.processEvent(event)
        self.createTextKeys()
        if self.fsm.hasDone():
            # the simulation has finished.
            # give some short time to allow END state to enter, change colour, and the exit.
            taskMgr.doMethodLater(1,self.quit, 'end state reached', extraArgs=[])


    def forceFSM(self, state):
        """Force the FSM to a given state, exiting any current state first, and
        then entering the required state. This is used mainly for testing."""
        if getattr(self, 'fsm', None):
            self.fsm.forceState(state)
            self.createTextKeys()


    def FsmEventHandler(self, event):
        """This method is used to capture events triggered by
        any state in the FSM. Panda3D will call this method with the
        event argument"""
        self.advanceFSM(event)


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
        self.watchFile("config/config.yaml")

        # create an object from dictionary to simplify usage
        self.config = objFromDict(configDict)

        # timestamp makes up a participant ID
        self.participantId = time.strftime("%y%m%d_%H%M%S")

        # create general log file for each participant
        genLog = self.config.simulationLog
        if getattr(self,'log',None):
            self.log.stopLog()
        self.log = Logger(self.baseTime, genLog.outfile, genLog.mode)
        #self.log.startLog()
        printOut("==== Application started ====\n", 2)
        self.log.logEvent("==== Application started ====\n")
        self.log.logEvent("date: " + time.ctime() + "\n")
        self.log.logEvent("participant id: %s\n" % self.participantId)
        self.log.logEvent("loading Elements\n")

        self.setupCamera()

        # TODO: decide what to do with the globals idea.
        # dictionary with key values for Elements to communicate.
        # between each other.
        # They can save values here and use them, ideally using
        # writeToGlobals and readFromGlobals in the configuration file.
        # self.globals = {}
        return

    def logEvent(self, message):
        self.log.logEvent(message)

    #=========================================================================================
    #========== INPUT HANDLING IN PANDA ======================================================
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
        oldProps = base.win.getProperties()
        hidden = oldProps.getCursorHidden()
        newProps = WindowProperties()
        newProps.setCursorHidden(not hidden)
        base.win.requestProperties(newProps)

    #=========================================================================================
    #========== CAMERA HANDLING ==============================================================
    #=========================================================================================

    # TODO: Remove this. Example on how to setup camera properties
    def setupPandaCamera(self):
        pass
        """Using the object cam with some basic properties about the
        the camera, setup the Panda camera through the object base
        from panda API"""
        # handy reference
        #cam = self.camera

        # drive mode to position the camera
        # base.useDrive()

        # no mouse interaction
        # fix the camera!

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
        new_wp.setSize(1920,1080)
        #new_wp.setUndecorated(True)
        base.win.requestProperties(new_wp)
        print "Old properties: " + str(old_wp)
        print "New properties: " + str(new_wp)

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
        setattr(self.camera, 'ratio', base.win.getXSize() / float(base.win.getYSize()))
        base.disableMouse()

    def windowEventHandler(self, window=None):
        """Function to handle window resize events"""
        # TODO: decide what to do with this function
        printOut("windowEventHandler called!", 0)
        return
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

    def addNode(self, npath, place='3D'):
        """
        Attach node to "render" or to "aspect2d"
        and adds it to the scenes dictionary
        :rtype : does not return anything
        :param npath: nodepath to attach
        :param place: place where to attach, can be 3d or HUD
        """
        mapNode={'3D':render,'HUD':aspect2d}
        if place.upper() in mapNode.keys():
            npath.reparentTo(mapNode[place.upper()])
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

#    def realignTextKeys(self):
#        """Realign the text keys if the window has been resized"""
#        #printOut("Realign text on window resize",0)
#        for (key, val) in self.screenText.items():
#            val.setX(base.a2dLeft)

    def toggleTextKeys(self):
        """Hides/shows all key texts. Should be consistent about "ALL" """
        for (key, val) in self.screenText.items():
            if val.isHidden():
                val.show()
            else:
                val.hide()

    def toggleVerbose(self):
        messenger.toggleVerbose()

    def quit(self, message = ''):
        try:
            self.log.logEvent("quiting simulation")
            self.log.logEvent("calling ExitState on any active element")
            for e in self.elements.values():
                if e.isActive():
                    e.exitState()

            self.log.logEvent("Simulation finished\n")
            if message: self.log.logEvent(message)
            self.log.stopLog()
        except Exception,e:
            printOut("Error whilst closing!")
            print e
        if not self.testMode:
            time.sleep(1)
            sys.exit(0)

    def watchFile(self, filename):
        self.watchFiles[filename] = os.stat(filename).st_mtime

    def watchFSTask(self,t):
        for f,value in self.watchFiles.items():
            current = os.stat(f).st_mtime
            if current != self.watchFiles[f]:
                print "File changed: %s, reloading. " %f,current
                taskMgr.doMethodLater(0.01,self.restartSimulation, 'reload scene')
                self.watchFiles[f] = current
                break
        return t.again


#    def pollZMQ(self,t):
#        try:
#            msg = self.commands_receiver.recv_string(flags=zmq.NOBLOCK)
#            if len(msg) > 0:
#                # answer back
#                self.commands_receiver.send_string('OK')
#                i = msg.find(' ')
#                # find command, use dictionary to call appropriate function with the rest as a string.
#                self.msgHandlers[msg[:i]](msg[i+1:])
#        except Exception, e:
#            pass
#            # print e
#        t.delayTime = 0.1
#        # printOut('running...' + str(t.time))
#        return t.again



