from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import *
from panda3d.core import *

from Elements.Element.Element import *

import sys
from Utils.Utils import splitString
from Utils.Debug import printOut
from Service import *

class UserQuestionnaire(Element):
    """
    Class to display questions one by one to
    a participant.
    Each question can contain:
    - A text question,
    - One image,
    - a place holder for the answer, depending on the
      type of answer expected.
    """
    def __init__(self, **kwargs):
        """
        Class constructor
        """
        # call Element constructor with configuration arguments
        super(UserQuestionnaire, self).__init__(**kwargs)
        printOut("Element for User Questionnaire constructed", 1)

        # build UI
        self.setupGUI()

        # create a simple service that can be queried in different ways,
        # pass (serverName, serviceName, callback)
        # TODO
        # self.createService('userdata0','UserData', self.getUserData)
        # printOut("Service userdata0 for dataform created",1)

        # in this dictionary we will keep the inputs from the form.
        self.answers = {}

    # def getUserData(self, input=[]):
    #     """Service published by this element,
    #     returns a dictionary with the values read
    #     from the GUI. If the Element hasnt been activated
    #     yet, returns None"""
    #     return self.userInput

    def scale(self,to):
        if to == 'down':
            self.label.setScale(self.label.getScale()[0]*0.99)
            print self.label.getScale()[0]
        else:
            self.label.setScale(self.label.getScale()[0]*1.01)
            print self.label.getScale()[0]

    def setupGUI(self):
        """ Builds the GUI based on the YAML description """
        # read title or set to a default value
        settings = getattr(self.config, "settings", None)
        if settings is None:
            printOut("Missing settings attribute for UserQuestionnaire", 1)
            self.world.quit()

        if getattr(self.config, "questions", None) is None:
            printOut("No questions set, add them to the config file", 1)
            self.world.quit()

        # background colour
        colour = getattr(self.config.settings, "background", [0.2,0.2,0.2,1])

        frameSize = (-self.config.world.camera.ratio,
                     self.config.world.camera.ratio,
                      -1.0,  1.0)

        # DirectFrame that will contain the GUI
        self.myFrame = DirectFrame(parent=self.hudNP,
                                   frameColor=colour,
                                   frameSize=frameSize,
                                   pos=(0,0,0))

        title = getattr(self.config.settings, "title", "Please answer the following questions:")
        self.label = OnscreenText(text = title,
                             pos = (0,0.9), #frameSize[3] - scale*1.5 ),
                             scale = 0.07, #scale * 1.5,
                             fg=(1.0,1.0,1.0,1.0),  #labelColour,
                             align = TextNode.ACenter, mayChange = 1)

        self.label.reparentTo(self.myFrame)

        self.questionNode = OnscreenText(text="question here!",
                             pos = (-1,0.5), #frameSize[3] - scale*1.5 ),
                             scale = 0.07, #scale * 1.5,
                             fg=(1.0,1.0,1.0,1.0),  #labelColour,
                             wordwrap = 30,
                             align = TextNode.ALeft, mayChange = 1)

        self.questionNode.reparentTo(self.myFrame)

        self.answerNode = NodePath("answerNP")
        self.answerNode.reparentTo(self.myFrame)


        self.answersGuiNodes = {}

        self.questionsText = {}

        for q in self.config.questions:
            self.setupQuestions(q)
        self.currQuestion = 0
        self.setupButtons()

    def setupButtons(self):
        self.nextButton = DirectButton( parent=self.answerNode, text="Next --> ",
                                        pad=[0.1,0.1], scale=0.05, pos=(1.05,0,-0.9),
                                        command=self.nextPressed )
        self.prevButton = DirectButton( parent=self.answerNode, text="<-- Prev",
                                        pad=[0.1,.1], scale=0.05, pos=(0.7, 0, -0.9),
                                        command=self.prevPressed)
        self.qnum = OnscreenText(parent=self.answerNode,
                                 text = "1/%d" % len(self.questionsText),
                                 pos = (0.85,-0.9), scale = 0.05, #scale * 1.5,
                                 fg=(1.0,1.0,1.0,1.0),  #labelColour,
                                 wordwrap = 10,
                                 align = TextNode.ALeft, mayChange = 1)
        self.prevButton['state'] = DGG.DISABLED

    def nextPressed(self):
        if self.currQuestion == len(self.questionsText)-1:
            self.sendMessage('auto')
            return

        self.prevButton['state'] = DGG.NORMAL
        if self.currQuestion < len(self.questionsText)-1:
            self.setQuestion(self.currQuestion+1)
            if self.currQuestion == len(self.questionsText)-1:
                self.nextButton['text'] = 'Finish'

    def prevPressed(self):
        self.nextButton['text'] = 'Next'
        if self.currQuestion > 0:
            if self.currQuestion == 1:
                self.prevButton['state'] = DGG.DISABLED
            self.setQuestion(self.currQuestion-1)

    def setQuestion(self, questNum):
        self.answersGuiNodes[self.currQuestion].hide()
        self.currQuestion = questNum
        self.questionNode.setText(self.questionsText[self.currQuestion])
        self.qnum.setText("%d/%d" % (self.currQuestion + 1,
                                     len(self.questionsText)))
        self.answersGuiNodes[self.currQuestion].show()

    def setupQuestions(self, question):

        self.questionsText[question.order] = question.text

        n = NodePath("answerGui_"+str(question.order))
        if 'TextEntry' == question.answerType:
            widget = DirectEntry(text = "" , scale=Vec3(0.1,1,0.1),
                                 cursorKeys=1,
                                 #command=self.setText, extraArgs=[],
                                 pos=(-1,1,0), numLines = 5, focus=0,
                                 width=20)
            widget.reparentTo(n)
        elif 'Option' == question.answerType:
            widget = DirectOptionMenu(text="options", scale=0.07,
                                      items=question.answerOptions,
                                      popupMarkerBorder=(1,0),
                                      initialitem=0,
                                      # command=self.optionMenu, extraArgs=[],
                                      pos=(-1.0,1,0.2))
            widget.reparentTo(n)
        if getattr(question, "graphics", None):
            for g in question.graphics:
                texName = g.image
                t = loader.loadTexture(texName)
                t.setWrapU(Texture.WMClamp)
                t.setWrapV(Texture.WMClamp)
                t.setMinfilter(Texture.FTLinearMipmapLinear)
                t.setAnisotropicDegree(2)
                plane = loader.loadModel("Elements/Game/models/plane")
                plane.setName("plane")
                plane.setPos(Vec3(g.pos[0],g.pos[1],g.pos[2]))
                plane.setScale(g.scale)
                plane.setTransparency(1)
                plane.setTexture(t, 1)
                plane.reparentTo(n)

        self.answersGuiNodes[question.order] = n
        n.reparentTo(self.questionNode)
        n.hide()

           # for each label, create a widget matching the JSOSN
            # widgetYpos = lastYpos


            # if (i.type == 'TickBox'):
                # my custom attribute, added in the event handler!
                # self.userInput[i.label] = w.clicked
            # else:
            #     """TextEntry or Option"""
            #     if (i.type == "TextEntry"):
            #         value = w.get(plain=True)
            #     else:
            #         value = w.get()
            #     try:
            #         t = i.datatype
            #         if (t in datatypes):
            #             evaluate = "%s(%s)" % (t,value)
            #             printOut("Evaluating expresion: %s" %evaluate,1)
            #             value = eval(evaluate)
            #     except AttributeError:
            #         printOut("No datatype defined for %s, assuming string" % i.label, 1)
            #     except:
            #         printOut("Invalid conversion from String to %s" % (t),1)
            #         pass
            #     self.userInput[i.label] = value

        # printOut("Values saved from Form:", 1)
        # for (k,v) in self.userInput.items():
        #     printOut("%s: %s" % (k,v), 1)


    # def clearInputs(self):
    #     for i in self.focusOrder:
    #         try:
    #             i.enterText('')
    #         except:
#                just ignore invalid method exception
                # pass

    # def optionMenu(self, newOption, widget):
    #     return
    #     print newOption," selected on ", str(widget)

    # def tickBoxClicked(self, state, widget):
        # thanks python...add a new member here because there is no
        # if (state==1):
        #     state=True
        # else:
        #     state=False
        # widget.clicked = state

    # def setText(self, text, widget):
    #     """Method called when the user presses Return on a text field"""
        # get position of the widget in the list of widgets
        # pos = self.focusOrder.index(widget)
        # pos = (pos+1)%len(self.focusOrder)
        # remove focus
        # widget['focus']=0
        # find next widget that can accept focus and change it
        # BE CAREFUL, THIS COULD CYCLE COMPLETELY UNTIL THE PREVIOUS WIDGET!!!
        # while (1):
        #     try:
        #         self.focusOrder[pos]['focus'] = 1
        #         break
        #     except:
        #         pos = (pos + 1) % len(self.focusOrder)

    #def directEntryClearText(self):
    #    pass

    def enterState(self):
        Element.enterState(self)
        self.setQuestion(0)

    def exitState(self):
        # exit state
        # self.saveInputs()
        Element.exitState(self)


