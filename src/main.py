import utils
import copy
import multiprocessing
from multiprocessing import Process, Pipe, Queue, Lock
import logging
import gmw
from sorting_network import *
from Party import *
import time
import math
import ot_recurrence
import sys

# TODO - transfer tests to a different file
def equality_test_battery():
    print("Equality test battery...")
    gc_eq = [gmw.equalityCirc(n) for n in range(1, 9, 1)]
    # (n_time_bits, n_symbol_bits, input)
    tests = []
    # T/F for each test case
    expected_output = []
    for bits in range(1, 9, 1):
        for time_1 in range(2**bits):
            for time_2 in range(2**bits):
                tests.append((bits, 1, [(time_1 << 1) | 1, (time_2 << 1) | 1]))
                expected_output.append(time_1 == time_2)

    outcomes = []
    for test in tests:
        p = Party(test[0], test[1], test[2], '')
        p.setGC(None, None, gc_eq[test[0]-1])
        outcomes.append(p.executeEqualityDummy())
    failure = False
    for i in range(0, len(expected_output)):
        if outcomes[i] != expected_output[i]:
            print("TEST", i, "FAILED: ")
            print("Expected", expected_output[i], " - Got", outcomes[i])
            failure = True
    if not failure:
        print("Test cases passed!")

def comparison_test_battery():
    print("Greater-than test battery...")
    gc_gt = [gmw.greaterThanCirc(n) for n in range(1, 9, 1)]
    # (n_time_bits, n_symbol_bits, input)
    tests = []
    # T/F for each test case
    expected_output = []
    for bits in range(1, 9, 1):
        for time_1 in range(2**bits):
            for time_2 in range(2**bits):
                tests.append((bits, 1, [(time_1 << 1) | 1, (time_2 << 1) | 1]))
                expected_output.append(time_1 > time_2)

    outcomes = []
    for test in tests:
        p = Party(test[0], test[1], [test[2]], '')
        p.setGC(gc_gt[test[0]-1], None, None)
        outcomes.append(p.executeComparisonDummy())
    failure = False
    for i in range(0, len(expected_output)):
        if outcomes[i] != expected_output[i]:
            print("TEST", i, "FAILED: ")
            print("Expected", expected_output[i], " - Got", outcomes[i])
            failure = True
    if not failure:
        print("Test cases passed!")

def parse_input_files(filename_1, filename_2, n_rounds, n_time_bits, n_sensors, pwr_of_2):
    input_a = []
    input_b = []
    n_elements = n_sensors * (2**n_time_bits)
    if pwr_of_2:
        n_elements = 2**(math.ceil(math.log2(n_elements)))
    with open(filename_1, 'r') as f:
        for j in range(n_rounds):
            input_a.append([int(f.readline()) for i in range(n_elements)])
    with open(filename_2, 'r') as f:
        for j in range(n_rounds):
            input_b.append([int(f.readline()) for i in range(n_elements)])
    return (input_a, input_b)

# TODO - organize the bulk of the following code into functions to make the main more readable

# USAGE: python3 main.py <Mode> [total_time] [time_window_bits] [n_sensors] [n_symbols]
if len(sys.argv) < 2 or (len(sys.argv) > 2 and len(sys.argv) < 6):
    print("USAGE: python3 main.py <Mode> [total_time] [time_window_bits] [n_sensors] [n_symbols]")
    exit(1)
mode = sys.argv[1]
if len(sys.argv) > 2:
    total_time = int(sys.argv[2])   
    n_time_bits = int(sys.argv[3])
    n_sensors = int(sys.argv[4])
    n_symbol_bits = math.ceil(math.log2(int(sys.argv[5])+1))    # extra null symbol which we add
    n_rounds = math.ceil((total_time+1)/(2**n_time_bits))       # [0, total_time] - evalutation starts with t=0
    print(n_rounds, n_time_bits, n_symbol_bits)

# open files of precomputed random OTs
alice_sender_file = open('a.txt', 'r')
alice_recver_file = open('b1.txt', 'r')
bob_sender_file = open('a1.txt', 'r')
bob_recver_file = open('b.txt', 'r')

