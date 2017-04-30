import time
import random

from Debug import printOut

class Logger(object):
    """simple class to dump timestamps and
    events from the game"""
    def __init__(self,basetime, filename, mode = 'a'):
        """Creates a logger utility, will store results in a python list, and dump them at the
        end when the log is closed..."""

        self.filename = filename
        self.baseTime = basetime
        self.mode = 'a'
        self.logList = []

        if self.filename is 'nolog':
            self.logging = False
            return

        ts = time.time() - self.baseTime

        try:
            with open(self.filename, self.mode) as output:
                output.write("Log created at: ")
                output.write("%07.5f:EOL\n" % ts)
                self.logging = True
        except Exception, e:
            printOut("Cannot create log file at " + self.filename + "this log file will not be valid:",0)
            self.logging = False
            print e

    def resetLog(self):
        # every time we call resetLog we clear the messages
        if not self.logging:
            return
        self.logList = []

    def writeln(self, text):
        """
        Writes a line of text WITHOUT a TIMESTAMP in the log file
        :param text: str
        :return: None
        """
        if not self.logging:
            return

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
        if (not self.logging) and (self.filename != 'nolog'):
            printOut("Trying to stop an invalid logger\n", 0)
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


