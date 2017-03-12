import sys
fname = sys.argv[1]
lines = open(fname).readlines()
print 'digraph drawing {'
print 'rankdir=LR;'
print 'node [shape = circle];'

for l in lines:
    if '- trans:' in l:
        left,right = l.strip().replace("'",'').split(':')[1:]
        fr,to = left.split('@')
        print fr,'->',to,"[ label = %s ];" % right
print '}'