if mode == 'M':
    times = input("Input times (space delimited): ")
    symbols = input("Input symbols (space delimited): ")

    gc_exch = gmw.exchangeCirc()
    gc_comp = gmw.greaterThanCirc(n_time_bits)
    max_time = 2**n_time_bits - 1
    max_symbol = 2**n_symbol_bits - 1
    times = [int(s) if int(s) <= max_time else exit(1) for s in times.split(' ')]
    symbols = [int(s) if int(s) <= max_symbol else exit(1) for s in symbols.split(' ')]
    n = len(times)
    assert(n == len(symbols))
    assert(n >= 2)
    input_for_printing = list(zip(times, symbols))
    input_list = [(times[i] << n_symbol_bits) | symbols[i] for i in range(n)]

    alice_input, bob_input = (None, None)
    if mode == 'D':
        alice_input, bob_input = (input_list, input_list)   # No communication or MPC
    else:
        alice_input, bob_input = utils.splitList(input_list, n_time_bits, n_symbol_bits)

    network = SortingNetwork('BUBBLE', n)

    # both parties own the same gc, but will alter values
    alice = Party(n_time_bits, n_symbol_bits, alice_input, "A")
    bob = Party(n_time_bits, n_symbol_bits, bob_input, "B")
    alice.setGC(gc_comp, gc_exch, None)
    bob.setGC(copy.deepcopy(gc_comp), copy.deepcopy(gc_exch), None)
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
    if mode == 'T':
        # equality_test_battery()
        comparison_test_battery()
    elif mode == 'D':
        start = time.time()
        alice.executeSortDummy()
        end = time.time()
        print("Took", end-start, "seconds.")
    elif mode == 'M':
        k = 256 # security parameter

        mpl = multiprocessing.log_to_stderr()
        mpl.setLevel(logging.INFO)
        
        connections = Pipe()
        ipc_lock = Lock()
        # Queue for reporting output
        q = Queue()
        p_a = Process(target=alice.executePipeline, args=(connections[0], q, ipc_lock, k))
        p_b = Process(target=bob.executePipeline, args=(connections[1], q, ipc_lock, k,))
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
    elif mode == 'A':
        infile_a = '../data/shares_a_window='+str(n_time_bits)
        infile_b = '../data/shares_b_window='+str(n_time_bits)
        input_a, input_b = parse_input_files(infile_a, infile_b, n_rounds, n_time_bits, n_sensors, True)
        
        alice_input, bob_input = (input_a, input_b)
        
        if n_time_bits == 0:
            alice = Party(n_time_bits, n_symbol_bits, alice_input, "A", n_sensors)
            bob = Party(n_time_bits, n_symbol_bits, bob_input, "B", n_sensors)
            # give parties their precomputed OT files
            alice.setOTFiles(alice_sender_file, alice_recver_file)
            bob.setOTFiles(bob_sender_file, bob_recver_file)
            k = 256 # security parameter
            
            connections = Pipe()
            # Queue for reporting output
            q = Queue()
            # q_OT_count = Queue()
            p_a = Process(target=alice.executeMooreMachineRoundsOnly, args=(connections[0], q, k))
            p_b = Process(target=bob.executeMooreMachineRoundsOnly, args=(connections[1], q, k))
            start = time.time()
            p_a.start()
            p_b.start()
            p_a.join()
            p_b.join()
            end = time.time()
            # should be 1 thing in the queue: color stream
            if q.empty():
                    print("ERROR QUEUE SIZE")
                    exit(1)
            res = q.get()
            _s = ''
            for col in res:
                _s += str(col)
            print("Color Stream")
            print(_s)
            
            print("Took", end-start, "seconds.")
            alice_sender_file.close()
            alice_recver_file.close()
            bob_sender_file.close()
            bob_recver_file.close()
            n_states = 12                               # number of states in Moore machine = 12
            k_prime = k + math.ceil(math.log2(n_states))
            ots_due_to_symbol_bits_moore = \
                n_rounds * ot_recurrence.numOTs_moore_machine_eval_one_round(1, n_symbol_bits, 3, k_prime) # n sensors needed
            print("n =", len(input_a[0]), "len of network =", len(network.swaps))
            output_file = open('../Graphs/testing_output.txt', 'a')
            output_file.write(str(n_rounds) + " " + str(0) + " " + \
                str(end-start) + " " + str(0) + " " + \
                str(0) + " " + str(0) + " " + \
                str(ots_due_to_symbol_bits_moore) + " " + str(n_rounds) + "\n")
            output_file.close()
            # Can enable actual OT counts to verify by uncommenting a line in gate eval and passing a real queue
            # ots = 0
            # while(not q_OT_count.empty()):
            #     ots += q_OT_count.get_nowait()
            # ots *= 3
            # print("nOTs actual (sort):", ots)
        else:
            gc_exch = gmw.exchangeCirc()
            gc_comp = gmw.greaterThanCirc(n_time_bits)

            n = 2**(math.ceil(math.log2(len(input_a[0]))))
            print("n =", n)
            network = SortingNetwork('ODD-EVEN-MERGE',n)

            # both parties own the same gc, but will alter values
            alice = Party(n_time_bits, n_symbol_bits, alice_input, "A", n_sensors)
            bob = Party(n_time_bits, n_symbol_bits, bob_input, "B", n_sensors)
            alice.setGC(gc_comp, gc_exch, None)
            bob.setGC(copy.deepcopy(gc_comp), copy.deepcopy(gc_exch), None)
            # both own same network, will not alter values
            alice.setSortingNetwork(network)
            bob.setSortingNetwork(network)
            # give parties their precomputed OT files
            alice.setOTFiles(alice_sender_file, alice_recver_file)
            bob.setOTFiles(bob_sender_file, bob_recver_file)

            k = 256 # security parameter
            
            connections = Pipe()
            ipc_lock = Lock()
            # Queue for reporting output
            q = Queue()
            # q_OT_count = Queue()
            p_a = Process(target=alice.executePipeline, args=(connections[0], q, ipc_lock, k, None,))
            p_b = Process(target=bob.executePipeline, args=(connections[1], q, ipc_lock, k, None,))
            start = time.time()
            p_a.start()
            p_b.start()
            p_a.join()
            p_b.join()
            end = time.time()
            # should be 1 thing in the queue: color stream
            if q.empty():
                    print("ERROR QUEUE SIZE")
                    exit(1)
            res = q.get()
            _s = ''
            for col in res:
                _s += str(col)
            print("Color Stream")
            print(_s)
            # should be 2*n_rounds things in the queue: symbol stream
            # for i in range(n_rounds):
            #     if q.empty():
            #             print("ERROR QUEUE SIZE")
            #             exit(1)
            #     res = q.get()
            #     if q.empty():
            #             print("ERROR QUEUE SIZE")
            #             exit(1)
            #     res2 = q.get()
            #     xor_symbols = utils.mergeLists(res, res2)
            #     print("Symbols:", xor_symbols)
            
            print("Took", end-start, "seconds.")
            alice_sender_file.close()
            alice_recver_file.close()
            bob_sender_file.close()
            bob_recver_file.close()
            n_states = 12                               # number of states in Moore machine = 12
            k_prime = k + math.ceil(math.log2(n_states))
            [OTs_due_to_time_bits_sort, OTs_due_to_symbol_bits_sort, OT_rounds_sort] = \
                [a * n_rounds for a in ot_recurrence.num_OTs_sort(len(network.swaps), n_time_bits, n_symbol_bits)]
            ots_due_to_symbol_bits_moore = \
                n_rounds * ot_recurrence.numOTs_moore_machine_eval_one_round(2**n_time_bits, n_symbol_bits, 3, k_prime) # n sensors needed
            print("n =", len(input_a[0]), "len of network =", len(network.swaps))
            output_file = open('../Graphs/testing_output.txt', 'a')
            output_file.write(str(n_rounds) + " " + str(n_time_bits) + " " + \
                str(end-start) + " " + str(OTs_due_to_time_bits_sort) + " " + \
                str(OTs_due_to_symbol_bits_sort) + " " + str(OT_rounds_sort) + " " + \
                str(ots_due_to_symbol_bits_moore) + " " + str(n_rounds) + "\n")
            output_file.close()
            # Can enable actual OT counts to verify by uncommenting a line in gate eval and passing a real queue
            # ots = 0
            # while(not q_OT_count.empty()):
            #     ots += q_OT_count.get_nowait()
            # ots *= 3
            # print("nOTs actual (sort):", ots)
            print("nOTs theoretical (sort):", OTs_due_to_time_bits_sort + OTs_due_to_symbol_bits_sort)