from panda3d.core import *
import random

# helper class
class PositionGenerator (object):
    """ Class to generate positions where parachutes
        must appear. Has to generate random positions,
        has to keep track of last positions generated,
        has to ocuppy the screen to it's full wide,
        but be no predictable."""
        
    def __init__(self, topLeft, topRight, memory=3, world=None, debug=False):
        """- topLeft and topRight are screen width limits
           - memory is how many positions it can remember,
           - world is a reference to the world where all resides used
             to know where are the parachutes when generating new positions.
           - debug will show graphycally the limits of the random generation
             with 2 smileys in the corners"""

        #slots = {1:{}, 2:{}, 3:{}}
        #for r in range(1,self.memory+1):
        #    slots[1][r] = 0
        #    slots[2][r] = 0
        #    slots[3][r] = 0
        
        #if (debug):
        #    self.tlNode = loader.loadModel("smiley.egg")
        #    self.tlNode.setPos(topLeft)
        #    self.tlNode.reparentTo(self.scenes['gamePlay'])
        #    self.tlNode = loader.loadModel("smiley.egg")
        #    self.tlNode.setPos(topRight)
        #    self.tlNode.reparentTo(self.scenes['gamePlay'])

        self.topLeft = topLeft
        self.topRight = topRight
        self.memory = memory
        self.lastPositions = []

        # grab a reference to the main object
        self.w = world

        # correction of the height because we rotated the
        # camera a bit - TODO - get rid of these manual adjustments!
        self.hideMeTop = 60
        self.sideFix=10

        # makes the random number generation fixed to a sequence
        random.seed(127)


    def getNewPos(self, distance = 20):
        """distance = distance UP from the top border, so the
           bigger the distance the farther the parachute starts
           from the top of the border
           If it cannot find a random position will try for a random
           position higher, until it finds one"""
           
        # loop until valid position
        newPosValid = False
        s = self.sideFix

        stepUp = 30
        counter= 0
        
        # distance in X between 2 parachutes
        spaceX = 2*self.topRight[0] / 10.0
        
        randZ = self.topRight[2] + self.hideMeTop + distance

        spaceZ = 100
        
        while (not newPosValid):
            newPosValid = True
            randX = random.uniform(self.topLeft[0] +s,
                            self.topRight[0]-s)
            randZ = random.uniform(randZ, randZ + distance)

            positions = self.w.getParachutesPositions('targets') + self.w.getParachutesPositions('non_targets')
            for pos in positions:
                if (abs(randX - pos.getX()) < spaceX and abs(randZ - pos[2]) < spaceZ):
                    newPosValid = False
                    break

            if (not newPosValid):
                counter+=1
                # try higher up
                if (counter % 5 == 0):
                    randZ += stepUp
                # give up
                if (counter % 20 == 0):
                    #print "giving up!"
                    return None
                continue

        # keep the list up to "memory" objects
        if (len(self.lastPositions) == self.memory):
            self.lastPositions.remove(self.lastPositions[0])
        self.lastPositions.append((int(randX),int(randZ)))
        return Vec3(randX, self.topLeft[1], randZ)

