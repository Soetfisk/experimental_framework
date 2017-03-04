__author__ = 'francholi'

import numpy as np

lines = open('expdata.txt').readlines()
## remove data about participant
new_list={}
for i,l in enumerate(lines):
    if 'Application' in l or 'date' in l or 'loading' in l or \
        'query' in l or 'Simulation' in l or l == '\n' or 'EOL' in l:
        continue
    if 'participant' in l:
        participant = l[0:l.find('-')]
        new_list[participant] = []
        previous_time = -1.0
        continue

    # remove PX-
    l = l[l.find('-')+1:]
    # split :
    l = l.split(':')
    # take absolute time
    abstime=float(l[0])
    # compute delay
    if (previous_time!=-1):
        delay = abstime - previous_time
    else:
        delay = 2.3
    previous_time = abstime
    rest=l[1].strip().split(' ')
    new_list[participant].append([delay]+rest[1:6:2])

conditions = {
'Analog_vs_Analog': lambda x: 'An_' in x[2] and 'An_' in x[3],
'Analog_vs_Any': lambda x: 'An_' in x[2] or 'An_' in x[3],
'Warm_vs_Cool': lambda x: 'Warm' in x[2] or 'Warm' in x[3],
'Complem_vs_Any': lambda x: 'CC' in x[2] or 'CC' in x[3],
'Triads_vs_Any': lambda x: 'Tr' in x[2] or 'Tr' in x[3],
'SplitComp_vs_SplitComp': lambda x: 'SpCo' in x[2] and 'SpCo' in x[3],
'SplitComp_vs_Any': lambda x: 'SpCo' in x[2] or 'SpCo' in x[3],
}

for condition,function in conditions.items():
    print condition,
print ''

delays={}
total=[]
for participant in range(1,16):
    delays[participant]={}
    print "P" + str(participant),
    for condition,function in conditions.items():
        temp_list = [ x[0] for x in new_list['P'+str(participant)] if function(x) ]
        if len(temp_list)==0:
            print new_list['P'+str(participant)][0]
            print "empty!, for condition " + condition + " for participant " + str(participant)
        else:
            delays[participant][condition] = round(np.array(temp_list).mean(),3)
            print delays[participant][condition],
    avg_part = round(np.array([ x[0] for x in new_list['P'+str(participant)]]).mean(),3)
    print avg_part
    total.append(avg_part)
print round(np.array(total).mean(),3)



#analogous_delays = [ x[3] for x in new_stats if 'An_' in x[1] and 'An_' in x[2]]
#print np.array(analogous_delays).mean()
