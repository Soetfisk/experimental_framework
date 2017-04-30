from time import ctime

# game imports
from targetGuide import targetGuide
from pointsHUD import pointsHUD
from Parachute import *
from Elements.Element.Element import *

from Utils.Debug import printOut

try:
    import json
except ImportError:
    import simplejson as json


class Game(Element):
    """class to implement game and replay functionality
       It has still some dependencies with the World class,
       for the keyboard and for the Camera which I should separate
       in classes"""

    def __init__(self, **kwargs):
        """by default is play mode, and no replay log file"""
        # this sets all the attributes specified in the generic JSON
        super(Game, self).__init__(**kwargs)
        #self.isReplay = self.className == 'Replay'
        self.isReplay = False

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
        rl = getattr(self.config, 'saveReplay', 'nolog,w')
        self.replayLog = Logger(self.baseTime, rl[0], 'w')
        # creating logger for the game
        # the string will look like "filename,mode"
        gl = getattr(self.config, 'logFile', 'nolog,a')
        self.gameLog = Logger(self.baseTime, gl[0], 'a')

    def readUserData(self):
        pass
        # Uses a service provided by DataForm.
        # Its a simple service registered by the name 'UserData' that
        # returns the input in the form.
        # We will use it in a blocking call here, so no need for a callback.
        # TODO
        # service = self.config.world.serviceMgr.getService('UserData')
        #if service:
        #    userData = service.service()
        #else:
        #    userData = None
        # this can be None or the Dictionary, depending if the user already
        # entered the data
        #return userData

    #=============================================
    def startLogging(self):
        #self.gameLog.startLog()
        self.gameLog.logEvent("==== new game participant ====\n")

        # process user data if present (from a previous form)
        #if self.userData:
        #    for k, v in self.userData.items():
        #        self.gameLog.logEvent("== UI ==  %s: %s\n" % (k, v), t)

        self.gameLog.logEvent("date: " + ctime() + "\n")
        self.gameLog.logEvent("game start\n")

    #=============================================
    def stopLogging(self):
        self.gameLog.stopLog()
        self.replayLog.stopLog()

    #=============================================
    def setupTerrain(self):
        """Sets terrain model, attaching it to the scene nodepath"""
        # transform to position the ground model
        self.groundTransform = NodePath("groundTransform")
        self.groundTransform.setHpr(130, 7, 7)
        # ground model
        self.ground = loader.loadModel("Elements/Game/models/terrain/master")
        self.ground.setPos(213, -179, -5)
        self.ground.reparentTo(self.groundTransform)
        # ground model is only shown in the gamePlay tree.
        self.groundTransform.reparentTo(self.sceneNP)
        return

    #=============================================
    # DEBUGING PURSPOSES -- I WANT A GUI!!!
    def moveGround(self, axis, amount):
        pos = self.ground.getPos()
        pos[axis] += amount
        self.ground.setPos(pos[0], pos[1], pos[2])
        print pos

    def rotate(self, amount):
        self.groundTransform.setH(self.groundTransform.getH() + amount)
        print "Heading: " + str(self.groundTransform.getH())

    #==============================================

    def setupParachutes(self):
        """Creates parachutes objects needed for the game, loads textures and all..."""
        # references to all the Parachute objects created
        # actual Parachutes objects
        self.parachutes = {}  # dict of parachute objects
        self.parachutesFalling = {}

        # bad guys (just names)
        self.targets = []  # parachutes that are targets
        # good guys (just names)
        self.non_targets = []  # parachutes that are no targets.

        # load sequences
        # references to the sequences in the config file
        #self.seqs = {}          # sequences by id.
        #try:
        #    sequences = self.config.targetSequences.sequences
        #    for s in sequences:
        #        self.seqs[s.id] = map(str.upper, map(str, s.seq))
        #    self.currSeq = self.seqs[self.config.targetSequences.use]
        #except Exception, e:
        #    print "Error loading target sequence from JSON file"
        #    print e
        #    sys.exit()

        # creates LOD manager (implements Observer pattern)
        # lm = LodManager()
        # gets the different LOD events that should be considered
        # lodEvents = self.config.LODEvents.lodEvents
        #for l in lodEvents:
        #    try:
        #        handler = getattr(lm, l.handler)
        #        lm.registerHandler(l.evtType, handler, l)
        #        printOut("registering %s\n" % l.evtType, 1)
        #    except:
        #        print "Trying to register a non-existent handler, check JSON gameConfig and LodManager class"

        parConfNode = self.config.parachutes

        for id0, color in enumerate(parConfNode.targets):
            for id1, q in enumerate(parConfNode.targetsQ):
                badGuy = parConfNode.texturePrefix + str(q) + parConfNode.texturePostfix
                # take the color name, but without the last two chars "_1"
                badGuy = badGuy.replace("Color", color)
                # add unique id per color and quality
                pos = badGuy.rfind("/") + 1
                uniqueName = badGuy[pos:]
                uniqueName = str(id0) + "." + str(id1) + "." + uniqueName
                # remove the prefix with the path

                self.targets.append(uniqueName)
                obj = Parachute(world=self, name=uniqueName, textureName=badGuy,
                                conf=parConfNode, collisions=True)
                obj.modelNP.reparentTo(self.sceneNP)
                obj.isTarget = True
                obj.ignoreHit = False
                self.parachutes[uniqueName] = obj

        for id0, color in enumerate(parConfNode.nonTargets):
            for id1, q in enumerate(parConfNode.nonTargetsQ):
                goodGuy = parConfNode.texturePrefix + str(q) + parConfNode.texturePostfix
                # take the color name, but without the last two chars "_1"
                goodGuy = goodGuy.replace("Color", color)
                pos = goodGuy.rfind("/") + 1
                uniqueName = goodGuy[pos:]
                uniqueName = str(id0) + "." + str(id1) + "." + uniqueName

                self.non_targets.append(uniqueName)
                obj = Parachute(world=self, name=uniqueName, textureName=goodGuy,
                                conf=parConfNode, collisions=True)
                obj.modelNP.reparentTo(self.sceneNP)
                obj.isTarget = False
                obj.ignoreHit = True
                self.parachutes[uniqueName] = obj

                #targetnames = self.currSeq  # target names

                # how many parachutes of each color, based on the max
                #each = int(ceil(float(parachutesCount) / len(parConfNode.parachutes.names)) )
                # check that 1 of each of the next 3 targets exists in upper
                # third of the screen
                #self.centerFirstThird = (-2*self.config.world.camera.minZ)/3.0
                #self.firstThirdSize = self.centerFirstThird

                #self.non_targets_cnt = []

                #
                #for color in parConfNode.names:

                #    levels = parConfNode.textures.levels
                #    for l in levels:

                #for i in range(6):
                # only 2 of each non-target
                #        if (i > 2 and color not in targetnames):
                #            pass
                #        nameId = color + "_" + str(i)
                # creates parachute object
                #        obj = Parachute(nameId, p, self, self.posGen, falltime, parConfNode.scale, not self.isReplay)

                #        obj.modelNP.reparentTo(self.sceneNP)
                #        self.parachutes[nameId] = obj

                # improve this registration on events
                #        lm.register(obj, ["CYCLE"])

                #        if (color not in targetnames):
                #            obj.isTarget = False
                #            obj.ignoreHit = True
                #            self.non_targets[nameId] = obj
                #            if (color not in self.non_targets_cnt):
                #                self.non_targets_cnt.append(color)
                #        else:
                #            self.targets[nameId] = obj
                #            obj.isTarget = True
                #            obj.ignoreHit = False

                # DON'T NEED THE LIST ANYMORE!, just replace it with length.
                #self.non_targets_cnt = len(self.non_targets_cnt)
                #self.lodManager = lm

    #=============================================

    def enterState(self):
        # call super first
        Element.enterState(self)

        rescale = self.rescaleFactor
        print rescale
        for p in self.parachutes.values():
            p.modelNP.setScale(rescale)

        # try and read user data from the form.
        # example of a blocking call
        #self.userData = self.readUserData()
        #printOut("From GAME, just read user data from the form",1)
        #printOut(str(self.userData),1)

        # as we need to wait for the async call, we have to start
        # the logging in the callback.
        self.startLogging()

        # eyeTracker task
        self.lastEyeSample = None
        #self.config.world.tracker.connect()

    #=============================================


    def exitState(self):
        # call super first
        Element.exitState(self)
        # specifics
        self.stopLogging()
        # remove all tasks!!!
        taskMgr.remove("addParachutes")
        self.sceneNP.hide()
        self.hudNP.hide()
        #self.sceneNP.removeNode()
        #self.hudNP.removeNode()

        #self.config.world.tracker.stopTrack()
        #taskMgr.remove("readTrackerGaze")

    #=============================================

    def logFrameTask(self, t):
        """logs all the positions of parachutes, cannon and ball so the game
        can be reproduced or played back at any speed forward and backward."""

        if self.lastEyeSample:
            eyesample = "[%.3f,%.3f]\n" % (self.lastEyeSample[0], self.lastEyeSample[1])
            self.replayLog.logEvent("E:" + eyesample)

        # grab all parachutes (name,value) and save their position
        for p_name, par in self.parachutes.items():
            np = par.modelNP
            if (np.getX() != -1000 and par.hitted == False ):
                position = "[\'%s\',%.3f,%.3f,%.3f]\n" % (p_name, np.getX(), np.getY(), np.getZ())
                self.replayLog.logEvent("P:" + position)
        # grab heading and pitch of the cannon
        hpr = self.cannon.getHpr()
        if (self.lastHpr != hpr):
            hpr_str = "[%.3f,%.3f]\n" % (hpr[0], hpr[1])
            self.replayLog.logEvent("C:" + hpr_str)
            self.lastHpr = hpr

        crossPos = self.crosshairNP.getPos()
        if (self.lastCrossHairPos != crossPos):
            crossPos_str = "[%.3f,%.3f,%.3f]\n" % (crossPos[0], crossPos[1], crossPos[2])
            self.replayLog.logEvent("T:" + crossPos_str)
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
            printOut("Error: Cannot convert value to float: %s" % howmuch, 0)
            howmuch = 0.0

        try:
            self._tempZ = self._tempZ + howmuch
        except:
            # we get here for an attribute error on _tempZ, therefore
            # _tempZ and _origZ don't exist !!
            self._tempZ = 0.0
            self._origZ = self.cannonNP.getZ()

        printOut("adjusting Cannon Height to: %f" % (self._origZ + self._tempZ), 0)
        self.cannonNP.setZ(self._origZ + self._tempZ)

    def setupCannonKeys(self):
        """ some additional key bindings"""
        k = self.kbd

        keyValue = {'j': [0], 'j-up': [4],
                    'l': [1], 'l-up': [5],
                    'i': [2], 'i-up': [6],
                    'k': [3], 'k-up': [7]}
        for key, value in keyValue.items():
            k.registerKey(key, self.config.name, self.arrowKey, "", False, value, False)
            self.registeredKeys.append(key)

        k.registerKey("w", self.config.name, self.shoot, "shoot!", False, [], False)
        self.registeredKeys.append("w")

    #=============================================
    def setupTargetsHUD(self):
        # this targuetGuideHUD goes into the HUD scene node

        # unique list
        bad = list(set(self.config.parachutes.targets))
        bad = map(str.upper, bad)
        self.targetGuideHUDLeft = targetGuide(bad, 'left',
                                              self.config.parachutes.targetsLabel)

        self.targetGuideHUDLeft.targetsNP.reparentTo(self.hudNP)

        good = list(set(self.config.parachutes.nonTargets))
        good = map(str.upper, good)
        self.targetGuideHUDRight = targetGuide(good, 'right',
                                               self.config.parachutes.nonTargetsLabel)
        self.targetGuideHUDRight.targetsNP.reparentTo(self.hudNP)

        # self.targetGuideHUD = targetGuide( self.currSeq )

        # nodePath = self.targetGuideHUD.targetsNP
        # nodePath.reparentTo(self.hudNP)

        # next three targets (to prepare the random generation)
        # self.nextThreeTargets = self.currSeq[0:3]
        # last target to verify if the current target has changed
        # recently
        # self.lastTarget = 0
        # how many cycles have been shooting targets
        # self.cyclesTargets = 0
        # current target in the sequence
        # self.currentTarget = 0

    #=============================================

    def setupGame(self):
        """ sets the game basic elements """

        # when this object (Game) was constructed, some
        # default attributes were added automatically, such
        # as configuration values from Json and the World object.
        cam = self.config.world.camera

        # keys and interaction in the game
        self.mapkeys = [0, 0, 0, 0]


        # director vector from camera to lookAt point
        #camLookAt = Vec3(cam.lookAt[0]-cam.pos[0],
        #                 cam.lookAt[1]-cam.pos[1],
        #                 cam.lookAt[2]-cam.pos[2])
        # camLookAt.normalize()
        # director vector scaled up to reflect the distance from
        # the camera to the plane where Parachutes are falling
        # camLookAt = camLookAt * self.config.parDistCam
        # creates a Random position generator class helper
        # to generate new positions for the parachutes
        # left and right corners.
        # THIS IS VERY TIME CONSUMING TASK!, and should be implemented in C
        # OR REWRITTEN

        # field of view in RADIANS
        fovRads = (cam.fov * pi / 180.0)
        # HIPOTHENUSE of the triangle from camera to parDistCam
        hip = self.config.parDistCam / cos(fovRads / 2)
        # Minimum X value within the viewing volume
        minX = -hip * sin(fovRads / 2.0)
        minZ = cam.ratio - hip * sin(fovRads / 2.0)

        Ypos = cam.pos[1] + self.config.parDistCam
        maxPar = self.config.parachutes.simultaneous
        self.posGen = PositionGenerator(
            topLeft=Vec3(minX, Ypos, -minZ),
            topRight=Vec3(-minX, Ypos, -minZ),
            memory=maxPar, world=self)

        # number of cycles after changing quality
        self.cycles = 0

        # start the timer as soon as the game starts, but the
        # parachutes will delay a bit to show up on the screen.
        self.lastGetParT = - self.config.parachutes.fallDelay

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
        # self.nodeExplosions = NodePath("particlesExplosion")
        # self.nodeExplosions.reparentTo(render)
        # self.nodeExplosions.setBin("fixed", 0)
        ## p.setDepthWrite(False)

        self.currController = 0
        self.controllers = [self.setChByKeyboard,
                            self.setChByMouse,
                            self.setChByTracker]

        # try to read pointsToEnd the game, if not set then
        # set it to 200 points and finish.
        if getattr(self.config, 'pointsToEnd', None) is None:
            self.config['pointsToEnd'] = 200
        self.finishGame = False
        return

    #=============================================

    def setupMousePlaneHit(self):
        # sets up a plane to test hits against the mouse...
        # this is used to control the crosshair with the mouse.
        distance = self.config.shooter.focusplane
        self.hitPlane = Plane(Vec3(0, 1, 0), Point3(0, distance, 0))
        cm = CardMaker("hitting plane")
        cm.setFrame(-100, 100, -100, 100)
        self.sceneNP.attachNewNode(cm.generate()).lookAt(0, -1, 0)

    def setupSounds(self):
        """
        Setup basic sounds, using the audio files described in the
        JSON config file
        """
        soundsCfg = self.config.soundsConfig
        self.sndEnabled = soundsCfg.enabled
        if (not soundsCfg.enabled):
            return

        self.volume = soundsCfg.vol
        self.sounds = {}
        for s in soundsCfg.sounds:
            self.sounds[s.id] = loader.loadSfx(s.filename)
            self.sounds[s.id].setVolume(float(s.vol))
        return

    def playSound(self, snd):
        """
        basic function to play sounds based on a dictionary
        of sound objects.
        """
        if (self.sndEnabled):
            try:
                self.sounds[snd].play()
            except KeyError:
                printOut("Trying to play sound, unknown sound: %s" % snd, 0)
                pass
            except Exception, e:
                printOut("Trying to play sound, unknown error", 0)
                print e

    def setupPointsHUD(self):
        r = self.config.world.camera.ratio
        self.pointsHUD = pointsHUD(self.config.pointsHUD,
                                   Vec3(-r + 0.05, 0, 0.90))
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
    def changeCrossHairControl(self):
        """
        Wraps around the existing cross hair controllers in the list self.controllers
        :return:
        """
        self.currController = (self.currController + 1) % len(self.controllers)
        self.controllers[self.currController]()

    def setChByTracker(self):
        self.chController = 'tracker'
        taskMgr.remove("chController")
        taskMgr.add(self.crossHairTracker, "chController", sort=2)
        self.config.world.accept("mouse1", self.shoot, [])
        printOut("Adding task to control crosshair using the EyeTracker", 0)

    def setChByKeyboard(self):
        self.chController = 'keyboard'
        taskMgr.remove("chController")
        taskMgr.add(self.crossHairKeyboard, "chController", sort=2)
        printOut("Adding task to control crosshair using the keyboard", 0)
        #self.config.world.ignore('mouse1-down')

    def setChByMouse(self):
        self.chController = 'mouse'
        taskMgr.remove("chController")
        taskMgr.add(self.crossHairMouse, "chController", sort=2)
        self.config.world.accept("mouse1", self.shoot, [])
        printOut("Adding task to control crosshair using the mouse", 0)

    #=============================================

    def startGame(self):
        """
        starts the game loop
        """
        # put crosshair in the middle of the screen
        self.aimAtXY(0.0, 0.0)
        # set cross hair controller (keyboard)
        shooter = self.config.shooter

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
        #if (self.replayLog.logging):
        #    t = time.time()
        #    self.replayLog.startLog(t)
        #    taskMgr.add(self.logFrameTask, "logFrameTask", sort=5)

        self.setupCannonKeys()

        # start tracking
        # self.config.world.tracker.track()
        return


    def aimAtXY(self, x, y):
        """Generic function that moves the chrosshairNP to
        the XY position on screen and rotates the cannon
        accordingly"""

        # where is the cross hair on the screen
        messenger.send('crossHair',sentArgs=[(x,y)])
        pos = Point2(x, y)
        pos3d = Point3()

        # frustrum points
        nearPoint = Point3()
        farPoint = Point3()
        base.camLens.extrude(pos, nearPoint, farPoint)
        if (self.hitPlane.intersectsLine(pos3d,
                                         render.getRelativePoint(camera, nearPoint),
                                         render.getRelativePoint(camera, farPoint))):
            #print "intersection at: ", pos3d
            self.crosshairNP.setX(pos3d.getX())
            # 5 is the limit to not go below the ground with the crosshair.
            self.crosshairNP.setZ(max(pos3d.getZ(), -45.0))
            #self.crosshairNP.setZ(pos3d.getZ())
            # print self.crosshairNP.getZ()
            # set here the crosshair...

        # make X between [-1,1] approx
        normX = self.crosshairNP.getX() / 140.0
        newH = 180.0 - (normX * 40)
        self.cannon.setH(newH)

        # assume 45 degrees is the maximum Heading angle of the turret
        # make Z between [-1,1] approx
        #print "Z:" + str(self.crosshairNP.getZ())
        normZ = (self.crosshairNP.getZ() + 45.0) / (80.0 + 45.0)
        #print "normZ:" + str(normZ)
        newP = -normZ * 25.0
        self.cannon.setP(newP)
        #self.cannon.setP(0)

    #=============================================
    #=============================================
    # TASKS

    def crossHairMouse(self, task):
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            self.cursorX, self.cursorY = mpos
            self.aimAtXY(mpos.x, mpos.y)
        return task.again

    def crossHairTracker(self, task):
        try:
            # read samples from the eyetracker -- returns a LIST of TUPLES
            samples = self.config.eyeTracker.readGaze(5)
            avgx = sum([x[0][0] for x in samples]) / 5
            avgy = sum([y[0][1] for y in samples]) / 5
            print avgx, avgy
            self.aimAtXY( avgx * 2.0 - 1.0, avgy * -2.0 + 1.0 )
            return task.again
        except AttributeError,e:
            if getattr(self.config,"eyeTracker",True):
                # TRUE IF IT DOES NOT EXIST
                self.setChByMouse()
                return task.done
        except Exception,e:
            print e,
            return task.again

    def crossHairKeyboard(self, t):
        """
        updates cross hair and cannon using arrow keys
        """
        #ts = time.time()
        #hpr = self.cannon.getHpr()
        #dt = t.time - self.lastCH
        #self.lastCH = t.time
        s = self.crosshairSpeed

        # 0 is left, 2 is right,
        # 4 is up and 6 is down.

        #keyValue={'j':[0],'j-up':[4],'l':[1],
        #        'l-up':[5],'i':[2],'i-up':[6],
        #        'k':[3],'k-up':[7]}

        dx = (-self.mapkeys[0] * s + self.mapkeys[1] * s)
        dz = (self.mapkeys[2] * s - self.mapkeys[3] * s)

        self.cursorX = min(1, max(self.cursorX + dx, -1.0))
        self.cursorY = min(1, max(self.cursorY + dz, -0.55))
        self.aimAtXY(self.cursorX, self.cursorY)
        return Task.cont

    #        if ((dx > 0 and hpr[0] > 135) or (dx < 0 and hpr[0] < 225)):
    #            self.crosshairNP.setX(self.crosshairNP.getX()+dx)
    #            # assume 45 degrees is the maximum Heading angle of the turret
    #            newH = 180.0 - (self.crosshairNP.getX() * 45 / 137)
    #            self.cannon.setH(newH)
    #            # CONDITIONAL LOG
    #            self.replayLog.logEvent("L:"+str(newH)+"\n",ts)
    #        if ((dz < 0 and hpr[1] < 15.0) or (dz > 0 and hpr[1] > -45)):
    #            self.crosshairNP.setZ(self.crosshairNP.getZ()+dz)
    #            # assume 45 degrees is the maximum Heading angle of the turret
    #            newP = -self.crosshairNP.getZ() * 45 / 180
    #            self.cannon.setP(newP)
    #
    #            # CONDITIONAL LOG
    #            self.replayLog.logEvent("M:"+str(newP)+"\n",ts)
    #        return Task.cont

    def addParachutes(self, t):
        """this is the most consuming task of the game, which
        tries to generate random positions but keeping with high
        priority the target parachutes, so there are ALWAYS some
        targets to shoot at and the user doesn't have time to look
        at the other parachutes"""

        if self.finishGame:
            # returning will stop the task
            return

        dt = t.time - self.lastGetParT
        # run this method only ONCE EVERY SECOND
        if (dt < 0.5):
            return Task.cont

        self.lastGetParT = t.time

        # check if there are parachutes that WERE falling and
        # they are not falling anymore, so move them to the list
        # of available parachutes.
        toRemove = []
        for p, v in self.parachutesFalling.items():
            if v.falling:
                continue
            else:
                self.parachutes[p] = v
                toRemove.append(p)
        for p in toRemove:
            del (self.parachutesFalling[p])
        # FROM THIS POINT, each parachute is the right Dictionary.


        # list of parachutes for which I have found a free position
        willStartFallingNow = []

        for p, v in self.parachutes.items():
            # starting position is always above the camera
            # for 250.0 of pardistcam, with +85 in Z we can
            # hide it

            # try 10 times to find a position for each parachute
            found = False
            for i in range(1, 10):
                if found:
                    break
                pos = Vec3(randint(-100, 100), self.config.parDistCam, randint(80, 100))
                for fv in \
                                self.parachutesFalling.values() + willStartFallingNow:
                    if (pos - fv.modelNP.getPos()). \
                            lengthSquared() < (40 * 40):
                        # finding ONE is enough
                        break
                else:
                    # Found a spot which is distant enough from
                    # the other falling (or to fall) parachutes.
                    found = True
                    v.newPos(x=pos[0], y=pos[1], z=pos[2], forced=True)
                    willStartFallingNow.append(v)

        for w in willStartFallingNow:
            self.parachutesFalling[w.name] = w
            del (self.parachutes[w.name])
            w.start()

        return Task.cont

    #        for n in self.nextThreeTargets:
    #            coveredBy = None
    #            candidates= []
    #            for k,v in self.targets.items():
    #                if (n in k and not v.falling):
    #                    candidates.append(k)
    #                else:
    #                    if ((n in k) and (k not in needNoMoreTargets)):
    #                        pos = v.modelNP.getPos()
    #                        if (v.falling and pos.getZ() > 70.0):
    #                            needNoMoreTargets.append(k)
    #                            coveredBy = (k,v)
    #                            break
    #            if (coveredBy == None and len(candidates)>0):
    #                if (self.targets[candidates[0]].newPos(0) == 1):
    #                    self.targets[candidates[0]].start()
    #            if (len(needNoMoreTargets) == 3): break
    #
    #        counter = 0
    #        ky = self.non_targets.keys()
    #        shuffle(ky)
    #        active = 0
    #
    #        for a in self.non_targets.values():
    #            if (a.falling): active+=1
    #
    #        for k in ky[0:5 - len(needNoMoreTargets)]:
    #            if (active > 3*self.non_targets_cnt):
    #                return Task.cont
    #
    #            t = self.non_targets[k]
    #            if (not t.falling):
    #                r = t.newPos(0)
    #                if (r==1):
    #                    t.start()
    #                    active+=1
    #
    #        return Task.cont
    #=============================================

    def validHit(self, par_name):
        """ is the par_name parachute the next target (color) in the targetGuideHUD """
        if par_name not in self.targets:
            self.addPoints(-10)
            return False

            #validColor = self.currSeq[self.currentTarget]
            #if (validColor not in par_name):
            #    return False
            #else:
            # log for replay

        if self.replayLog:
            self.replayLog.logEvent("H:[\'" + par_name + "\']\n")
            # good hit, advance arrow
            # self.targetGuideHUD.advanceArrow()
            #self.replayLog.logEvent("A: %d\n" % self.targetGuideHUD.currentTarget, ts)

        self.addPoints(15)
        return True

        #newTarget = (self.currentTarget+1) % len(self.currSeq)
        # nextThreeTargets
        # ntt = self.currSeq[newTarget:newTarget+3]
        # did we wrap around??
        # l = len(ntt)
        #if (l<3):
        #    ntt += self.currSeq[0:3-l]
        #self.nextThreeTargets = ntt

        # new cycle ??
        #if (newTarget is 0):
        #    self.cyclesTargets += 1
        #    c = CycleEvent(self.cyclesTargets)
        #    self.lodManager.notify(c)

        #self.lastTarget = self.currentTarget
        #self.currentTarget = newTarget

    #=============================================

    def setPoints(self, points):
        self.points = points
        self.pointsHUD.setPoints(points)
        # the game ends if the user reaches pointToEnd points
        # from the config file.
        if self.points >= self.config.pointsToEnd:
            self.finishGame = True
            taskMgr.doMethodLater(2.0, self.sendMessage, 'end game', extraArgs=['endOfGame'])

    #=============================================

    def addPoints(self, points):
        self.setPoints(self.points + points)

    #=============================================

    def getParachutesPositions(self, type_par='targets'):
        """returns a list of 3d positions with all targets positions
           in a particular instant"""
        pass

    #        temp = self.targets.items()
    #        if type_par == 'non_targets':
    #            temp = self.non_targets.items()
    #        if type_par == 'all':
    #            temp += self.non_targets.items()
    #
    #        result = []
    #        for k, v in temp:
    #            result.append(v.modelNP.getPos())
    #        return result

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

        self.cursorX = 0
        self.cursorY = 0

        shooter = self.config.shooter

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

        # position the cannon relative to camera position
        self.cannon.setScale(0.15)

        # this is trial an error for different resolutions, to get
        # the cannon in a nice place.
        Y = float(shooter.cannonPosY)
        Z = float(shooter.cannonPosZ)

        self.cannon.setPos(camera.getPos() + Vec3(0, Y, Z))
        # position to match initial pos of the crosshair
        # TODO - fix these constants!
        self.cannon.setHpr(180, 0, 0)
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

        self.bullets = []
        for i in range(shooter.bulletSet):

            bulletNP = loader.loadModel(shooter.bullet)
            bulletNP.node().setName("bulletNode_" + str(i))
            bulletNP.setScale(self.bulletSize)
            bulletNP.setName("bulletNP_" + str(i))
            bulletNP.setColor(0.1, 0.1, 0.1)

            if not self.isReplay:
                # collision sphere solid attached to the node
                # the sphere is a bit ahead of the bullet
                # the radious will change the difficulty
                colSolid = CollisionSphere(0, 5, 0, 3.0)
                colNP = bulletNP.attachNewNode(
                    CollisionNode('ColNodeBullet_' + str(i)))

                colNP.node().addSolid(colSolid)
                colNP.node().setFromCollideMask(BitMask32(0x80))

                bulletNP.setCollideMask(BitMask32(0x0))

                base.cTrav.addCollider(colNP, self.colHandlerEvent)

            self.bullets.append(bulletNP)
            self.bullets[-1].reparentTo(cannonNP)

        self.bulletIdx = 0
        self.maxbullets = shooter.bulletSet

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
        self.replayLog.logEvent("S\n")

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
        idx = self.bulletIdx % self.maxbullets
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
        event = "hideball" + str(idx)
        proj.setDoneEvent(event)

        #p.reparentTo(self.bullets[idx])
        #p.start(self.bullets[idx])
        proj.acceptOnce(event, self.hideAndRemoveBullet, [self.bullets[idx]])

        self.bulletIdx += 1
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
            self.mapkeys[key - 4] = 0

        if (self.replayLog.logging):
            # get time stamp
            state = "K:" + str(self.mapkeys) + "\n"
            self.replayLog.logEvent(state)

        return

    #=============================================
    def pauseFall(self):
        for p, v in self.parachutesFalling.items():
            v.pauseFall()

    def unPauseFall(self):
        for p, v in self.parachutesFalling.items():
            v.unPauseFall()
