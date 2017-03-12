# panda imports
from direct.gui.DirectGui import *

#sys utils

#game imports
from Elements.Game.Game import Game as GameClass
from Elements.Game.Parachute import *
from Elements.Element.Element import *
from Elements.Game.targetGuide import *

class Replay(GameClass):
    """class to implement replay functionality"""

    def __init__(self, **kwargs):

        # build game element, no extra arguments needed.
        super(Replay,self).__init__(**kwargs)
        # hide the node until is used
        self.hideElement()
        # used to remember if the slider was changed using
        # the mouse
        self.lastSliderPos = 0

    def enterState(self):
        # call super enterState first
        Element.enterState(self)
        self.setupReplay()
        self.config.world.ignore('mouse1-down')
        self.config.world.ignore('mouse1-up')

    def exitState(self):
        # call super first
        Element.exitState(self)

    def readLogFile(self, logFile):
        """Parses the log file, which contains basically timestamps,
           events and arguments if they are needed by the events"""
        # read the WHOLE file
        lines = open(logFile).readlines()
        # three equally sized lists with numbers
        stamps = range(0, len(lines))
        events = range(0, len(lines))
        evtArgs = range(0, len(lines))

        for i in range(0, len(lines)):
            '''
            Fields examples:
            Parachute quality
            0.000:Q:['GREEN_5',0]
            Parachute position
            0.001:P:['RED_5',-122.361,140.000,203.004]
            CrossHair position
            0.001:C:[173.422,-6.452]
            Turret HeadingPitchRoll
            0.001:T:[22.530,135.000,20.163]
            Keyboard arrows state
            0.316:K:[1, 0, 0, 0]
            Shoot has happened.
            1.952:S
            '''
            s = lines[i].strip().split(':')
            # read a float by BRUTE FORCE!
            stamps[i] = eval(s[0]) 
            # read a key to call a function
            events[i] = s[1]
            # read a list of arguments
            try:
                # try to force reading a LIST by BRUTE FORCE, I know this is
                # dangerous, but we are not supposed to tamper in the LOG files
                # anyway!. If many people use this application framework then
                # this might need to be re-implemented...
                # this code is highly coupled with how the game generates the
                # logs
                l = eval(s[2])
                evtArgs[i] = l
                if (events[i] == 'P' or events[i] == 'B'):
                    # convert to list of ID (parachute or ball) and Vec3
                    evtArgs[i] = [l[0], Vec3(l[1],l[2],l[3])]
                elif (events[i] == 'H'):
                    pass
                elif (events[i] == 'C'):
                    evtArgs[i] = Vec3(l[0],l[1],0)
                elif (events[i] == 'T'):
                    evtArgs[i] = Vec3(l[0],l[1],l[2])
            except:
                evtArgs[i] = None

        # store the lists in the game object
        self.logged_stamps=stamps
        self.logged_events=events
        self.logged_eventArgs=evtArgs

    def setupReplay(self):
        """ sets the game basic elements """
        # clear all collisions patterns
        # self.colHandlerEvent.clearInPatterns()
        # self.colHandlerEvent.clearOutPatterns()
        #expecting this keyword for the file name:
        try:
            self.readLogFile(self.s_replayLog)
        except AttributeError:
            print "Missing replay log file in the Experiment setup"
            sys.quit()
        except IOError:
            print "Could not open the file " + self.s_replayLog
            sys.quit()
        self.playing = False
        self.replaySlider = DirectSlider( range=(0,len(self.logged_events)),
                                          value=0,pageSize=1, command=self.updateSlider)

        self.replayBaseTime = self.logged_stamps[0]
        # width is the whole screen size, so now it is 0.3 * 2 == 0.6
        scale=0.5
        self.replaySlider.setScale(scale)
        self.replaySlider.setX(base.a2dLeft + scale + 0.05)
        self.replaySlider.setZ(base.a2dBottom + self.replaySlider.getHeight())
        #print "Base time in Log: ", self.replayBaseTime
        #self.replaySlider.hide()
        return
    #===========================================

    def toggleReplaySlider(self):
        if (self.replaySlider.isHidden()):
            self.replaySlider.show()
        else:
            self.replaySlider.hide()
        pass

    def replayLogTask(self,task):
        """
        :param t: Panda task
        :return: Task.cont or Task.done
        """
        elapsed = task.time
        #print "Task elapsed time:", elapsed
        # while the time elapsed is greater than the difference between the current
        # log timestamp and the base timestamp, execute the log line
        line = int(self.replaySlider.getValue())
        while elapsed >= self.logged_stamps[line]-self.replayBaseTime:
            #print line
            code = self.logged_events[line]
            # reproduce the position of the PARACHUTES
            args = self.logged_eventArgs[line]

            if code == 'P':
                # parachute position
                self.parachutes[args[0]].setPos(args[1])
                self.parachutes[args[0]].modelNP.show()
            elif code == 'C':
                # position cannon
                self.cannon.setHpr(args)
            elif code == 'E':
                # position eyetracker record
                pass
            #elif (code == 'K'):
            #    self.mapkeys = self.logged_eventArs[l]
            elif code == 'S':
                # shoot!
                self.shoot()
            elif code == 'H':
                # parachute hit
                self.parachutes[args[0]].hitted=True
                self.parachutes[args[0]].modelNP.hide()
            elif code == 'A':
                self.targetGuideHUD.forceArrow(args)
            elif code == 'T':
                self.crosshairNP.setPos(args)
            elif code == 'Q':
                self.parachutes[args[0]].forceTexture(args[1])
                    
            # event processed, go to next event
            line+=1

            if len(self.logged_stamps) == line:
                # don't return Task.cont, but t.done to stop the task
                self.playing = False
                self.replaySlider.setValue(line)
                return Task.done
        self.replaySlider.setValue(line)
        return Task.cont

    def updateSlider(self):
        #self.config.world.accept('mouse1-up', self.updateGame, [])
        #if self.playing:
        #    self.stopReplay()
        pass

    def updateGame(self):
        self.config.world.ignore('mouse1-up')
        #self.startReplay()

    def displayEyeGaze(self):
        pass

    def togglePauseReplay(self):
        if self.playing:
            self.stopReplay()
        else:
            # hide all parachutes
            self.hideAllParachutes()
            self.startReplay()

    def hideAllParachutes(self):
        for p in self.parachutes.values():
            p.setPos(Vec3(0, 1000, 0))

    def startReplay(self):
        if self.playing:
            return
        # the task by itself has a timer! (task.time)
        self.hideAllParachutes()
        taskMgr.add(self.replayLogTask, "replayLogTask")
        # this is the base timestamp from the log
        if self.replaySlider.getValue()==0:
            self.replayBaseTime = 0
        else:
            self.replayBaseTime = self.logged_stamps[int(self.replaySlider.getValue())-1]
        # set flag
        #print "Replay Base time: ",self.replayBaseTime
        self.playing = True
        return

    def stopReplay(self):
        if self.playing:
            taskMgr.remove("replayLogTask")
            self.playing = False

