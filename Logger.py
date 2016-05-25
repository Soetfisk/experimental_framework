import time

from Utils.Debug import printOut

class Logger(object):
    """simple class to dump timestamps and
    events from the game"""
    def __init__(self,basetime, fileName, mode = 'a'):
        "Creates a log, throws exception of error opening file"

        # set this to -1 until we start logging
        self.baseTime = basetime

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

    def isLogging(self):
        return self.logging

    def startLog(self):
        if not self.logging:
            return
        # instead of writing into a file, dump all in memory, and write at the end
        self.logStarted=True

    def writeln(self, text):
        """
        Writes a line of text without a timestamp in the log file
        :param text: str
        :return: None
        """
        self.logList.append(text+'\n')
        return

    def logEvent(self,event):
        """Logs a single event, with a timestamp with
        5 fractional digits of precision
        An event is a timestamp, a colon (:), an event
        key and arguments or extra description of the event
        if necessary"""
        # format output...
        if not self.logging:
            return

        ts = time.time()

        if event[-1]!='\n':
            event = event + '\n'
        #self.logList.append("%07.5f:%s" % (ts - self.baseTime, event))
        self.logList.append("%07.5f:%s" % (ts - self.baseTime, event))

    def stopLog(self):
        """
        Stop logging.
        :return: None
        """
        if not self.logging:
            return
        self._closeLog()

    def _closeLog(self):
        """
        Private function, used by stopLog, to close the log file if necessary
        :param ts: timestamp
        :return: None
        """
        ts = time.time() - self.baseTime
        # write backlog
        for l in self.logList:
            self.outfile.write(l)
        # close file
        finalTime="%7.3f:EOL\n" % ts
        self.outfile.write(finalTime)
        self.outfile.close()
    
