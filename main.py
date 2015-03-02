import os, sys
sys.path.append("./external")
import Utils.Debug as debug
import time

def printUsage():
    print "Usage: ppython main.py exp=experimentFile.yaml [debug=0] [channels=all]"
    sys.exit()

if __name__=='__main__':
    # extract experiment file from command line
    experiment='none'
    try:
        for arg in sys.argv:
            if 'exp=' in arg:
                experiment = arg.split('=')[1]
                continue
            if 'debug=' in arg:
                # debug verbosity is 0 (minimum)
                verb = int(arg.split('=')[1])
                debug.curr_verb = min(verb, debug.max_verb)
                continue
            if 'channels=' in arg:
                debug.channels = arg.split('=')[1]
                continue
    except IndexError,e:
        printUsage()

    if (experiment is 'none'):
        printUsage()

    # reaching this point, we have the right command line arguments,
    # lets try and create the basic World object,
    # which will in place create additional objects.
    debug.printOut('Importing world module', 3)
    # this will import the Panda3D engine stuff (most of it)
    from World import World
    # create one object with an experiment
    w = World(experiment)
    # enter main loop from Panda3D (see tasks in World)
    run()

