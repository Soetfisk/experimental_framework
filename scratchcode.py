__author__ = 'francholi'
#============================================================================
#class YamlParameterTree(ParameterTree):
#    def __init__(self, appPtr):
#        ParameterTree.__init__(self)
#        self.appPtr = appPtr
#        #self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
#        #self.customContextMenuRequested.connect(self.raiseContextMenu)
#        #self.removeContextMenu = None
#        #self.addTransitionMenu = None
#
#    def mouseClickEvent(self, ev):
#        if ev.button() == QtCore.Qt.RightButton:
#            if self.raiseContextMenu(ev):
#                ev.accept()
#
#    def raiseContextMenu(self, pos):
#        global_pos = self.mapToGlobal(pos)
#        self.selectedItem = None
#        self.selectedItem = self.itemAt(pos.x(),pos.y())
#        if self.selectedItem and self.selectedItem.param.parent():
#            pname = self.selectedItem.param.parent().name()
#            if pname == 'Elements' or pname == 'Transitions':
#                menu = self.getRemoveContextMenu()
#                menu.popup(QtCore.QPoint(global_pos.x(), global_pos.y()))
#            elif self.selectedItem.param.name() == 'Transitions':
#                menu = self.getAddTransitionCtxMenu()
#                menu.popup(QtCore.QPoint(global_pos.x(), global_pos.y()))
#            else:
#                pass
#
#        return True
#
##    def getAddTransitionCtxMenu(self):
##        if self.addTransitionMenu is None:
##            self.addTransitionMenu = QtGui.QMenu()
##            self.addTransitionMenu.setTitle("Remove")
##            addTransAction = QtGui.QAction("Add transition", self.addTransitionMenu)
##            addTransAction.triggered.connect(self.addTransition)
##            self.addTransitionMenu.addAction(addTransAction)
##            #self.getAddTransitionCtxMenu.addTransAction = addTransAction
##        return self.addTransitionMenu
#
#    # This method will be called when this item's _children_ want to raise
#    # a context menu that includes their parents' menus.
#    def getRemoveContextMenu(self):
#        if self.removeContextMenu is None:
#            self.removeContextMenu = QtGui.QMenu()
#            self.removeContextMenu.setTitle("Remove")
#            removeItemAction = QtGui.QAction("Remove", self.removeContextMenu)
#            removeItemAction.triggered.connect(self.removeItem)
#            self.removeContextMenu.addAction(removeItemAction)
#            #self.removeContextMenu.removeItem = removeItemAction
#        return self.removeContextMenu
#            #alpha = QtGui.QWidgetAction(self.menu)
#            #alphaSlider = QtGui.QSlider()
#            #alphaSlider.setOrientation(QtCore.Qt.Horizontal)
#            #alphaSlider.setMaximum(255)
#            #alphaSlider.setValue(255)
#            #alphaSlider.valueChanged.connect(self.setAlpha)
#            #alpha.setDefaultWidget(alphaSlider)
#            #self.menu.addAction(alpha)
#            #self.menu.alpha = alpha
#            #self.menu.alphaSlider = alphaSlider
#            #return self.menu
#
#    def removeItem(self):
#        parentParam = self.selectedItem.parent()
#        t = self.appPtr.paramTran
#        a = t.child('Transitions')
#        a.removeChild(a.names[self.selectedItem.param.name()])
#        self.selectedItem = None

#    def addTransition(self):
#        self.appPtr.addTransition()

