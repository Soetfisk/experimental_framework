# -*- coding: utf-8 -*-

import glob, os

import PySide
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType

import external.yaml as yaml
from collections import OrderedDict
from Utils.yamlToParameter import extractElement,pushUp
from functools import partial

#============================================================================
class Element():
    templates = {}

    def __init__(self):
        # yaml templates for the element in the folder Templates
        pass

    @classmethod
    def findTemplates(cls, dir = "Elements/Templates"):
        os.chdir(dir)
        for file in glob.glob('*.yaml'):
            cls.templates[file[:-5]] = pushUp(yaml.load(open(file)))
        return cls.templates.keys()

    @classmethod
    def getTemplate(cls, elementName):
        return cls.templates.get(elementName,None)

#============================================================================
class YamlParameterTree(ParameterTree):
    def __init__(self, appPtr):
        ParameterTree.__init__(self)
        self.appPtr = appPtr
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.raiseContextMenu)
        self.removeContextMenu = None
        self.addTransitionMenu = None

    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            if self.raiseContextMenu(ev):
                ev.accept()

    def raiseContextMenu(self, pos):
        global_pos = self.mapToGlobal(pos)
        self.selectedItem = None
        self.selectedItem = self.itemAt(pos.x(),pos.y())
        if self.selectedItem and self.selectedItem.param.parent():
            pname = self.selectedItem.param.parent().name()
            if pname == 'Elements' or pname == 'Transitions':
                menu = self.getRemoveContextMenu()
                menu.popup(QtCore.QPoint(global_pos.x(), global_pos.y()))
            elif self.selectedItem.param.name() == 'Transitions':
                menu = self.getAddTransitionCtxMenu()
                menu.popup(QtCore.QPoint(global_pos.x(), global_pos.y()))
            else:
                pass

        return True

    def getAddTransitionCtxMenu(self):
        if self.addTransitionMenu is None:
            self.addTransitionMenu = QtGui.QMenu()
            self.addTransitionMenu.setTitle("Remove")
            addTransAction = QtGui.QAction("Add transition", self.addTransitionMenu)
            addTransAction.triggered.connect(self.addTransition)
            self.addTransitionMenu.addAction(addTransAction)
            #self.getAddTransitionCtxMenu.addTransAction = addTransAction
        return self.addTransitionMenu

    # This method will be called when this item's _children_ want to raise
    # a context menu that includes their parents' menus.
    def getRemoveContextMenu(self):
        if self.removeContextMenu is None:
            self.removeContextMenu = QtGui.QMenu()
            self.removeContextMenu.setTitle("Remove")
            removeItemAction = QtGui.QAction("Remove", self.removeContextMenu)
            removeItemAction.triggered.connect(self.removeItem)
            self.removeContextMenu.addAction(removeItemAction)
            #self.removeContextMenu.removeItem = removeItemAction
        return self.removeContextMenu
            #alpha = QtGui.QWidgetAction(self.menu)
            #alphaSlider = QtGui.QSlider()
            #alphaSlider.setOrientation(QtCore.Qt.Horizontal)
            #alphaSlider.setMaximum(255)
            #alphaSlider.setValue(255)
            #alphaSlider.valueChanged.connect(self.setAlpha)
            #alpha.setDefaultWidget(alphaSlider)
            #self.menu.addAction(alpha)
            #self.menu.alpha = alpha
            #self.menu.alphaSlider = alphaSlider
            #return self.menu

    def removeItem(self):
        parentParam = self.selectedItem.parent()
        t = self.appPtr.paramTran
        a = t.child('Transitions')
        a.removeChild(a.names[self.selectedItem.param.name()])
        self.selectedItem = None

    def addTransition(self):
        self.appPtr.addTransition()

class TransactionsGroup(pTypes.GroupParameter):
    def __init__(self, **opts):
        opts['type']='group'
        opts['addText']='Add transaction'
        opts['addList']=['str']
        pTypes.GroupParameter.__init__(self, **opts)

    def addNew(self, typ):
        val = {
            'str':'pepe'
        }[typ]
        self.addChild(dict(name="TransactionsGroup %d" % (len(self.childs)+1), type=typ, value=val, removable=True, renamable=True))


