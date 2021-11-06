import io

prefix_file = 'prefix.txt'
suffix_file = 'suffix.txt'

human_input_name = 'groupA-script1.txt'
machine_file_name = 'machine_script.txt'

interval = 5

script = []
G_set = {}

drone_list = []

with open(human_input_name) as human_script:
    for line in human_script.readlines():
        if line != '' and line != '\n':
            line = line.rstrip()
            
            if '//' in line:
                #ignore comments
                continue
                
            elif 'duration' in line:
                full_duration = int(line.split(' ')[1])
            
            elif 'group' in line:
                G = line.split(' ')[1]
                # print(G)
                #for each group, make a new dict in G_set dict
                G_set[G] = {}
                id_list = line.partition('=')[2]
                id_list = ''.join(id_list.split())
                id_list = id_list.split(',')
                G_set[G]['ids'] = id_list
                G_set[G]['last_height'] = 0
                print(G_set[G])

            #parse human-readable commands    
            elif ':' in line:
                G = line.partition(':')[0]
                print(G)
                time = line.split(' ')[1].rstrip('s')
                command = line.split(' ')[2]
    
                if 'takeoff' in command:
                    G_set[G][int(time)] = 'takeoff'
                    #assume takeoff height is 50....
                    G_set[G]['last_height'] = 50
                    print('added takeoff command at %ss' % time)
                    
                elif '-' in time:
                	#track start and end times for movements
                    start = int(time.partition('-')[0].rstrip('s'))
                    end = int(time.partition('-')[2].rstrip('s'))
                    duration = end - start
                    #calculate distance of movement
                    distance = int(command) - G_set[G]['last_height']
                    #calculate speed of movement
                    speed = abs(distance / duration)

                    #print refence specs per movement
                    print('group %s moving from %i to %i' % (G, G_set[G]['last_height'], int(command)))
                    print('move duration: %i' % duration)
                    print('move distance: %i' % distance)
                    print('move speed: %f' % speed)
                    
                    #calculate number of intervals in this movement & distance per interval
                    #interval duration is how often the script will send commands
                    intervals = duration // interval
                    inter_dist = distance / intervals
                    print('move occurs over %f intervals, %f per interval' % (intervals, inter_dist))
                    
                    for i in range(int(intervals)):
                    	#create entry in group(G) dict with the starting time as key and command as value
                        timestamp = start + (i * interval)
                        G_set[G][timestamp] = 'go 0 0 %f %f' % (inter_dist, speed)
                        
                    #update and track the last height this group is supposed to be at, for distance calculations
                    G_set[G]['last_height'] = int(command)
        
    human_script.close()

#print final drone instruction dictionary for reference
for key in G_set.keys():
    print('\ngroup %s final dict:' % key)
    print(G_set[key])

#create master list of 'expected' drone ids to pass into testing/controlling/managing scripts
for G in G_set.keys():
    for drone in G_set[G]['ids']:
#         print(drone)
        drone_list.append(drone)

id_ints = [int(_id) for _id in drone_list]
id_ints.sort()
print('machine script expects drones: ' + str(id_ints))
        
#first line of script gives expected drone ids for later use
script.append('expect ' + str(id_ints) + '\n')

#prefix file allows the user to put whatever extra commands they want at the beginning
with open(prefix_file, 'r') as prefix:
    for line in prefix.readlines():
        script.append(line)
    prefix.close()

#calculate number of intervals (inter_steps) based on full_duration from human script
inter_steps = range(0, full_duration, 5)

#create and append script sections PER INTERVAL, based on each groups's saved dict compilation
for step in inter_steps:
	#make timestamp comment for clarity
    script.append('//time(seconds) = %s\n' % step)
    for G in G_set.keys():
    	#if the group dict has a move command for this interval, use it
        if step in G_set[G].keys():
            for _id in G_set[G]['ids']:
                this_line = _id + '>' + G_set[G][step] +'\n'
                script.append(this_line)
        #if it doesn't have a move command, send >stop
        else:
            for _id in G_set[G]['ids']:
                this_line = _id + '>stop\n'
                script.append(this_line)
    #sync at the end of every interval for interval duration
    #(this might cause the script to run longer than desired,
    #but we need more testing to refine this technique)
    script.append('sync %i\n' % interval)

#like the prefix, the suffix file allows for extra commands at the end (such as *>land, battery check)
with open(suffix_file, 'r') as suffix:
    for line in suffix.readlines():
        script.append(line)
    suffix.close()

#finally, write the machine script file in the parent directory. note the windows \\, you will have to localize for unix
with open('..\\' + machine_file_name, 'w') as output:
    output.writelines(script)
    output.close

#make a note of it
print('\n---------------> successfully exported new script to ' + machine_file_name)