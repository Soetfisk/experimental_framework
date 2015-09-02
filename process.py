__author__ = 'francholi'

#lines = open('expdata.txt').readlines()
#output = open('result.txt','w')
## remove data about participant
#for i,l in enumerate(lines):
#    if 'Application' in l or 'date' in l or 'loading' in l or \
#        'query' in l or 'participant' in l or \
#        'Simulation' in l or l == '\n' or 'EOL' in l:
#        continue
#    elif l[0] == 'P':
#        l = l[l.find('-')+1:]
#    l = l.split(':')
#    abstime=l[0]
#    rest=l[1].split()
#    c = ','
#    output.write(
#        '{0},{1[1]},{1[3]},{1[5]}\n'.format(abstime,rest)
#    )
#    ''
#output.close()


import numpy as np
stats=open('result.csv').readlines()
stats = stats[1:]
new_stats=[]
for l in stats:
    l=l.split(',')
    new_stats.append(l[:3] + [ float(l[3]) ])

conditions = {
'Analog_vs_Analog': lambda x: 'An_' in x[1] and 'An_' in x[2],
'Analog_vs_Any': lambda x: 'An_' in x[1] or 'An_' in x[2],
'Warm_vs_Cool': lambda x: 'Warm' in x[1] or 'Warm' in x[2],
'Complem_vs_Compem': lambda x: 'CC' in x[1] and 'CC' in x[2],
'Complem_vs_Any': lambda x: 'CC' in x[1] or 'CC' in x[2],
'Triads_vs_Triads': lambda x: 'Tr' in x[1] and 'Tr' in x[2],
'Triads_vs_Any': lambda x: 'Tr' in x[1] or 'Tr' in x[2],
'SplitComp_vs_SplitComp': lambda x: 'SpCo' in x[1] and 'SpCo' in x[2],
'SplitComp_vs_Any': lambda x: 'SpCo' in x[1] or 'SpCo' in x[2],
}




analogous_delays = [ x[3] for x in new_stats if 'An_' in x[1] and 'An_' in x[2]]
print np.array(analogous_delays).mean()
