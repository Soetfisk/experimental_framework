# -*- coding: utf-8 -*-

import glob, os
import platform

import PySide
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType

import external.yaml as yaml
from collections import OrderedDict
from Utils.yamlToParameter import fromYamlToParameter,pushUp
from functools import partial

#============================================================================
class Element():
    # utility class that accesses the folder with Element templates and provides
    # the YAML description along with their names.
    templates = {}

    def __init__(self):
        # yaml templates for the element in the folder Templates
        pass

    @classmethod
    def findTemplates(cls, dir = "Elements/Templates"):
        if cls.templates == {}:
            for file in glob.glob(dir+'/*.yaml'):
                # grab file name and remove extension, use that as a key.
                off = file.rfind('\\')
                cls.templates[file[off+1:-5]] = pushUp(yaml.load(open(file)))
        return cls.templates.keys()

    @classmethod
    def getTemplate(cls, elementName):
        return cls.templates.get(elementName,None)


class TransitionsGroup(pTypes.GroupParameter):
    # special class to group transitions in a tree.
    # includes context menues to rename, remove and add transitions
    # naming is automatic.
    # also provides a method to return a YAML version of the transitions in the
    # group
    def __init__(self, **opts):
        opts['type']='group'
        opts['addText']='Add'
        opts['addList']=['transition','extract']
        pTypes.GroupParameter.__init__(self, **opts)

    def extractYamlTransitions(self):
        result = []
        for t in self.children():
            children = [x.value() for x in t.children()]
            tr = '{arg[0]} @ {arg[1]}:{arg[2]}'.format(arg=children)
            result.append({'trans':tr })
        print result

    def addNew(self, typ):
        if 'extract' in typ:
            self.extractYamlTransitions()
            return
        t = {'from':'completeX', 'to':'completeX', 'msg':'completeX'}
        id = len(self.childs)+1
        while True:
            try:
                name = 'transition %d' % id
                transition = fromYamlToParameter(t,name)
                transition['renamable']=True
                transition['removable']=True
                self.addChild(transition)#dict(name="transition %d" % (len(self.childs)+1), type='group', children=val, removable=True, renamable=True))
                break
            except:
                id += 1
                pass

class ElementsGroup(pTypes.GroupParameter):
    """
    Class to handle Elements in the property tree, rename, add, remove
    Property NAME maintains consistency with the elements name inside.

    When an element is created, the YAML version loaded from the file is
    saved, so when we want to export it we can simply save the parts that
    have changed.
    """
    def __init__(self, **opts):
        opts['type']='group'
        opts['addText']='Add'
        opts['addList']=Element.findTemplates()

        pTypes.GroupParameter.__init__(self, **opts)
        #self.sigChildAdded.connect(self.childAddedA)

        for e in self.children():
             e.opts['expanded']=False
             e.sigNameChanged.connect(self.elementNameChanged)
             e.child('className').setReadonly(True)

             for j in e.children():
                 if j.name() == 'name':
                     j.sigValueChanged.connect(self.elementNameChangedInside)
                     break

    def elementNameChangedInside(self, el):
        el.parent().setName(el.value())



    def elementNameChanged(self, el):
        for j in el.children():
            if j.name() == 'name':
                j.setValue(el.name())
                break

    def addNew(self, typ):
        id = len(self.childs)+1
        name = str(typ)+str(id)
        temp = fromYamlToParameter(Element.getTemplate(typ),name)
        temp['renamable']=True
        temp['removable']=True
        temp['expanded']=False
        for child in temp['children']:
            if 'className' in child.values() or 'module' in child.values():
                child['readonly'] = True

        # this while loop is just to create a unique name
        newDict = None
        while True:
            try:
                name = str(typ)+str(id)
                temp['name'] = name
                newDict = None
                for el in temp['children']:
                    if 'name' in el.values():
                        newDict = el
                        temp['children'].remove(el)
                        newDict['value']=name
                        break
                temp['children'].insert(1,newDict)
                self.addChild(temp)
                break
            except:
                id += 1
                pass
        child = self.child(name)
        child.sigNameChanged.connect(self.elementNameChanged)
        for j in child.children():
            if j.name() == 'name':
                j.sigValueChanged.connect(self.elementNameChangedInside)
                break
        for i in child.items:
            i.contextMenu.addSeparator()
            i.contextMenu.addAction('Test alone').triggered.connect(partial(testElement, child))

def testElement(el):
    elementYaml = {}
    elementYaml[el.name()] = extractDictionary(el)
    print elementYaml

def extractDictionary(param):
    if isinstance(param, pTypes.GroupParameter):
        intermediate = {}
        for c in param.children():
            intermediate[c.name()] = extractDictionary(c)
        return intermediate
    elif param.opts['type'] == 'color':
        return (param.value().red(),param.value().green(),param.value().blue(),param.value().alpha())
    else:
        return param.value()

class Application():

    def __init__(self, yamlConfigFile = "experiments/empty.yaml"):
        # Must construct a QApplication before a QPaintDevice
        self.app = QtGui.QApplication([])
        self.win = QtGui.QWidget()

        # prepare parameters tree
        elements, transitions = self.setupParameterTrees(yamlConfigFile)
        self.paramElem = Parameter.create(name='ElementsTree', type='group', children=elements)
        self.paramTran = Parameter.create(name='TransitionsTree', type='group', children=transitions)

        # elements
        self.elementsTree = ParameterTree()
        self.elementsTree.setParameters(self.paramElem, showTop=False)
        self.elementsTree.menu = None

        # fix late context menus on parameter tree elements
        elements = self.paramElem.child("Elements")
        for c in elements.children():
            for i in c.items:
                try:
                    i.contextMenu.addSeparator()
                    i.contextMenu.addAction('Test alone').triggered.connect(partial(testElement,c))
                except:
                    pass

        # transitions
        self.transitionsTree = ParameterTree()
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
        print self.getMainWindowId()
        QtGui.QApplication.instance().exec_()

    def getMainWindowId(self):
        wid = self.win.winId()
        if platform.system() == "Windows":
            import ctypes
            ctypes.pythonapi.PyCObject_AsVoidPtr.restype = ctypes.c_void_p
            ctypes.pythonapi.PyCObject_AsVoidPtr.argtypes = [ ctypes.py_object ]
            wid = ctypes.pythonapi.PyCObject_AsVoidPtr(wid)
        return wid

    def setupParameterTrees(self, yamlFile):
        """Build two parameters tree based on Elements and Transitions"""
        self.yConfig = pushUp(yaml.load(open(yamlFile)))
        elements=[]
        for e in self.yConfig['elements']:
            elements.append(fromYamlToParameter(e,e['name']))
            elements[-1]['renamable']=True
            elements[-1]['removable']=True
        elementsGroup = ElementsGroup(name='Elements', children=elements)

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
            myTransition = fromYamlToParameter(t,'transition %d'%i)
            myTransition['removable']=True
            myTransition['renamable']=True
            transitions.append(myTransition)
        transitions = TransitionsGroup(name="Transitions", children=transitions)

        return ([elementsGroup], [transitions])


"""
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
"""

if __name__=='__main__':
    app = Application()

