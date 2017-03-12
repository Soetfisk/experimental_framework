import time
import random

from Debug import printOut

class Logger(object):
    """simple class to dump timestamps and
    events from the game"""
    def __init__(self,basetime, filename, mode = 'a'):
        "Creates a log, throws exception of error opening file"

        # set this to -1 until we start logging
        self.baseTime = basetime
        self.mode = mode
        self.filename = filename

        if filename is not 'nolog':
            self.logging = True
            printOut("Logging on " + filename, 4)

        else:
            self.logging = False

    def isLogging(self):
        return self.logging

    def startLog(self):
        # every time we call startLog we clear the messages
        if not self.logging:
            return
        # instead of writing into a file, dump all in memory, and write at the end
        self.logList = []
        self.logging=True

    def writeln(self, text):
        """
        Writes a line of text WITHOUT a TIMESTAMP in the log file
        :param text: str
        :return: None
        """
        if text[-1] != '\n':
            self.logList.append(text)
        else:
            self.logList.append(text + '\n')
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
        # add new line if necessary
        if event[-1] != '\n':
            self.logList.append("%07.5f:%s\n" % (ts - self.baseTime, event))
        else:
            self.logList.append("%07.5f:%s" % (ts - self.baseTime, event))


    def stopLog(self):
        """
        Stop logging.
        Opens the file (usually in append mode), dumps the string list, closes the file.
        :return: None
        """
        if not self.logging:
            return
        ts = time.time() - self.baseTime
        text = ''.join([s for s in self.logList])
        try:
            with open(self.filename, self.mode) as output:
                # fastest method to concatenate strings in Python
                # then do ONE single write to file
                output.write(text)
                output.write("%07.5f:EOL\n" % ts)
                # file is closed after "with" clause
        except Exception,e:
            print e
            printOut("Warning: Failed writing to log file %s" % self.filename, 0)
            printOut("Trying temporary file...",0)
            tempName = str(random.randint)
            with open(tempName,mode='w') as tempfile:
                tempfile.write(text)
                tempfile.write("%07.5f:EOL\n" % ts)
                printOut("Log dumped to file %s\n" % tempName, 0)
        finally:
            self.logList = []


#    def _closeLog(self):
#        """
#        Private function, used by stopLog, to close the log file if necessary
#        :param ts: timestamp
#        :return: None
#        """
#        # write backlog
#        # close file
#        self.outfile.write(finalTime)
#        self.outfile.close()
    
