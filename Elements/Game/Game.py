from time import ctime

#game imports
from targetGuide import targetGuide
from pointsHUD import pointsHUD
from Logger import Logger
from PositionGenerator import PositionGenerator
from Parachute import *
from LodManager import *
from Element import *

from Utils.Debug import printOut, verbosity

try:
        import json
except ImportError:
        import simplejson as json

class Game(Element):
    """class to implement game and replay functionality
       It has still some dependencies with the World class,
       for the keyboard and for the Camera which I should separate
       in classes"""

    def __init__(self,**kwargs):
        """by default is play mode, and no replay log file"""
        # this sets all the attributes specified in the generic JSON
        super(Game,self).__init__(**kwargs)
        self.isReplay = self.className=='Replay'

        # builds two Logger objects, one for replay capabilities
        # and the other one as a general log of the game
        self.setupLog()


        # setup the main components in the game
        self.setupGame()


    #=============================================
    def setupLog(self):
        # creating logger for the replay
        # the string will look like "filename,mode"
        # if no value is found, 'nolog,w' is returned.
        rl = getattr(self,'s_saveReplay','nolog,w').split(',')
        self.replayLog = Logger(rl[0],rl[1])
        # creating logger for the game
        # the string will look like "filename,mode"
        gl = getattr(self,'s_logFile','nolog,a').split(',')
        self.gameLog = Logger( gl[0],gl[1])

    def readUserData(self):
        # Uses a service provided by DataForm.
        # Its a simple service registered by the name 'UserData' that
        # returns the input in the form.
        # We will use it in a blocking call here, so no need for a callback.
        service = self.world.serviceMgr.getService('UserData')
        if (service):
            userData = service.service()
        else:
            userData = None

        # this can be None or the Dictionary, depending if the user already
        # entered the data
        return userData

    def startLogging(self):
        t = time.time()
        self.gameLog.startLog(t)
        self.gameLog.logEvent("==== new game participant ====\n", t)

        # process user data if present (from a previous form)
        if self.userData:
            for k, v in self.userData.items():
                self.gameLog.logEvent("== UI ==  %s: %s\n" % (k,v),t)

        self.gameLog.logEvent("date: " + ctime() + "\n", t)
        self.gameLog.logEvent("game start\n", t)

    #=============================================

    def stopLogging(self):
        self.gameLog.stopLog()
        self.replayLog.stopLog()

    #=============================================

    def setupTerrain(self):
        """Sets terrain model, attaching it to the scene nodepath"""
        # transform to position the ground model
        self.groundTransform = NodePath("groundTransform")
        self.groundTransform.setHpr(120, 0, 0)
        # ground model
        self.ground = loader.loadModel("Elements/Game/models/terrain/master")
        self.ground.setPos(78, -100, 0)
        self.ground.reparentTo(self.groundTransform)
        # ground model is only shown in the gamePlay tree.
        self.groundTransform.reparentTo(self.sceneNP)
        return

    #=============================================

    def setupParachutes(self):
        """Creates parachutes objects needed for the game, loads textures and all..."""

        # references to all the Parachute objects created
        self.parachutes = {}    # dict of parachute objects
        # more references to parachutes, this time by semantics
        # how can we generalize these semantics about the game!
        self.targets = {}       # parachutes that are targets
        self.non_targets = {}   # parachutes that are no targets.

        # load sequences
        # references to the sequences in the config file
        self.seqs = {}          # sequences by id.
        try:
            sequences = self.jsonConfig.targetSequences.sequences
            for s in sequences:
                self.seqs[s.id] = map(str.upper, map(str, s.seq))
            self.currSeq = self.seqs[self.jsonConfig.targetSequences.use]
        except Exception, e:
            print "Error loading target sequence from JSON file"
            print e
            sys.exit()

        # creates LOD manager (implements Observer pattern)
        lm = LodManager()
        # gets the different LOD events that should be considered
        lodEvents = self.jsonConfig.LODEvents.lodEvents
        for l in lodEvents:
            try:
                handler = getattr(lm, l.handler)
                lm.registerHandler(l.evtType, handler, l)
                printOut("registering %s\n" % l.evtType, 1)
            except:
                print "Trying to register a non-existent handler, check JSON gameConfig and LodManager class"


        parConfNode = self.jsonConfig.parachutes
        targetnames = self.currSeq  # target names

        # how many at the same time will fall and at what speed
        parachutesCount = parConfNode.simultaneous
        falltime = parConfNode.falltime

        # how many parachutes of each color, based on the max
        each = int(ceil(float(parachutesCount) / len(parConfNode.parachutes)) )

        # check that 1 of each of the next 3 targets exists in upper
        # third of the screen
        self.centerFirstThird = (-2*self.world.camera.minZ)/3.0
        self.firstThirdSize = self.centerFirstThird

        self.non_targets_cnt = []

        for p in parConfNode.parachutes:
            color = str(p.name.upper())
            # for each colour create 6 parachutes, so to cover three colours
            # in a row.
            for i in range(6):
                # only 2 of each non-target
                if (i > 2 and color not in targetnames):
                    pass
                nameId = color + "_" + str(i)

                # creates parachute object
                obj = Parachute(nameId, p, self, falltime, parConfNode.scale, not self.isReplay)

                obj.modelNP.reparentTo(self.sceneNP)
                self.parachutes[nameId] = obj

                # improve this registration on events
                lm.register(obj, ["CYCLE"])

                if (color not in targetnames):
                    obj.isTarget = False
                    obj.ignoreHit = True
                    self.non_targets[nameId] = obj
                    if (color not in self.non_targets_cnt):
                        self.non_targets_cnt.append(color)
                else:
                    self.targets[nameId] = obj
                    obj.isTarget = True
                    obj.ignoreHit = False

        # DON'T NEED THE LIST ANYMORE!, just replace it with length.
        self.non_targets_cnt = len(self.non_targets_cnt)
        self.lodManager = lm

    #=============================================

    def enterState(self):
        # call super first
        Element.enterState(self)

        # try and read user data from the form.
        # example of a blocking call
        self.userData = self.readUserData()
        printOut("From GAME, just read user data from the form",1)
        printOut(str(self.userData),1)

        # as we need to wait for the async call, we have to start
        # the logging in the callback.
        self.startLogging()

        # eyeTracker task
        self.lastEyeSample = None
        self.world.tracker.connect()

    #=============================================

    def exitState(self):
        # clear all keybindings
        # self.cleanUpKeys()
        # call super first
        Element.exitState(self)
        # specifics
        self.stopLogging()
        # remove all tasks!!!
        taskMgr.remove("addParachutes")
        self.sceneNP.removeNode()
        self.hudNP.removeNode()

        self.world.tracker.stopTrack()
        taskMgr.remove("readTrackerGaze")

    #=============================================

    def logFrameTask(self, t):
        """logs all the positions of parachutes, cannon and ball so the game
        can be reproduced or played back at any speed forward and backward."""
        curr_t = time.time()

        if self.lastEyeSample:
            eyesample = "[%.3f,%.3f]\n" % (self.lastEyeSample[0], self.lastEyeSample[1])
            self.replayLog.logEvent("E:"+eyesample, curr_t)

        # grab all parachutes (name,value) and save their position
        for p_name,par in self.parachutes.items():
            np = par.modelNP
            if (np.getX() != -1000 and par.hitted==False ):
                position = "[\'%s\',%.3f,%.3f,%.3f]\n" % (p_name,np.getX(),np.getY(),np.getZ())
                self.replayLog.logEvent("P:" + position ,curr_t)
        # grab heading and pitch of the cannon
        hpr = self.cannon.getHpr()
        if (self.lastHpr != hpr):
            hpr_str = "[%.3f,%.3f]\n" % (hpr[0],hpr[1])
            self.replayLog.logEvent("C:" + hpr_str ,curr_t)
            self.lastHpr = hpr

        crossPos = self.crosshairNP.getPos()
        if (self.lastCrossHairPos != crossPos):
            crossPos_str = "[%.3f,%.3f,%.3f]\n" % (crossPos[0],crossPos[1],crossPos[2])
            self.replayLog.logEvent("T:" + crossPos_str ,curr_t)
            self.lastCrossHairPos = crossPos


        #for b in range(len(self.bullets)):
        #    np = self.bullets[b]
        #    if (np.getX() != 0):
        #        position = "[%d,%.7f,%.7f,%.7f]" % (b,np.getX(),np.getY(),np.getZ())
        #        self.replayLog.logEvent("B:"+position+"\n", curr_t)
        return Task.cont

    #=============================================

    def moveCannon(self, howmuch):
        """convert value howmuch to float and move the cannon that amount"""
        try:
          howmuch = float(howmuch)
        except:
          printOut("Error: Cannot convert value to float: %s" %howmuch, 0)
          howmuch = 0.0

        try:
            self._tempZ=self._tempZ+howmuch
        except:
            # we get here for an attribute error on _tempZ, therefore
            # _tempZ and _origZ don't exist !!
            self._tempZ=0.0
            self._origZ=self.cannonNP.getZ()

        printOut("adjusting Cannon Height to: %f" % (self._origZ+self._tempZ), 0)
        self.cannonNP.setZ( self._origZ + self._tempZ )

    def setupCannonKeys(self):
        """ some additional key bindings"""
        k = self.kbd

        keyValue={'j':[0],'j-up':[4],
                  'l':[1],'l-up':[5],
                  'i':[2],'i-up':[6],
                  'k':[3],'k-up':[7]}
        for key,value in keyValue.items():
            k.registerKey(key,self.arrowKey,"",False,value,False)
            self.event_keys.append(key)

        k.registerKey("w", self.shoot,"shoot!", False,[],False)
        self.event_keys.append("w")

    #=============================================
    def cleanUpKeys(self):
        #for k in self.event_keys:
        #    self.kbd.unregKey(k)
        pass

    def setupTargetsHUD(self):
        # this targuetGuideHUD goes into the HUD scene node
        self.targetGuideHUD = targetGuide( self.currSeq )
        nodePath = self.targetGuideHUD.targetsNP
        nodePath.reparentTo(self.hudNP)

        # next three targets (to prepare the random generation)
        self.nextThreeTargets = self.currSeq[0:3]
        # last target to verify if the current target has changed
        # recently
        self.lastTarget = 0
        # how many cycles have been shooting targets
        self.cyclesTargets = 0
        # current target in the sequence
        self.currentTarget = 0

    #=============================================

    def setupGame(self):
        """ sets the game basic elements """

        # when this object (Game) was constructed, some
        # default attributes were added automatically, such
        # as configuration values from Json and the World object.
        cam = self.world.camera

        # keys and interaction in the game
        self.mapkeys = [0, 0, 0, 0]

        # creates a Random position generator class helper
        # to generate new positions for the parachutes
        # left and right corners.
        # THIS IS VERY TIME CONSUMING TASK!, and should be implemented in C
        # OR REWRITTEN
        Ypos = cam.pos[1] + cam.parDistCam
        maxPar = self.jsonConfig.parachutes.simultaneous
        self.posGen = PositionGenerator(
                      topLeft=Vec3(cam.minX + cam.delta, Ypos, -cam.minZ),
                      topRight=Vec3(-cam.minX - cam.delta, Ypos, -cam.minZ),
                      memory=maxPar, world=self )

        # number of cycles after changing quality
        # self.cycles = 0

        # to start the timer immediately
        self.lastGetParT = -2

        # loads the 3d terrain (3d scene)
        self.setupTerrain()
        # generates ALL the parachutes, and some extra stuff
        self.setupParachutes()
        # activates particles in Panda
        base.enableParticles()
        # enables collisions
        if not self.isReplay:
            self.setupCollisions()
        # sets up the HUD for the targets
        self.setupTargetsHUD()
        # sets up the HUD for the points
        self.setupPointsHUD()
        # sets up the cannon
        self.setupCannon()
        # set up sounds for the game
        self.setupSounds()
        # set up mouse plane hitting test (for mouse aiming)
        self.setupMousePlaneHit()

        # hide the parent node of THIS ELEMENT (Game)
        # until it is used
        self.hideElement()

        # list of keys registered to unregister them at the end.
        self.event_keys = []

        # particle system for explosions
        self.nodeExplosions = NodePath("particlesExplosion")
        self.nodeExplosions.reparentTo(render)
        self.nodeExplosions.setBin("fixed", 0)
        #p.setDepthWrite(False)
        return

    #=============================================

    def setupMousePlaneHit(self):
        # sets up a plane to test hits against the mouse...
        # this is used to control the crosshair with the mouse.
        distance = self.jsonConfig.shooter.focusplane
        self.hitPlane = Plane(Vec3(0,1,0), Point3(0,distance,0))
        cm = CardMaker("hitting plane")
        cm.setFrame(-100,100,-100,100)
        self.sceneNP.attachNewNode(cm.generate()).lookAt(0,-1,0)


    def setupSounds(self):
        """
        Setup basic sounds, using the audio files described in the
        JSON config file
        """
        soundsCfg = self.jsonConfig.soundsConfig
        self.sndEnabled = soundsCfg.enabled
        if (not soundsCfg.enabled):
            return

        self.volume = soundsCfg.vol
        self.sounds = {}
        for s in soundsCfg.sounds:
            self.sounds[s.id] = loader.loadSfx(s.filename)
            self.sounds[s.id].setVolume(float(s.vol))
        return

    def playSound(self,snd):
        """
        basic function to play sounds based on a dictionary
        of sound objects.
        """
        if (self.sndEnabled):
          try:
            self.sounds[snd].play()
          except KeyError:
            printOut("Trying to play sound, unknown sound: %s"%snd,0)
            pass
          except Exception,e:
            printOut("Trying to play sound, unknown error",0)
            print e

    def setupPointsHUD(self):
        r = self.world.camera.ratio
        self.pointsHUD = pointsHUD(self.jsonConfig.pointsHUD,
                                   Vec3(-r+0.05,0,0.90))
        self.pointsHUD.getNP().reparentTo(self.hudNP)
        self.setPoints(0)

    #=============================================

    def setupCollisions(self):
        # setup basic collisions
        base.cTrav = CollisionTraverser('my-col-traverser')
        self.colHandlerEvent = CollisionHandlerEvent()
        self.colHandlerEvent.addInPattern('hit-%in')
        # show collisions as they happen
        # base.cTrav.showCollisions(render)
        return

    
    #=============================================
    # CHANGE HOW WE CONTROL THE CROSSHAIR
    #=============================================
    def setChByTracker(self):
        self.chController = 'tracker'
        taskMgr.remove("chController")
        # start tracking
        # self.world.tracker.track()
        taskMgr.add(self.crossHairTracker, "chController", sort=2)
        self.world.accept("mouse1", self.shoot,[])
        printOut("Adding task to control crosshair using the EyeTracker",0)

    def setChByKeyboard(self):
        self.chController = 'keyboard'
        taskMgr.remove("chController")
        taskMgr.add(self.crossHairKeyboard, "chController", sort=2)
        #self.world.ignore('mouse1-down')

    def setChByMouse(self):
        self.chController = 'mouse'
        taskMgr.remove("chController")
        taskMgr.add(self.crossHairMouse, "chController", sort=2)
        self.world.accept("mouse1", self.shoot,[])
    #=============================================

    def startGame(self):
        """
        starts the game loop
        """
        # put crosshair in the middle of the screen
        self.aimAtXY(0.0,0.0)
        # set cross hair controller (keyboard)
        shooter = self.jsonConfig.shooter
        if (shooter.control == 'keyboard'):
            self.setChByKeyboard()
        elif (shooter.control == 'mouse'):
            self.setChByMouse()
        elif (shooter.control == 'tracker'):
            self.setChByTracker()

        taskMgr.add(self.addParachutes, "addParachutes", sort=1)

        # this is going to call this function every frame.
        # so we check to avoid adding the task, but it not really
        # needed, since replayLog has dummy functions that log nothing
        # in case the logging is disabled.
        if (self.replayLog.logging):
            t = time.time()
            self.replayLog.startLog(t)
            taskMgr.add(self.logFrameTask, "logFrameTask", sort=5)

        self.setupCannonKeys()

        # start tracking
        self.world.tracker.track()
        return


    def aimAtXY(self,x,y):
        """Generic function that moves the chrosshairNP to
        the XY position on screen"""

        pos = Point2(x,y)
        pos3d = Point3()
        nearPoint = Point3()
        farPoint = Point3()
        base.camLens.extrude(pos, nearPoint, farPoint)
        if (self.hitPlane.intersectsLine(pos3d,
                              render.getRelativePoint(camera,nearPoint),
                              render.getRelativePoint(camera,farPoint))):

            #print "intersection at: ", pos3d
            self.crosshairNP.setX(pos3d.getX())
            # 5 is the limit to not go below the ground with the crosshair.
            self.crosshairNP.setZ(max(pos3d.getZ(),5.0))
            # set here the crosshair...

        # make X between [-1,1] approx
        normX = self.crosshairNP.getX() / 137
        newH = 180.0 - (normX * 40)
        self.cannon.setH(newH)
        # assume 45 degrees is the maximum Heading angle of the turret
        # make Z between [-1,1] approx
        normZ = self.crosshairNP.getZ() / 125
        newP = -normZ * 40
        self.cannon.setP(newP)
    #=============================================
    #=============================================
    # TASKS

    def crossHairMouse(self,task):
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            self.aimAtXY(mpos.x,mpos.y)
        return task.again

    def crossHairTracker(self,task):
        #printOut("at crosshairTracker",0)
        # sample is a (x,y) tuple
        sample = self.world.tracker.readGazeSample()
        # tracker.trackerWinSize is (X,Y,W,H)
        tws = self.world.tracker.trackerWinSize
        if sample:
            # map gaze sample to Panda screen coordinates
            # assume that both windows share the same top-left
            # origins (or full-screen)
            normSample = ((sample[0] / tws[2])*2 - 1, (sample[1] / tws[3])*2 - 1)
            self.lastEyeSample = normSample
            # INVERT Y coordinate because OpenFrameWorks uses different convention.
            self.aimAtXY(normSample[0], -normSample[1])
        else:
            print "sample is None!"
        return task.again
 
    def crossHairKeyboard(self, t):
        """
        updates cross hair and cannon using arrow keys
        """
        ts = time.time()
        hpr = self.cannon.getHpr()
        dt = t.time - self.lastCH
        self.lastCH = t.time
        s = self.crosshairSpeed

        # 0 is left, 2 is right,
        # 4 is up and 6 is down.

        #keyValue={'j':[0],'j-up':[4],'l':[1],
        #        'l-up':[5],'i':[2],'i-up':[6],
        #        'k':[3],'k-up':[7]}

        dx = -self.mapkeys[0]*s + self.mapkeys[1]*s
        dz = self.mapkeys[2]*s - self.mapkeys[3]*s

        if ((dx > 0 and hpr[0] > 135) or (dx < 0 and hpr[0] < 225)):
            self.crosshairNP.setX(self.crosshairNP.getX()+dx)
            # assume 45 degrees is the maximum Heading angle of the turret
            newH = 180.0 - (self.crosshairNP.getX() * 45 / 137)
            self.cannon.setH(newH)
            # CONDITIONAL LOG
            self.replayLog.logEvent("L:"+str(newH)+"\n",ts)
        if ((dz < 0 and hpr[1] < -5.0) or (dz > 0 and hpr[1] > -45)):
            self.crosshairNP.setZ(self.crosshairNP.getZ()+dz)
            # assume 45 degrees is the maximum Heading angle of the turret
            newP = -self.crosshairNP.getZ() * 45 / 125
            self.cannon.setP(newP)

            # CONDITIONAL LOG
            self.replayLog.logEvent("M:"+str(newP)+"\n",ts)
        return Task.cont

    def addParachutes(self, t):
        """this is the most consuming task of the game, which
        tries to generate random positions but keeping with high
        priority the target parachutes, so there are ALWAYS some
        targets to shoot at and the user doesn't have time to look
        at the other parachutes"""

        dt = t.time - self.lastGetParT
        # check EVERY SECOND
        if (dt < 1):
            return Task.cont

        self.lastGetParT = t.time

        needNoMoreTargets = []
        # determine which of the next three targets need a replacement now
        for n in self.nextThreeTargets:
            coveredBy = None
            candidates= []
            for k,v in self.targets.items():
                if (n in k and not v.falling):
                    candidates.append(k)
                else:
                    if ((n in k) and (k not in needNoMoreTargets)):
                        pos = v.modelNP.getPos()
                        if (v.falling and pos.getZ() > 70.0):
                            needNoMoreTargets.append(k)
                            coveredBy = (k,v)
                            break
            if (coveredBy == None and len(candidates)>0):
                if (self.targets[candidates[0]].newPos(0) == 1):
                    self.targets[candidates[0]].start()
            if (len(needNoMoreTargets) == 3): break

        counter = 0
        ky = self.non_targets.keys()
        shuffle(ky)
        active = 0

        for a in self.non_targets.values():
            if (a.falling): active+=1

        for k in ky[0:5 - len(needNoMoreTargets)]:
            if (active > 3*self.non_targets_cnt):
                return Task.cont

            t = self.non_targets[k]
            if (not t.falling):
                r = t.newPos(0)
                if (r==1):
                    t.start()
                    active+=1

        return Task.cont

    #=============================================

    def validHit(self,par_name):
        """ is the par_name parachute the next target (color) in the targetGuideHUD """
        validColor = self.currSeq[self.currentTarget]
        if (validColor not in par_name):
            self.addPoints(-10)
            return False
        else:
            # log for replay
            if (self.replayLog):
                ts = time.time()
                self.replayLog.logEvent("H:[\'"+par_name+"\']\n",ts)

            # good hit, advance arrow
            self.targetGuideHUD.advanceArrow()
            self.replayLog.logEvent("A: %d\n" % self.targetGuideHUD.currentTarget, ts)
            self.addPoints(15)

            newTarget = (self.currentTarget+1) % len(self.currSeq)
            # nextThreeTargets
            ntt = self.currSeq[newTarget:newTarget+3]
            # did we wrap around??
            l = len(ntt)
            if (l<3):
                ntt += self.currSeq[0:3-l]
            self.nextThreeTargets = ntt

            # new cycle ??
            if (newTarget is 0):
                self.cyclesTargets += 1
                c = CycleEvent(self.cyclesTargets)
                self.lodManager.notify(c)

            self.lastTarget = self.currentTarget
            self.currentTarget = newTarget
            return True

    #=============================================

    def setPoints(self, points):
        self.points = points
        self.pointsHUD.setPoints(points)

    #=============================================

    def addPoints(self, points):
        self.points += points
        self.pointsHUD.setPoints(self.points)

    #=============================================

    def getParachutesPositions(self, type_par='targets'):
        """returns a list of 3d positions with all targets positions
           in a particular instant"""
        temp = self.targets.items()
        if type_par == 'non_targets':
            temp = self.non_targets.items()
        if type_par == 'all':
            temp += self.non_targets.items()

        result = []
        for k, v in temp:
            result.append(v.modelNP.getPos())
        return result

    #=============================================

    # PARTICLES SETUP
    def createCannonExp(self):
        p = ParticleEffect()
        p.loadConfig(Filename(self.cannonParticle))
        p.setPos(100, -100, 0)
        # draw last!
        p.setBin("fixed", 10)
        p.setDepthWrite(False)
        return p

    #=============================================

    def createExplosion(self):
        p = ParticleEffect()
        p.loadConfig(Filename(self.explosionParticle))
        p.setPos(0, 0, -1)
        # draw last!
        #p.setBin("fixed", 0)
        p.setDepthWrite(False)
        return p

    #=============================================
    # CANNON RELATED
    def setupCannon(self):
        """ Sets up cannon 3d model, bullets models, crossHair model,
        a task to update the crossHair"""

        shooter = self.jsonConfig.shooter

        # to keep track of time for the task
        # that updates crossHair
        self.lastCH = 0

        cannonNP = NodePath('cannonNP')
        cannonNP.reparentTo(self.sceneNP)

        # distance from cannon to parachutes in 3d
        distance = shooter.focusplane

        # crossHair size, speed, texture
        self.bulletSize = shooter.bulletSize
        self.bulletTime = shooter.bulletTime
        self.explosionParticle = shooter.explosionParticle
        self.cannonParticle = shooter.cannonParticle

        # controls which cannon of the two available shoots.
        self.tip0 = True
        self.cannon = loader.loadModel(shooter.cannonModel)
        self.cannon.reparentTo(cannonNP)
        #self.cannon.reparentTo(gamePlay3dNode)

        # position the cannon relative to camera position
        self.cannon.setScale(0.2)

        # this is trial an error for different resolutions, to get
        # the cannon in a nice place.
        Y = float(shooter.cannonPosY)
        Z = float(shooter.cannonPosZ)

        self.cannon.setPos(camera.getPos() + Vec3(0, Y, Z))
        # position to match initial pos of the crosshair
        # TODO - fix these constants!
        self.cannon.setHpr(180, -4.68, 0)
        self.lastHpr = self.cannon.getHpr()

        self.cannonTip0 = NodePath("tip0")
        self.cannonTip0.reparentTo(self.cannon)
        # relative positions - TODO - fix with blender
        self.cannonTip0.setPos(0.6, -4, 1.3)

        self.cannonTip1 = NodePath("tip1")
        self.cannonTip1.reparentTo(self.cannon)
        # relative positions - TODO - fix with blender
        self.cannonTip1.setPos(-0.6, -4, 1.4)

        self.cannonSmokeNP = NodePath("smokeNP")
        self.cannonSmokeNP.reparentTo(self.cannon)

        self.bullets=[]
        for i in range(shooter.bulletSet):

            bulletNP = loader.loadModel(shooter.bullet)
            bulletNP.node().setName("bulletNode_"+str(i))
            bulletNP.setScale(self.bulletSize)
            bulletNP.setName("bulletNP_"+str(i))
            bulletNP.setColor(0.1,0.1,0.1)

            if not self.isReplay:
                # collision sphere solid attached to the node
                # the sphere is a bit ahead of the bullet
                # the radious will change the difficulty
                colSolid = CollisionSphere(0, 5, 0, 3.0)
                colNP = bulletNP.attachNewNode(
                        CollisionNode('ColNodeBullet_'+str(i)))

                colNP.node().addSolid(colSolid)
                colNP.node().setFromCollideMask(BitMask32(0x80))

                bulletNP.setCollideMask(BitMask32(0x0))

                base.cTrav.addCollider(colNP, self.colHandlerEvent)

            self.bullets.append(bulletNP)
            self.bullets[-1].reparentTo(cannonNP)

        self.bulletIdx=0
        self.maxbullets=shooter.bulletSet

        t = loader.loadTexture(shooter.crosshair)
        t.setMinfilter(Texture.FTLinearMipmapLinear)
        #t.setAnisotropicDegree(2)

        self.crosshairNP = loader.loadModel("Elements/Game/models/plane")
        self.crosshairNP.setPos(0, distance, 10)
        self.crosshairNP.setScale(shooter.scaleCH)
        self.crosshairNP.setTransparency(1)
        self.crosshairNP.setTexture(t)

        self.crosshairNP.reparentTo(cannonNP)
        self.crosshairSpeed = shooter.speedCH
        self.lastCrossHairPos = self.crosshairNP.getPos()
        self.cannonNP = cannonNP

    #=============================================

    def shoot(self):
        # get timestamp
        ts = time.time()
        self.replayLog.logEvent("S\n", ts)

        # switch from where the bullet starts, tip0 or tip1
        if (self.tip0):
            fromNode = self.cannonTip0
        else:
            fromNode = self.cannonTip1
        self.tip0 = not self.tip0

        # create a smoke effect on the tip of the cannon
        cannonSmoke = self.createCannonExp()
        cannonSmoke.reparentTo(self.cannonSmokeNP)
        cannonSmoke.setScale(3.5, 3.5, 3.5)
        cannonSmoke.setPos(0, -7, 0)
        cannonSmoke.start(self.cannonSmokeNP)
        # schedule the removal of the nodePath containing the smoke
        taskMgr.doMethodLater(0.8, cannonSmoke.removeNode,
                              'clearSmoke', extraArgs=[])

        # advance in the pool of bullets
        idx=self.bulletIdx%self.maxbullets
        self.bullets[idx].setScale(self.bulletSize)
        self.bullets[idx].show()
        ##self.bullets[idx].setScale(2.0 / 10.0)
        ##self.bullets[idx].setScale(0.1)

        # build projectile interval of the bullet
        proj = ProjectileInterval(self.bullets[idx],
                     startPos=fromNode.getPos(self.sceneNP),
                     endPos=(self.crosshairNP.getPos() + Vec3(0, 1, 0)),
                     gravityMult=1.0,
                     duration=self.bulletTime)

        # this is to make the ball like the size of the cannon, and then
        # enlarge it a bit so it doesn't appear too small at distance
        resizeBullet = self.bullets[idx].scaleInterval(self.bulletTime, 1.4)

        # event handling to hide the ball
        event = "hideball"+str(idx)
        proj.setDoneEvent(event)

        #p.reparentTo(self.bullets[idx])
        #p.start(self.bullets[idx])

        proj.acceptOnce(event, self.hideAndRemoveBullet, [self.bullets[idx]])

        self.bulletIdx+=1
        proj.start()
        resizeBullet.start()

        # shoot sound
        self.playSound("shoot")
        return

    #=============================================

    def hideAndRemoveBullet(self, node):
        """
        node is the bullet node p is the particle explosion node
        this gets executed when the bullet finishes the trajectory
        """
        p = self.createExplosion()
        p.reparentTo(self.explosionParticle)

        p.setScale(13, 13, 13)
        p.setPos(node.getPos() + Vec3(0, -10, 0))
        p.start(self.sceneNP)

        taskMgr.doMethodLater(0.8, p.cleanup, 'hideFire', extraArgs=[])

        node.hide()
        node.setPos(-10000, -10000, -10000)

        self.playSound("explosion")
        return

    #=============================================

    def arrowKey(self, key):
        """ numbers are mapped from the numeric keypad """
        # even numbers, pressed key!
        if (key < 4):
            self.mapkeys[key] = 1
        else:
            self.mapkeys[key-4] = 0

        if (self.replayLog.logging):
            # get time stamp
            ts = time.time()
            state = "K:" + str(self.mapkeys) + "\n"
            self.replayLog.logEvent(state, ts)

        return

    #=============================================