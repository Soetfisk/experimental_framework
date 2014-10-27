from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import *
from panda3d.core import *

from Element import *

import sys
from Utils.Utils import splitString
from Utils.Debug import printOut
from Service import *

class DataForm(Element):
    """Class to display a form on screen and
    capture user data. The form is constructed
    dynamically from a TEXTUAL description.
    The class provides a service, to serve the
    answers as a dictionary to anyone that
    posseses a hook"""
    def __init__(self, **kwargs):
        """
        Class constructor
        """
        # build basic element
        super(DataForm, self).__init__(**kwargs)
        printOut("Element for DataForm constructed", 1)
        # the config is loaded by Element automatically into self.config
        self.setupGUI()
        printOut("DataForm GUI constructed", 1)
        # create a simple service that can be queried in different ways,
        # pass (serverName, serviceName, callback)
        # TODO
        # self.createService('userdata0','UserData', self.getUserData)
        # printOut("Service userdata0 for dataform created",1)

        # in this dictionary we will keep the inputs from the form.
        self.userInput = {}

    def needsToSaveData(self):
        return True
    def saveUserData(self):
        self.saveInputs()

    def getUserData(self, input=[]):
        """Service published by this element,
        returns a dictionary with the values read
        from the GUI. If the Element hasnt been activated
        yet, returns None"""
        return self.userInput

    def setupGUI(self):
        """ Builds the GUI based on the JSON description """
        # stores the GUI labels
        self.guiLabels=[]
        # stores ALL the widgets in order of focus (even if they cannot get focus)
        self.focusOrder = []
        # DirectFrame that will contain the GUI
        self.myFrame = None

        # frame to hold the form (left, right, bottom, top)
        # Find out window dimensions
        ratio = self.config.world.camera.ratio
        frameSize = (-ratio,ratio,-1.0,1.0)
        # centered
        pos = (0,1.0,0)
        # background colour
        colour = self.colours['dark_grey']
        # guiLabels colour
        labelColour = self.config.settings.labelcolour
        # global scale of the frame
        scale    = self.config.settings.scale
        # canvas with scrolling capabilities
        self.myFrame = DirectScrolledFrame ( canvasSize=( frameSize[0], frameSize[1], 50*frameSize[2],
                              frameSize[3]), frameColor = colour, frameSize  = frameSize, pos = pos )
        # reparent the frame to the hudNP so we can hide it easily
        self.myFrame.reparentTo(self.hudNP)

        # read title or set to a default value
        title = getattr(self.config.settings,"title", "Introduce your data")

        # title of the frame
        label = OnscreenText( text = title,
                              pos = (0, frameSize[3] - scale*1.5 ),
                              scale = scale * 1.5, fg=labelColour, align=TextNode.ACenter,
                              mayChange=1 )
        label.reparentTo(self.myFrame.getCanvas())

        # max length in characters of a label (will split in lines if bigger)
        maxLabel = self.config.settings.maxlabel
        maxwidth=0
        # position of the first label and widget
        lastYpos = frameSize[3] - scale*4

        for count,i in enumerate(self.config.input):

            # create label in several lines up to 15 chars
            # split the string in several lines up to 15 chars
            printOut("Creating element: %s" % i.label, 2)
            splitWords = splitString( str(i.label) + ':', maxLabel  )
            for s in splitWords:
                lastYpos -= 1.1*scale
                label2 = OnscreenText(text = s, pos = (0,lastYpos),scale = scale, fg=labelColour,
                                     align=TextNode.ARight, mayChange=1)
                bounds = label2.getTightBounds()
                width = abs(bounds[0][0]-bounds[1][1])
                if (width > maxwidth): maxwidth=width
                label2.reparentTo(self.myFrame.getCanvas())
                self.guiLabels.append(label2)


            # for each label, create a widget matching the JSOSN
            widgetYpos = lastYpos
            if ( str(i.type) == 'TextEntry' ):
                widget = DirectEntry(text = "" , scale=scale,
                        cursorKeys=1,
                        command=self.setText, extraArgs=[],
                        pos=(0,1,widgetYpos), numLines = 1, focus=0)
            elif ( str(i.type) == 'Option' ):
                widget = DirectOptionMenu( text="options", scale=1.10*scale, items=i.values,
                        popupMarkerBorder=(1,0),
                        initialitem=0, command=self.optionMenu, extraArgs=[],
                        pos=(0,1,widgetYpos))
            elif ( str(i.type) == 'TickBox' ):
                widget = DirectCheckButton( text="", scale=scale,
                         command=self.tickBoxClicked, extraArgs=[],
                         pos=(scale,1,widgetYpos+scale/3.0))
                widget.clicked=False

            # order of creation
            widget['extraArgs'] = [widget]
            self.focusOrder.append(widget)
            widget.reparentTo(self.myFrame.getCanvas())
            # distance to next widget
            lastYpos -= scale

        # adjust X position based on the largest word
        for l in self.guiLabels:
            #adjust X position
            l.setX( frameSize[0] + maxwidth + 0.05 )
        for w in self.focusOrder:
            w.setX( w['pos'][0] + frameSize[0] + maxwidth + 0.10 )

        # add a button to save the values and advance from the FORM (exit this state)
        lastYpos -= 2*scale
        pad0 = (0.9,0.7)
        #self.saveButton = DirectButton( parent = self.myFrame,
        #                            text="Save", pad=pad0, scale=0.05,
        #                            pos=(frameSize[1] - 10*0.05, 0, lastYpos), command=self.savePressed
        #                            )
        #self.finishButton = DirectButton ( parent = self.myFrame,
        #        text="Finish", pad=pad0, scale=0.05,
        #        pos=(frameSize[1] - 5*0.05,0,lastYpos), command=self.finishPressed
        #        )
        #self.finishButton["state"] = DGG.DISABLED
        #self.clearButton = DirectButton ( parent = self.myFrame,
        #        text="Clear", pad=pad0, scale=0.05,
        #        pos=(frameSize[1] - 15*0.05,0,lastYpos), command=self.clearButton
        #        )
        self.nextButton = DirectButton(
                                        parent = self.myFrame, text="Next",
                                        pad=pad0, scale=0.05,
                                        pos=(frameSize[1]-10*0.05,0,-0.9),
                                        command=self.nextPressed
                                      )
        # resize canvas to fit in height
        self.myFrame['canvasSize'] = ( frameSize[0],frameSize[1],lastYpos,frameSize[3] )

    #def savePressed(self):
    #    self.saveInputs()

    #def finishPressed(self):
    #    self.config.world.advanceFSM()

    #def clearButton(self):
    #    self.clearInputs()
    def nextPressed(self):
        self.sendMessage('nextPressed')

    def saveInputs(self):
        """
        Saves all the information from the form. If the JSON describing the
        form specifies datatypes for the inputs, then a conversion is performed,
        otherwise the value is saved a string. TickBox is always boolean.
        """
        # Internal comment:
        # self.config.input has the same order as self.guiLabels and self.focusOrder
        # self.focusOrder is a list with each widget (with or without focus!)
        # Use datatype specified in the JSON to convert the values, if no datatype
        # is specified, assume string

        for i,w in zip(self.config.input, self.focusOrder):
            datatypes=('int','float','str','bool')

            if (i.type == 'TickBox'):
                # my custom attribute, added in the event handler!
                self.userInput[i.label] = w.clicked
            else:
                """TextEntry or Option"""
                if (i.type == "TextEntry"):
                    value = w.get(plain=True)
                else:
                    value = w.get()
                try:
                    t = i.datatype
                    if (t in datatypes):
                        evaluate = "%s(%s)" % (t,value)
                        printOut("Evaluating expresion: %s" %evaluate,1)
                        value = eval(evaluate)
                except AttributeError:
                    printOut("No datatype defined for %s, assuming string" % i.label, 1)
                except:
                    printOut("Invalid conversion from String to %s" % (t),1)
                    pass
                self.userInput[i.label] = value

        printOut("Values saved from Form:", 1)
        for (k,v) in self.userInput.items():
            printOut("%s: %s" % (k,v), 1)


    def clearInputs(self):
        for i in self.focusOrder:
            try:
                i.enterText('')
            except:
                # just ignore invalid method exception
                pass

    def optionMenu(self, newOption, widget):
        return
        # print newOption," selected on ", str(widget)

    def tickBoxClicked(self, state, widget):
        # thanks python...add a new member here because there is no
        if (state==1):
            state=True
        else:
            state=False
        widget.clicked = state

    def setText(self, text, widget):
        """Method called when the user presses Return on a text field"""
        # get position of the widget in the list of widgets
        pos = self.focusOrder.index(widget)
        pos = (pos+1)%len(self.focusOrder)
        # remove focus
        widget['focus']=0
        # find next widget that can accept focus and change it
        # BE CAREFUL, THIS COULD CYCLE COMPLETELY UNTIL THE PREVIOUS WIDGET!!!
        while (1):
            try:
                self.focusOrder[pos]['focus'] = 1
                break
            except:
                pos = (pos + 1) % len(self.focusOrder)

    #def directEntryClearText(self):
    #    pass

    def enterState(self):
        Element.enterState(self)
       #self.config.world.stopKeyboard()

    def exitState(self):
        # exit state
        self.saveInputs()
        Element.exitState(self)