class Application():
    def mouseClicked(self, evt):
        pass
    def __init__(self, yamlConfigFile = "experiments/empty.yaml"):

        # Must construct a QApplication before a QPaintDevice
        self.app = QtGui.QApplication([])
        self.win = QtGui.QWidget()

        # prepare parameters tree
        elements, transitions = self.setupParameterTrees(yamlConfigFile)
        transitions.append(
            TransactionsGroup(name="TransactionsXYZ",
                              children=[
                                  {'name': 'ScalableParam 1', 'type': 'str', 'value': "default param 1"},
                                  {'name': 'ScalableParam 2', 'type': 'str', 'value': "default param 2"}, ]))
        self.paramElem = Parameter.create(name='ElementsTree', type='group', children=elements)
        self.paramTran = Parameter.create(name='TransitionsTree', type='group', children=transitions)

        # elements
        self.elementsTree = YamlParameterTree(self)
        self.elementsTree.setParameters(self.paramElem, showTop=False)
        self.elementsTree.menu = None

        # transitions
        self.transitionsTree = YamlParameterTree(self)
        self.transitionsTree.setParameters(self.paramTran, showTop=False)

        # divide whole window in two
        horizontalSplitter = QtGui.QSplitter()
        horizontalSplitter.setOrientation(QtCore.Qt.Horizontal)
        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        self.win.setLayout(layout)
        layout.addWidget(horizontalSplitter)

        # left hand side of the window
        #self.previewArea = getGraphicsWidget()
        self.previewArea = pg.QtGui.QTextEdit()
        self.previewArea.setText("HERE THERE WILL BE A PREVIEW OF THE FSM, NOT A TEXT EDIT")
        self.previewArea.setReadOnly(True)
        self.debugOutput = pg.QtGui.QTextEdit()
        self.debugOutput.setReadOnly(True)

        # split win widget in LEFT (PREVIEW) and RIGHT (PROPERTY PANES)

        propertySheetSplitter = QtGui.QSplitter()
        propertySheetSplitter.setOrientation(QtCore.Qt.Vertical)

        menuBar = QtGui.QMenuBar()
        actionMenu = menuBar.addMenu('Actions')
        helpMenu = menuBar.addMenu('Help')
        addElementMenu = actionMenu.addMenu('Add Element')
        #addTransMenu = actionMenu.addMenu('Add Transition')

        action = QtGui.QAction('Add Transition', propertySheetSplitter)
        action.triggered.connect(self.addTransition)
        actionMenu.addAction(action)

        for e in Element.findTemplates():
            action = QtGui.QAction(e, propertySheetSplitter)
            action.triggered.connect(partial(self.addElement,e))
            addElementMenu.addAction(action)

        propertySheetSplitter.addWidget(menuBar)
        propertySheetSplitter.addWidget(self.elementsTree)
        propertySheetSplitter.addWidget(self.transitionsTree)

        previewAreaSplitter = QtGui.QSplitter()
        previewAreaSplitter.setOrientation(QtCore.Qt.Vertical)
        previewAreaSplitter.addWidget(self.previewArea)
        previewAreaSplitter.addWidget(self.debugOutput)

        horizontalSplitter.addWidget(previewAreaSplitter)
        horizontalSplitter.addWidget(propertySheetSplitter)

        self.win.show()
        self.win.resize(800,800)
        # run
        QtGui.QApplication.instance().exec_()

    def addTransition(self):
        Transitions = self.paramTran.child('Transitions')
        count = len(Transitions.children())
        name = 'transition '+ str(count)
        while name in Transitions.names.keys():
            count+=1
            name = 'transition '+ str(count)
        t = extractElement(OrderedDict({'from':'completeX', 'to':'completeX', 'msg':'completeX'}),name)
        Transitions.addChild(t)
        self.transitionsTree.setParameters(self.paramTran)

    def addElement(self, argument):
        yamlTemplate = Element.getTemplate(argument)
        propertyTemplate = extractElement(yamlTemplate, yamlTemplate['name'])
        Elements = self.paramElem.child('Elements')
        Elements.addChild(propertyTemplate)

    def setupParameterTrees(self, yamlFile):
        """Build two parameters tree based on Elements and Transitions"""
        #a = open("experiments/empty.yaml")
        #f = open(yamlFile)
        self.yConfig = pushUp(yaml.load(open(yamlFile)))
        elements=[]
        for e in self.yConfig['elements']:
            elements.append(extractElement(e,e['name']))
        elementsGroup = {'type':'group','name':'Elements','children':elements}

        transitions=[]
        for i,t in enumerate(self.yConfig['transitions']):
            if ':' in t:
                msg = t['trans'].split(':')[1]
                if len(msg) is 0: msg='auto'
            else:
                msg='auto'
            tFrom = t['trans'].split('@')[0]
            tTo = t['trans'].split('@')[1].split(':')[0]
            t = OrderedDict()
            t['from']=tFrom
            t['to']=tTo
            t['msg']=msg
            transitions.append(extractElement(t,'transition %d'%i))
        transitionsGroup = {'type':'group','name':'Transitions','children':transitions}

        return ([elementsGroup], [transitionsGroup])


