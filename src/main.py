import utils
import copy
import multiprocessing
from multiprocessing import Process, Pipe, Queue, Lock
import logging
import gmw
from sorting_network import *
from Party import *
import time

# create a test circuit and run it across 2 parties with GMW
gc_exch = gmw.exchangeCirc()
gc_comp = gmw.comparatorCirc()
# open files of precomputed random OTs
alice_sender_file = open('a.txt', 'r')
alice_recver_file = open('b1.txt', 'r')
bob_sender_file = open('a1.txt', 'r')
bob_recver_file = open('b.txt', 'r')

n_time_bits = int(input("Number of time bits: "))
n_symbol_bits = int(input("Number of symbol bits: "))
times = input("Input times (space delimited): ")
symbols = input("Input symbols (space delimited): ")

gc_eq = gmw.equalityCirc(n_time_bits)
max_time = 2**n_time_bits - 1
max_symbol = 2**n_symbol_bits - 1
times = [int(s) if int(s) <= max_time else exit(1) for s in times.split(' ')]
symbols = [int(s) if int(s) <= max_symbol else exit(1) for s in symbols.split(' ')]
n = len(times)
assert(n == len(symbols))
assert(n >= 2)
input_for_printing = list(zip(times, symbols))
input_list = [(times[i] << n_symbol_bits) | symbols[i] for i in range(n)]
alice_input, bob_input = utils.splitList(input_list, n_time_bits, n_symbol_bits)

network = SortingNetwork('BUBBLE', n)

# both parties own the same gc, but will alter values
alice = Party(n_time_bits, n_symbol_bits, alice_input, "A")
bob = Party(n_time_bits, n_symbol_bits, bob_input, "B")
alice.setGC(gc_comp, gc_exch, gc_eq)
bob.setGC(copy.deepcopy(gc_comp), copy.deepcopy(gc_exch), copy.deepcopy(gc_eq))
# both own same network, will not alter values
alice.setSortingNetwork(network)
bob.setSortingNetwork(network)
# give parties their precomputed OT files
alice.setOTFiles(alice_sender_file, alice_recver_file)
bob.setOTFiles(bob_sender_file, bob_recver_file)
print("plaintext:\n", input_for_printing)
print("Alice shares:\n", alice.my_shares)
print("Bob shares:\n", bob.my_shares)

# evaluate circuits concurrently.
if __name__ == '__main__':
    k = 8 # security parameter
    s = 16 # statistical security parameter

    mpl = multiprocessing.log_to_stderr()
    mpl.setLevel(logging.INFO)
    
    connections = Pipe()
    ipc_lock = Lock()
    # Queue for reporting output
    q = Queue()
    p_a = Process(target=alice.executePipeline, args=(connections[0], q, ipc_lock, k, s,))
    p_b = Process(target=bob.executePipeline, args=(connections[1], q, ipc_lock, k, s,))
    start = time.time()
    p_a.start()
    p_b.start()
    p_a.join()
    p_b.join()
    end = time.time()
    # should be 2 things in the queue
    if(q.empty()):
        print("ERROR QUEUE SIZE")
        exit(1)
    res1 = q.get()
    if(q.empty()):
        print("ERROR QUEUE SIZE")
        exit(1)
    res2 = q.get()
    output_list = [(num >> n_symbol_bits, num & utils.bitmask(0, n_symbol_bits-1)) for num in utils.mergeLists(res1, res2)]
    print("list after sort", output_list)
    print("Took", end-start, "seconds.")
    alice_sender_file.close()
    alice_recver_file.close()
    bob_sender_file.close()
    bob_recver_file.close()