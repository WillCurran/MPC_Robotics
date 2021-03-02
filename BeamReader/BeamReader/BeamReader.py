import time
import random
import os
import sys
from multiprocessing import Process, Lock

FILE_NAME_SHARES_A = 'shares_a'
FILE_NAME_SHARES_B = 'shares_b'

def count_bits(n):
	return len(bin(n)[2: ])


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

def print_func(lock, file_name, label_index, num_agents):
    print('Reading file : ', file_name)
    file = open(file_name, "r")
    file_data = file.readlines()
    file.close()
    lock.acquire()
    try:
        file_shares_a = open(FILE_NAME_SHARES_A, 'a')
        file_shares_b = open(FILE_NAME_SHARES_B, 'a')
        for line in file_data:
            print(str(int(line)))
            plain_number = (int(line) << count_bits(num_agents)) + label_index
            random_number = random.randint(1,plain_number)
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
    if len(sys.argv) < 2:
        sys.exit("Must pass at least one agent label.") 
    names = sys.argv[1:]
    procs = []
    lock = Lock()
    # instantiating process with arguments
    names.sort()

    for i in range(len(names)):
        proc = Process(target=print_func, args=(lock,names[i],i,len(names)))
        procs.append(proc)
        proc.start()

    # complete the processes
    for proc in procs:
        proc.join()