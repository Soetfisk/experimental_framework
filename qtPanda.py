__author__ = 'francholi'

import sys
import platform

from PySide.QtCore import *
from PySide.QtGui import *
from PySide import QtUiTools
from multiprocessing import Process, Pipe

from panda3d.core import loadPrcFileData
from panda3d.core import WindowProperties
from direct.showbase.ShowBase import ShowBase

def loadUi(uifilename, parent=None):
    loader = QtUiTools.QUiLoader()
    uifile = QFile(uifilename)
    uifile.open(QFile.ReadOnly)
    ui = loader.load(uifile, parent)
    uifile.close()
    return ui

class FrontEnd(QWidget):
    def __init__(self, pipe, ui):
        QWidget.__init__(self)
        absLayout = QVBoxLayout()
        absLayout.addWidget(ui)
        self.setLayout(absLayout)
        #self.pandaView = ui.pandaPreview


        self.pipe = pipe

        #self.resize(800, 600)
        self.setWindowTitle('Simple')
        self.show()
        #self.pandaView.setParent(None)
        #self.pandaView.show()

    def getViewportID(self):
        wid = self.winId()
        if platform.system() == "Windows":
            import ctypes
            ctypes.pythonapi.PyCObject_AsVoidPtr.restype = ctypes.c_void_p
            ctypes.pythonapi.PyCObject_AsVoidPtr.argtypes = [ ctypes.py_object ]
            wid = ctypes.pythonapi.PyCObject_AsVoidPtr(wid)
        return wid

    def resizeEvent(self, e):
        self.pipe.send(["resize", e.size().width(), e.size().height()])

class BackEnd(object):
    def __init__(self, viewportID, pipe):
        self.pipe = pipe

        #loadPrcFileData("", "window-type none")

        #ShowBase()
        #wp = WindowProperties()
        #wp.setOrigin(0, 0)
        #wp.setSize(800, 600)
        #wp.setParentWindow(viewportID)
        #base.openDefaultWindow(props = wp, gsg = None)

        #s = loader.loadModel("smiley.egg")
        #s.reparentTo(render)
        #s.setY(5)

        #base.setFrameRateMeter(True)
        #base.taskMgr.add(self.checkPipe, "check pipe")

        #base.run()

    def closeCallback(self):
        sys.exit()

    def resizeCallback(self, viewportSizeH, viewportSizeV):
        pass
        #wp = WindowProperties()
        #wp.setOrigin(0, 0)
        #wp.setSize(viewportSizeH, viewportSizeV)
        #base.win.requestProperties(wp)

    def checkPipe(self, task):
        while self.pipe.poll():
            request = self.pipe.recv()
            method = request[0]
            args = request[1:]

            getattr(self, method + "Callback")(*args)

        return task.cont

class Controller(object):
    def __init__(self):
        self.pipe, remote_pipe = Pipe()
        self.app = QApplication([])
        MainWindow = loadUi("ui.ui")
        self.frontEnd = FrontEnd(self.pipe, MainWindow)

        self.backEnd = Process(
            target = BackEnd,
            args = (self.frontEnd.getViewportID(), remote_pipe)
        )

        self.app.aboutToQuit.connect(self.onDestroy)

        self.backEnd.start()
        self.app.exec_()

    def onDestroy(self, *args):
        print "Destroy"
        self.pipe.send(["close"])
        self.backEnd.join(1)
        if self.backEnd.is_alive():
            self.backEnd.terminate()

if __name__ == "__main__":
    c = Controller()

