# some handy functions that I've used in different
# places

# utility function to create an enum
# Use like this:
# Numbers = enum(ONE=1, TWO=2, THREE=3)
# Numbers.ONE == 1
def createEnum(**enums):
    return type('Enum',(),enums)

def make_list(node):
    """
    A handy function that creates a list if the argument is not
    a list
    """
    if (isinstance(node,list)):
        return node
    else:
        return [node]

def makeDict(args):
    """
    make a dictionary out of the cmd line arguments,
    using lhs as key and rhs as a string value
    """
    d = {}
    for a in args:
        d[a.split('=')[0]] = a.split('=')[1]
    return d

def splitString(myString, maxlength):
    """ recursive function to split a string into a list of strings
    based on length """
    pos = myString.find(' ',maxlength)
    if (pos == -1):
        return [ myString ]
    return [ myString[:pos] ] + splitString(myString[pos+1:],maxlength)

class objFromDict(object):
    """
    given a dictionary, create an object with each key as an
    attribute
    """
    def __init__(self, d):
        for a, b in d.items():
            try:
                if isinstance(b, (list, tuple)):
                    setattr(self, a, [objFromDict(x) if isinstance(x, dict) else x for x in b])
                else:
                    if (a=='keys' or a==u'keys'):
                        print a,b
                    setattr(self, str(a), objFromDict(b) if isinstance(b, dict) else b)
            except Exception,e:
                print e
                print a,b
                quit()



