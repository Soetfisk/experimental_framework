# trivial module that defines a function to print out
# debugging information, and defines a variable to control
# the verbosity.

verbosity = 0
# specifying channels we can filter by tags or categories
channels = ['all']

def printOut( message, level, channel='all' ):
    if (level <= verbosity):
        if ('all' in channels or channel in channels):
            print message
