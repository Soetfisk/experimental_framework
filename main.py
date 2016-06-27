import os, sys
import time

# from external I pick up YAML and colorama for output colouring.
sys.path.append("./external")
# debug has printOut(message, verbose_level) to print to the output
import Utils.Debug as debug

def printUsage():
    print "Usage: ppython main.py exp=[experimentFile.yaml|online] [debug=0] [channels=all]"
    print "If 'online' is specified, nothing is going to show and the program will wait for" \
          "an external program to send YAML elements for testing, or YAML experiments."
    sys.exit()

if __name__=='__main__':
    # extract experiment file from command line
    experiment='online'
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

    # reaching this point, we have the right command line arguments,
    # lets try and create the basic World object,
    # which will in place create additional objects.
    debug.printOut('Importing world module', 3)
    # this will import the Panda3D engine stuff (most of it)
    from World import World
    # create one object with an experiment or 'online' word
    w = World(experiment)
    # enter main loop from Panda3D (see tasks in World)
    base.run()

