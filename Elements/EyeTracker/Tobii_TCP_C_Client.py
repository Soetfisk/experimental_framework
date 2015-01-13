from Elements.EyeTracker.EyeTrackerClient import EyeTrackerClient

# @TODO Implement TCP client, protocol over TCP to connect to C Client,
# @TODO
# empty class
class Tobii_TCP_C_Client(EyeTrackerClient):
    def __init__(self, **kwargs):
        super(Tobii_TCP_C_Client, self).__init__(**kwargs)
#
    def connect(self):
        pass

    def disconnect(self):
        pass

    def startTracking(self):
        pass

    def stopTracking(self):
        pass

    def enterState(self):
        EyeTrackerClient.enterState(self)

    def exitState(self):
        EyeTrackerClient.exitState(self)
