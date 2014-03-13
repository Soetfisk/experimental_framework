from colorama import *
init()

# trivial module that defines a function to print out
# debugging information, and defines a variable to control
# the verbosity.

min_verb = 0
max_verb = 4
# five levels of debug
colors = [Fore.RED,Fore.YELLOW,Fore.YELLOW,Fore.YELLOW,Fore.GREEN]
curr_verb= 0

# specifying channels we can filter by tags or categories
channels = ['all']
# there are 5 levels of debug, RED for errors, YELLOW for Warnings
# and GREEN for information
# Also, the debugging verbosity will say how much is printed, ERRORS
# are always printed, but WARNINGS and INFO is CUSTOMIZABLE with a runtime
# argument "debug=numerical_value"


def printOut(message, level=curr_verb, channel='all' ):
    # ignore channels for now.
    if curr_verb >= level >= 0:
        print(colors[level] + message)
