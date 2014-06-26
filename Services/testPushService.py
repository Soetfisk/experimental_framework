from panda3d.core import *
 
from Element import *

import sys
from Debug import printOut
from Utils import splitString
from Service import *

class testPushService(Element):
    """Class to test a push service. This class will create a new service, and
    push 2D random coordinates data at 100Hz"""

    def __init__(self, **kwargs):
        """
        Class constructor
        """
        # build basic element
        super(testPushService, self).__init__(**kwargs)
        self.createService()

    def createService(self):
        """ Creates and register a service in the service manager to handle
        queries of data obtained in the data form """
        service = self.config.world.serviceMgr.createFromTemplate( 'UserData' )
        service.setServerName('userdata0')

        service.setServiceImp( self.getUserData )
        # register service
        self.config.world.serviceMgr.registerService ( service )

    def setupGUI(self):
        """ Builds the GUI based on the XML description """
        # stores the GUI labels
        self.guiLabels=[]
        # stores ALL the widgets in order of focus (even if they cannot get focus)
        self.focusOrder = []
        # DirectFrame that will contain the GUI
        self.myFrame = None


        # frame to hold the form (left, right, bottom, top)
        frameSize = (-1.5,1.5,-0.8,0.8)
        # centered
        pos = (0,1.0,0)
        # background colour
        colour = (0.2,0.2,0.2,1)
        # guiLabels colour
        labelColour = map(float, self.xmlConfig.settings.labelcolour.split(','))
        # global scale of the frame
        scale    = float (self.xmlConfig.settings.scale)
        # canvas with scrolling capabilities
        self.myFrame = DirectScrolledFrame ( canvasSize=( frameSize[0], frameSize[1], 50*frameSize[2],
                              frameSize[3]), frameColor = colour, frameSize  = frameSize, pos = pos )
        # reparent the frame to the hudNP so we can hide it easily
        self.myFrame.reparentTo(self.hudNP)

        title = getattr(self.xmlConfig.settings,"title", "Introduce your data")

        # title of the frame
        label = OnscreenText( text = title,
                              pos = (0, frameSize[3] - scale*1.5 ),
                              scale = scale * 1.5, fg=labelColour, align=TextNode.ACenter,
                              mayChange=1 )
        label.reparentTo(self.myFrame.getCanvas())

        # max length in characters of a label (will split in lines if bigger)
        maxLabel = int (self.xmlConfig.settings.maxlabel)
        maxwidth=0
        # position of the first label and widget
        lastYpos = frameSize[3] - scale*4

        for count,i in enumerate(self.xmlConfig.input):

            # create label in several lines up to 15 chars
            # split the string in several lines up to 15 chars
            splitWords = splitString( i.label + ':', 10 )
            for s in splitWords:
                lastYpos -= 1.1*scale

                label = OnscreenText( text = s, pos = (0,lastYpos),scale = scale, fg=labelColour,
                                      align=TextNode.ARight, mayChange=1)
                bounds = label.getTightBounds()
                width = abs(bounds[0][0]-bounds[1][1])
                if (width > maxwidth): maxwidth=width
                label.reparentTo(self.myFrame.getCanvas())
                self.guiLabels.append(label)

            # for each label, create a widget matching the XML
            widgetYpos = lastYpos
            if ( i.type == 'TextEntry' ):
                widget = DirectEntry(text = "" , scale=scale,command=self.setText, 
                        extraArgs=[], pos=(0,1,widgetYpos), numLines = 1, 
                        focus=0)
            elif ( i.type == 'Option' ):
                values = i.values.split(',')
                widget = DirectOptionMenu( text="options", scale=1.10*scale, items=values,
                        popupMarkerBorder=(1,0),
                        initialitem=0, command=self.optionMenu, extraArgs=[], 
                        pos=(0,1,widgetYpos))
            elif ( i.type == 'TickBox' ):
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
            # adjust X position
            l.setX( frameSize[0] + maxwidth + 0.05 )
        for w in self.focusOrder:
            w.setX( w['pos'][0] + frameSize[0] + maxwidth + 0.10 )

        # resize canvas to fit in height
        self.myFrame['canvasSize'] = ( frameSize[0],frameSize[1],lastYpos,frameSize[3] )

    def saveInputs(self):
        """ save each input from the user. self.xmlConfig.input has the
        same order as self.guiLabels and self.focusOrder """
        self.userInput = {}
        for i,w in zip(self.xmlConfig.input, self.focusOrder):
            if (i.type == 'TextEntry'):
                self.userInput[i.label] = w.get(plain=True)
            elif (i.type == 'TickBox'):
                # my custom attribute, added in the event handler!
                self.userInput[i.label] = w.clicked
            elif (i.type == 'Option'):
                self.userInput[i.label] = w.get()

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
        """pos is the position of the widget in the list of widgets"""
        pos = self.focusOrder.index(widget)
        pos = (pos+1)%len(self.focusOrder)
        widget['focus']=0
        # find next widget that can accept focus   
        while (1):
            try:
                # add focus to next one
                self.focusOrder[pos]['focus'] = 1
                break
            except:
                pos = (pos + 1) % len(self.focusOrder)

    #def directEntryClearText(self):
    #    pass

    def getUserData(self, input=[]):
        """Service published by this element,
        returns a dictionary with the values read
        from the GUI. If the Element hasnt been activated
        yet, returns None"""
        return self.userInput

    def enterState(self):
        # super enterState
        Element.enterState(self)

    def exitState(self):
        # exit state
        self.saveInputs()
        Element.exitState(self)

