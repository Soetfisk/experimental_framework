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
    # NON-RECURSIVE
    myKeys=[]
    # for each key
    for i in range(len(v)):
        aKey = []
        if 'key' not in v.keys() or 'callback' not in v.keys():
            raise Exception("Error in key definition")
        aKey.append( { 'type': 'str', 'name': 'key', 'value': v['key']} )
        aKey.append( { 'type': 'str', 'name': 'callback', 'value': v['callback']} )
        if v.has_key('once'):
            aKey.append( { 'type': 'bool', 'name': 'once', 'value': v['once']} )
        if v.has_key('tuple_args'):
            aKey.append( { 'type': 'str', 'name':'tuple_args', 'value': v['tuple_args']})
        keyGroup = { 'type':'group','name':v['key'], 'childre': aKey}
        myKeys.append(keyGroup)
    return {'type':'group','name':'Keymap','children':myKeys}

def handleTuples(k,v):
    return { 'type': 'str', 'name':k, 'value': str(v)}

def handleOption(k,v):
    return { 'type': 'list', 'name':k, 'values': list(v[:-1]), 'value':v[-1]}

def handleColor(k,v):
    # convert from string to tuple
    return { 'type': 'color', 'name':k, 'value': eval(v) }

def handleText(k,v):
    return { 'name': k, 'type': 'text', 'value': v }

def handleFileName(k,v):
    return { 'type': 'str', 'name':k, 'value': v }

mappings = {
    'keys': handleKeys,
    'tuple_': handleTuples,
    'option_': handleOption,
    'color_': handleColor,
    'fname_': handleFileName,
    'text_': handleText,
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
        for m in mappings:
            if m == k[0:len(m)] and not isinstance(v,dict) and not isinstance(v,list):
                item = mappings[m](k,v)
                break
        else:
            item = {'type':type(v).__name__, 'name':k, 'value':v}

        if isinstance(v,dict):
            item = fromYamlToParameter(v,k)
            groups.append(item)
        # the list consist of only dictionaries!!!
        elif isinstance(v,list) and len([e for e in v if isinstance(e,dict)])==len(v):
            item = fromYamlToParameter( {str(i):vv for (i,vv) in enumerate(v)},k )
            groups.append(item)
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
    keys on the top.
    """

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
