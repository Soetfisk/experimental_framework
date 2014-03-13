import time

from Utils.Debug import printOut

class Logger(object):
    """simple class to dump timestamps and
    events from the game"""
    def __init__(self,fileName, mode):
        "Creates a log, throws exception of error opening file"

        # set this to false unless we can open the file or the
        # name is different from 'nolog'
        self.logging = False
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

        if self.logging is False:
            # avoid any call to this functions with a dummy function
            self.startLog = self._noLog
            self.logEvent = self._noLog
            self.stopLog  = self._noLog

    def _noLog(self):
        pass

    def isLogging(self):
        return self.logging

    def startLog(self,t):
        self.baseTime = t
        # instead of writing into a file, dump all in memory, and write at the end
        self.logStarted=True

    def logEvent(self,event, ts):
        """Logs a single event, with a timestamp with
        5 fractional digits of precision
        An event is a timestamp, a colon (:), an event
        key and arguments or extra description of the event
        if necessary"""
        # format output...
        ts2 = "%7.3f:" % (ts - self.baseTime)
        new_line = ts2+event
        self.logList.append(new_line)

    def stopLog(self):
        self.closeLog(time.time())

    def closeLog(self, ts):
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
    
