__author__ = 'francholi'

from collections import OrderedDict

"""
    keys:
    - key: arrow_left
      callback: imageSelected
      once: false
      tuple_args: ()
    - key: x
"""
def handleKeys(k,v):
    # v is a list of keys, each key is an ordered dictionary
    myKeys=[]
    # for each key
    for key in v:
        aKey = []
        if 'key' not in key.keys() or 'callback' not in key.keys():
            print "ERROR: Error in key definition"
            print "%s" % str(key)
            raise Exception("Error in key definition")
        aKey.append( { 'type': 'str', 'name': 'key', 'value': key['key']} )
        aKey.append( { 'type': 'str', 'name': 'callback', 'value': key['callback']} )
        if key.has_key('once'):
            aKey.append( { 'type': 'bool', 'name': 'once', 'value': key['once']} )
        if key.has_key('tuple args'):
            aKey.append( { 'type': 'str', 'name':'tuple args', 'value': key['tuple args']})
        keyGroup = { 'type':'group','name':key['key'], 'children': aKey}
        myKeys.append(keyGroup)
    return {'type':'group','name':'Keymap','children':myKeys}

def handleTuples(k,v):
    return { 'type': 'str', 'name':k, 'value': str(v)}

def handleOption(k,v):
    return { 'type': 'list', 'name':k, 'values': list(v[:-1]), 'value':v[-1]}

def handleColor(k,v):
    # convert from string to tuple
    if isinstance(v,list):
       v = str(tuple(v))
    return { 'type': 'color', 'name':k, 'value': eval(v) }

def handleFile(k,v):
    return { 'type': 'file', 'name':k, 'value': v }

def handleFolder(k,v):
    return { 'type': 'folder', 'name':k, 'value': v}

def handleText(k,v):
    return { 'name': k, 'type': 'text', 'value': v }

def handleList(k,v):
    return { 'type': 'list', 'name':k, 'values': v }

# if the name of the key contains this, use the function as a handler
# to return the right type.
mappings = {
    'keys': handleKeys,
    'vec2': handleTuples,
    'vec3': handleTuples,
    'vec4': handleTuples,
    'tuple': handleTuples,
    'option': handleOption,
    'color': handleColor,
    'file': handleFile,
    'folder': handleFolder,
    'text': handleText,
    'list': handleList,
}

def fromParameterToYaml(paramenter, name):
     """
    Recursive method to convert from YAML to the representation that ParameterTree
    supports
    It uses the naming convention from the attributes to derive a datatype
    """
     pass
#    single = []
#    groups = []
#    for k,v in yamlDict.items():
#        for m in mappings:
#            if m == k[0:len(m)] and not isinstance(v,dict) and not isinstance(v,list):
#                item = mappings[m](k,v)
#                break
#        else:
#            item = {'type':type(v).__name__, 'name':k, 'value':v}
#
#        if isinstance(v,dict):
#            item = fromYamlToParameter(v,k)
#            groups.append(item)
#        # the list consist of only dictionaries!!!
#        elif isinstance(v,list) and len([e for e in v if isinstance(e,dict)])==len(v):
#            item = fromYamlToParameter( {str(i):vv for (i,vv) in enumerate(v)},k )
#            groups.append(item)
#        elif isinstance(v,list):
#            item = {'name': k, 'type': 'list', 'values': v, 'value': v[0]}
#            single.append(item)
#        else:
#            single.append(item)
#
#    p = {'type':'group','name':yamlDict.get('name',name), 'children':single+groups }
#    return p

def fromYamlToParameter(yamlDict, name):
    """
    Recursive method to convert from YAML to the representation that ParameterTree
    supports
    It uses the naming convention from the attributes to derive a datatype
    """
    single = []
    groups = []
    for k,v in yamlDict.items():
        # is there a specific word to narrow further the datatype
        if k.split(' ')[0] in mappings.keys():
            item = mappings[k.split(' ')[0]](k,v)
            single.append(item)
            continue
        # general case
        else:
            item = {'type':type(v).__name__, 'name':k, 'value':v}

        #for m in mappings:
        #    if m == k[0:len(m)] and not isinstance(v,dict): # and not isinstance(v,list):
        #        item = mappings[m](k,v)
        #        break
        if isinstance(v,dict):
            item = fromYamlToParameter(v,k)
            groups.append(item)
        # if it is a list of dictionaries, and ONLY DICTIONARIES!!!
        elif isinstance(v,list) and len([e for e in v if isinstance(e,dict)])==len(v):
            item = fromYamlToParameter( {str(i):vv for (i,vv) in enumerate(v)},k )
            groups.append(item)
        # a normal list
        elif isinstance(v,list):
            item = {'name': k, 'type': 'list', 'values': v, 'value': v[0]}
            single.append(item)
        else:
            single.append(item)

    p = {'type':'group','name':yamlDict.get('name',name), 'children':single+groups }
    return p

def pushUp(myDict):
    """
    :param myDict: receives a dictionary or list, with a freshly loaded YAML configuration
    :return: returns an ordered dictionary. The order will force some specific
    keys on the top. The keys that I care are: 'module','className','name'
    """
    # TODO: maybe this could be avoided using the explicit order in the templates.

    if isinstance(myDict,list):
        # are ALL the elements in the list "dictionaries"
        if len([e for e in myDict if isinstance(e,dict)])==len(myDict):
            return [pushUp(x) for x in myDict]
    if not isinstance(myDict,dict):
        return myDict
    orderedDict = OrderedDict()
    order = ['module','className','name']
    for o in order:
        if o in myDict:
            orderedDict[o]=myDict[o]
    restKeys = [k for k in myDict if k not in order]
    for k in restKeys:
        orderedDict[k]=pushUp(myDict[k])
    return orderedDict
