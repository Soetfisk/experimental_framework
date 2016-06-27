__author__ = 'Francholi'

# panda imports
from direct.gui.DirectGui import *
from direct.task.Task import *
from panda3d.core import *
from Elements.Element.Element import *

from Utils.Utils import enum

from socket import socket, error, AF_INET, SOCK_STREAM

#sys utils
import sys

class ServerConfig(Element):
    """
    ServerConfig class to connect to the server, get configuration
     and push configuration when the experiment finishes.
    """
    def __init__(self, **kwargs):
        # build basic element
        super(ServerConfig, self).__init__(**kwargs)
        # this defines:
        # self.sceneNP and self.hudNP

        self.serverName = self.config.serverName
        self.serverPort = self.config.serverPort
        self.connToken = None
        self.COM = enum(GET_CONFIG=0, SEND_RESULTS=1)

        tN = TextNode("info_text")
        tN.setAlign(TextNode.ACenter)
        tNP = NodePath(tN)
        tNP.setBin("gui-popup",100)
        tNP.setPos(-0.5,0,-0.9)
        tNP.setName("info_text")
        tNP.setScale(0.05)
        tN.setText("Server Connection Manager")
        tN.setTextColor(1,0,0,1)
        # attach the text node to the HUD section
        tNP.reparentTo(self.hudNP)
        # hide the whole node
        self.infoText = tN
        self.infoTextNP = tNP
        self.hideElement()
        printOut("%s created!" % self.config.name,0)

    def enterState(self):
        # super class enterState
        Element.enterState(self)
        #self.infoTextNP.hide()

    def exitState(self):
        # print "leaving state ScreenText"
        Element.exitState(self)

    def getConfig(self):
        """
        try to connect to server, retrieve
        config information and close the TCP
        connection
        """
        try:
            #self.infoTextNP.show()
            self.infoText.setText("Connecting to server...")
            sock = socket(AF_INET, SOCK_STREAM)
            sock.connect((self.serverName, self.serverPort))
            self.infoText.setText("Connected.")
            sock.send(self.COM.GET_CONFIG)
            self.infoText.setText("Getting configuration...")
            # read configuration for the game
            self.configNode = sock.recv(50)
            printOut("Answer from server: " + self.configNode)
            self.infoText.setText("Configuration obtained.")
        except Exception, e:
            printOut("Couldn't connect to server!",0)
            print e
            self.infoText.setText("Error getting config, using defaults.")
        finally:
            sock.close()

        #self.infoTextNP.hide()

    def pushResults(self, r):
        try:
            #self.infoTextNP.show()
            sock = socket(AF_INET, SOCK_STREAM)
            sock.connect((self.serverName, self.serverPort))
            self.infoText.setText("Connected.")
            sock.send(self.COM.SEND_RESULTS)
            self.infoText.setText("Sending results...")
            # read configuration for the game
            sent = sock.send(r)
            printOut("Sending bytes")
            self.infoText.setText("Success sendind results...")
        except Exception, e:
            self.infoText.setText("Error sending results, please zip the folder"
                                  "'run' and send it through email to "
                                  "flopezluro@gmail.com with subject 'results'")
            print e
        sock.close()

        #self.infoTextNP.hide()












