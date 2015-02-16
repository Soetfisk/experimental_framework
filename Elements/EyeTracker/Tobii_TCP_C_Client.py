from Elements.EyeTracker.EyeTrackerClient import EyeTrackerClient
import socket


# @TODO Implement TCP client, protocol over TCP to connect to C Client,
# @TODO
# empty class
class Tobii_TCP_C_Client(EyeTrackerClient):

    def __init__(self, **kwargs):
        """
        Connects to a TCP server that is connected to the EyeTracker
        just to provide a stream of gaze data
        :param kwargs: dict
        :return: None
        """
        if getattr(self, "defaults", None) is None:
            self.defaults = {}
        self.defaults["serverIp"] = "127.0.0.1"
        self.defaults["serverPort"] = 2345

        super(Tobii_TCP_C_Client, self).__init__(**kwargs)

    def connect(self):
        self.tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcpSocket.connect((self.config.serverIp, self.config.serverPort))
        self.tcpSocket.send("CONNECT")
        ans = self.tcpSocket.recv(128)
        if (ans == "CONNECTED"):
            self.connected = True
        else:
            self.connected = False

    def disconnect(self):
        self.tcpSocket.send("DISCONNECT")
        self.tcpSocket.close()

    def startTracking(self):
        if (self.connected):
            self.tcpSocket.send("START_TRACKING")
            taskMgr.add(self.readGaze,'readGazeTask')

    def stopTracking(self):
        self.tcpSocket.send("STOP_TRACKING")

    def enterState(self):
        EyeTrackerClient.enterState(self)
        self.connect()
        self.startTracking()

    def exitState(self):
        self.stopTracking()
        self.disconnect()
        EyeTrackerClient.exitState(self)

    def readGaze(self, t):
        return t.cont
