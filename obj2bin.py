__author__ = 'francholi'
import sys
import struct

# code from
# stackoverflow.com/questions/2262333/
# is-there-a-built-in-or-more-pythonic-way-to-try-to-parse-a-string-to-an-integer
def ignore_exception(IgnoreException=Exception,DefaultVal=None):
    """ Decorator for ignoring exception from a function
    e.g.   @ignore_exception(DivideByZero)
    e.g.2. ignore_exception(DivideByZero)(Divide)(2/0)
    """
    def dec(function):
        def _dec(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except IgnoreException:
                return DefaultVal
        return _dec
    return dec

def printUsage():
    print "python obj2bin.py objFile binFile"

vertices = []
normals = []
uvs = []
group = 'default'
meshParts = {'default': {'faces': [], 'material': ''}}
# id, properties including texture filenames for each map
materials = {}

def parseFace(line):
    for v in [map(float, vtx.split('/')) for vtx in line.split()[1:]]:
        meshParts[group]['faces'].append(v)
#================================================
def parseGroup(line):
    global group
    group = reduce(lambda x,y: x+'_'+y, line.split()[1:])
    meshParts.setdefault(group, {'faces':[],'material':''} )
#================================================
def parseMaterial(line):
    # trick to avoid writing try/except blocks for the parsing part
    ignore = [ ignore_exception(ValueError)(int),
               ignore_exception(ValueError)(float),
               str ]
    matfile = open(line.split()[1])
    currMat = ''
    for line in matfile.readlines():
        if line.strip().startswith('#'): continue
        if 'newmtl' in line:
            currMat = line.split()[1]
            materials[currMat]={}
        else:
            line = line.split()
            matValues=[]
            for v in line[1:]:
                for f in ignore:
                    newV = f(v)
                    if newV is not None:
                        matValues.append(newV)
                        break
            materials[currMat][line[0]] = matValues
    matfile.close()
#================================================
def parseSmoothingGroup(line):
    pass
#================================================
maps = {'v ': lambda line: vertices.append(map(float, line.split()[1:])),
        'vn': lambda line: normals.append(map(float, line.split()[1:])),
        'vt': lambda line: uvs.append(map(float, line.split()[1:])),
        'g ': parseGroup,
        's ': parseSmoothingGroup,
        'f ': parseFace,
        'mt': parseMaterial,
        'us': lambda line: meshParts[group].setdefault('material',line.split()[1])
}

def parseObj(filename):
    for line in open(filename):
        try:
            line = line.lstrip()
            if len(line) == 0 or line[0] == '#':
                continue
            maps[line[0:2]](line)
        except Exception,e:
            print e
            print "Error parsing line"
            print line
            sys.exit()
    print vertices
    print normals
    print uvs
    print materials

    dumpBin()

def dumpBin():
    with open(sys.argv[2],'w') as output:
        # number of parts
        numMeshParts = struct.pack('i',len(meshParts.keys()))
        output.write(numMeshParts)
        for m in meshParts.keys():
            numVtx = struct.pack('i', len(meshParts[m]['faces']*3))
            numMats = struct.pack('i', len(meshParts[m]['material']) )
            #for matId in len(meshParts[m]['materials']):
            #struct.pack('ffffffff',*(0,0,0,0,0,0,0,0) )
            print "num materials:", len(meshParts[m]['material'])
            print "vertices..."
            print "materials...."

if __name__ == '__main__':
    if len(sys.argv) != 3:
        printUsage()
        exit()
    else:
        parseObj(sys.argv[1])
        a = 1
