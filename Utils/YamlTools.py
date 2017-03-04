__author__ = 'francholi'


def str2tuple(x):
    """nasty hack to fix something about YAML conversion
    that I do not remember now, but I will fix and remove this code."""
    if not isinstance(x,str):
        return x
    try:
        if ")" in x:
            temp = eval(x.replace(")",",)"))
            return temp
        else:
            return x
    except:
        return x

def fixTuples(yamlTree):
    if isinstance(yamlTree,list):
        for i,x in enumerate(yamlTree):
            yamlTree[i] = fixTuples(x)
    if isinstance(yamlTree,dict):
        for k,v in yamlTree.items():
            yamlTree[k] = fixTuples(v)
    return str2tuple(yamlTree)



