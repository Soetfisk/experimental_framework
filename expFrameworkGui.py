# -*- coding: utf-8 -*-
import PySide
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType
import numpy as np
import os

pg.mkQApp()

## Define main window class from template
path = os.path.dirname(os.path.abspath(__file__))
uiFile = os.path.join(path, 'designerExample.ui')
WindowTemplate, TemplateBaseClass = pg.Qt.loadUiType(uiFile)

class MainWindow(TemplateBaseClass):
    def __init__(self):
        TemplateBaseClass.__init__(self)
        self.setWindowTitle('pyqtgraph example: Qt Designer')

        self.params = Parameter.create(name='params', type='group', children=[
            dict(name='Load Preset..', type='list', values=[]),
            #dict(name='Unit System', type='list', values=['', 'MKS']),
            dict(name='Duration', type='float', value=10.0, step=0.1, limits=[0.1, None]),
            dict(name='Reference Frame', type='list', values=[]),
            dict(name='Animate', type='bool', value=True),
            dict(name='Animation Speed', type='float', value=1.0, dec=True, step=0.1, limits=[0.0001, None]),
            dict(name='Recalculate Worldlines', type='action'),
            dict(name='Save', type='action'),
            dict(name='Load', type='action'),
            ])
        self.tree = ParameterTree()
        self.tree.setParameters(self.params, showTop=False)
        self.tree2 = ParameterTree()
        self.tree2.setParameters(self.params, showTop=False)

        self.ui = WindowTemplate()
        self.ui.setupUi(self)

        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout()
        widget.setLayout(layout)
        layout.addWidget(self.tree)
        layout.addWidget(self.tree2)

        # Create the main window
        self.setCentralWidget(widget)
        #self.ui.plotBtn.clicked.connect(self.plot)

        self.show()

    def plot(self):
        pass
        #self.ui.plot.plot(np.random.normal(size=100), clear=True)

win = MainWindow()


## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
