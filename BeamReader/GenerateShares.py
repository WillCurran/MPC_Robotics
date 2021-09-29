# Generates shares for given time window == 0.
# TODO - simplify BeamReader and move functionality here.

import random
import os
import sys
import math
from multiprocessing import Process, Lock

FILE_NAME_SHARES_A = 'shares_a'
FILE_NAME_SHARES_B = 'shares_b'

def parse_local_event_history(file_name, label_index, start, end, num_beams):
    sensor_bits = math.ceil(math.log2(num_beams+1)) # beams, plus null symbol
    sensor_max = 2**sensor_bits-1
    # initialize all times to null symbol, sensor max
    data = {k: sensor_max for k in range(0,end-start)}
    with open(file_name, "r") as file:
        for line in file:
            current_value = int(line) - start
            if current_value < 0:
                continue
            if current_value >= end-start:
                break
            data[current_value] = label_index
    return data

print('Number of arguments:' + str(len(sys.argv)))
if len(sys.argv) < 3:
    sys.exit("Must pass at least one agent label with two time stamps.") 
start = int(sys.argv[1])
end = int(sys.argv[2])
names = sys.argv[3:]
histories = [{} for i in range(len(names))]
for i in range(len(names)):
    histories[i] = parse_local_event_history(names[i], i, start, end, len(names))
    print(histories[i])

sensor_bits = math.ceil(math.log2(len(names)+1)) # beams, plus null symbol
sensor_max = 2**sensor_bits-1
# consolidate histories
file_shares_a = open(FILE_NAME_SHARES_A, 'w')
file_shares_b = open(FILE_NAME_SHARES_B, 'w')
for i in range(start, end):
    share_a = random.getrandbits(sensor_bits)
    share_b = sensor_max
    for j in range(len(names)):
        if histories[j][i] < sensor_max:
            share_b = histories[j][i]
            break
    
    share_b = share_b ^ share_a
    file_shares_a.write(str(share_a) + '\n')
    file_shares_b.write(str(share_b) + '\n')
file_shares_a.close()
file_shares_b.close()
