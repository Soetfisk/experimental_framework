import time

from Utils.Debug import printOut

class Logger(object):
    """simple class to dump timestamps and
    events from the game"""
    def __init__(self,fileName, mode):
        "Creates a log, throws exception of error opening file"

        # set this to -1 until we start logging
        self.baseTime = 0.0

        if fileName is not 'nolog':
            try:
                f = open(fileName,mode)
                self.logging = True
                self.outfile = f
                printOut("Logging on " + fileName, 4)
                # we will store in memory the log, until the end.
                self.logList = []
            except Exception,e:
                printOut("Warning: Failed generating log file %s" % fileName, 0)
                printOut("Warning: Will continue, but no log will be generated", 0)
                print e
                self.logging = False
        else:
            self.logging = False

        if self.logging is False:
            # avoid any call to this functions with a dummy function
            self.startLog = self._startLog
            self.logEvent = self._logEvent
            self.stopLog  = self._stopLog

    def _noLog(self):
        pass

    def isLogging(self):
        return self.logging

    def _startLog(self,t):
        pass
    def startLog(self,t=-1):
        if t==-1:
            t = time.time()
        self.baseTime = t
        # instead of writing into a file, dump all in memory, and write at the end
        self.logStarted=True

    def _logEvent(self, event, ts):
        pass

    def writeln(self, text):
        """
        Writes a line of text without a timestamp in the log file
        :param text: str
        :return: None
        """
        self.logList.append(text+'\n')
        return

    def logEvent(self,event, ts=-1):
        """Logs a single event, with a timestamp with
        5 fractional digits of precision
        An event is a timestamp, a colon (:), an event
        key and arguments or extra description of the event
        if necessary"""
        # format output...
        if (ts==-1):
            ts = time.time()

        self.logList.append("%7.4f:%s" % (ts - self.baseTime, event))

    def _stopLog(self):
        pass
    def stopLog(self):
        self.closeLog(time.time())

    def closeLog(self, ts=-1):
        if (ts == -1):
            ts = time.time()

        if (self.baseTime==-1):
            printOut("Warning: closing log before starting the timers",1)
            printOut("Warning: timestamps will not make sense",1)
            self.baseTime=0


        #print "Closing log on " + str(self.outfile)
        ts2 = ts - self.baseTime
        # write backlog
        for l in self.logList:
            self.outfile.write(l)
        # close file
        finalTime="%7.3f:" % ts2
        self.outfile.write(finalTime)
        self.outfile.write(":EOL\n")
        self.outfile.close()
    
