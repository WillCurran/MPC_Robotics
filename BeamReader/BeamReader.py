import time
import random
import os
import sys
import math
from multiprocessing import Process, Lock

FILE_NAME_SHARES_A = 'shares_a'
FILE_NAME_SHARES_B = 'shares_b'

def flipCoin():
    return random.choice([True,False])

def read_delete_and_create_again(file_name):
    file = open(file_name, "r")
    file_data = file.read()
    file.close()

    if os.path.exists(file_name):
      os.remove(file_name)

    file = open(file_name, "x")
    file.write(file_data)
    file.close()

def print_func(lock, file_name, label_index, start, end, num_beams):
    sensor_bits = math.ceil(math.log2(num_beams+1)) # beams, plus null symbol
    sensor_max = 2**sensor_bits-1
    time_bits = math.ceil(math.log2(end-start))                         
    data = {k: sensor_max for k in range(0,end-start)}
    with open(file_name, "r") as file:
        for line in file:
            current_value = int(line) - start
            if current_value < 0:
                continue
            if current_value >= end-start:
                break
            data[current_value] = label_index
    f = open(file_name, "r")
    file_data = f.readlines()
    f.close()
    lock.acquire()
    try:
        print('Reading file : ', file_name)
        print(data)
        file_shares_a = open(FILE_NAME_SHARES_A, 'a')
        file_shares_b = open(FILE_NAME_SHARES_B, 'a')
        for key in data:
            plain_number = (key << sensor_bits) + data[key]
            random_number = random.getrandbits(sensor_bits + time_bits)
            share_a = random_number
            share_b = plain_number ^ random_number
            file_shares_a.write(str(share_a) + '\n')
            file_shares_b.write(str(share_b) + '\n')
    finally:
        lock.release()

if __name__ == "__main__":  # confirms that the code is under main function
    if os.path.exists(FILE_NAME_SHARES_A): 
        os.remove(FILE_NAME_SHARES_A)
    if os.path.exists(FILE_NAME_SHARES_B): 
        os.remove(FILE_NAME_SHARES_B)
    print('Number of arguments:' + str(len(sys.argv)))
    if len(sys.argv) < 5:
        sys.exit("Must pass at least one agent label with two time stamps.") 
    start = int(sys.argv[1])
    end = int(sys.argv[2])
    time_window = 2**int(sys.argv[3])
    names = sys.argv[4:]
    procs = []
    lock = Lock()
    # instantiating process with arguments
    names.sort()
    for s in range(start, end, time_window):
        for i in range(len(names)):
            proc = Process(target=print_func, args=(lock,names[i],i,s,s+time_window,len(names)))
            procs.append(proc)
            proc.start()

        # complete the processes
        for proc in procs:
            proc.join()