## If anything changes in the tree, print a message
#def change(param, changes):
#    return
#    print("tree changes:")
#    for param, change, data in changes:
#        path = p.childPath(param)
#        if path is not None:
#            childName = '.'.join(path)
#        else:
#            childName = param.name()
#        print('  parameter: %s'% childName)
#        print('  change:    %s'% change)
#        print('  data:      %s'% str(data))
#        print('  ----------')

#p.sigTreeStateChanged.connect(change)


#def valueChanging(param, value):
#    pass
    #print("Value changing (not finalized):", param, value)

# Too lazy for recursion:
#for child in p.children():
#    child.sigValueChanging.connect(valueChanging)
#    for ch2 in child.children():
#        ch2.sigValueChanging.connect(valueChanging)


"""
def save():
    global state
    state = p.saveState()

def restore():
    global state
    add = p['Save/Restore functionality', 'Restore State', 'Add missing items']
    rem = p['Save/Restore functionality', 'Restore State', 'Remove extra items']
    p.restoreState(state, addChildren=add, removeChildren=rem)

#p.param('Save/Restore functionality', 'Save State').sigActivated.connect(save)
#p.param('Save/Restore functionality', 'Restore State').sigActivated.connect(restore)
"""


#def createNode(scene):
#    pen = QtGui.QPen(QtGui.QColor(QtCore.Qt.green))
#    brush = QtGui.QBrush(pen.color().darker(150))
#    view = scene.parent()
#    view = pg.GraphicsView()
#    view.setForegroundBrush(brush)
#    node = scene.addRect(0,0,10,30, pen=pen)
#    node.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
#    return node
#
#def nodeUnderMouse(node):
#    print 'under mouse'

#def getGraphicsWidget():
#    view = pg.GraphicsView()
#    scene = pg.GraphicsScene()
#    view.setScene(scene)
#
#    pen   = QtGui.QPen(QtGui.QColor(QtCore.Qt.green))
#    brush = QtGui.QBrush(pen.color().darker(150))
#    #item = scene.addEllipse(x, y, w, h, pen, brush)
#    #item2 = scene.addRect(x,y,w,h,pen,brush)
#    #scene.setForegroundBrush(brush)
#    item = createNode(scene)
#    #item.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
#    #item2.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
#    #item2 = QtGui.QGraphicsRectItem()
#    #item2.



    # create an open path
    #path = QtGui.QPainterPath()
    #path.moveTo(-w, -h)
    #path.lineTo(-w, h)
    #path.lineTo(w, h)
    #path.lineTo(w, -h)

    #clr   = QtGui.QColor('blue')
    #clr.setAlpha(120)
    #brush = QtGui.QBrush(clr)
    #pen   = QtGui.QPen(QtCore.Qt.NoPen)
    #fill_item = scene.addRect(-w, y, w*2, h, pen, brush)
    #path_item = scene.addPath(path)
#    return view


## test save/restore
#s = p.saveState()
#p.restoreState(s)


if __name__=='__main__':
    app = Application()

