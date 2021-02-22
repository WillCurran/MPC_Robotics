import utils
import copy
from multiprocessing import Process, Pipe, Queue, Lock
import gmw
from sorting_network import *
from Party import *

# create a test circuit and run it across 2 parties with GMW
gc_exch = gmw.exchangeCirc()
gc_comp = gmw.comparatorCirc()
gc_exch_copy = copy.deepcopy(gc_exch)
gc_comp_copy = copy.deepcopy(gc_comp)

input_list = input("Input list (space delimited): ")   # assumes single bits
input_list = [int(s) for s in input_list.split(' ')]
n = len(input_list)
assert(n >= 2)
alice_input, bob_input = utils.splitList(input_list)
network = SortingNetwork('BUBBLE', n)

# both parties own the same gc, but will alter values
alice = Party(alice_input, "A")
bob = Party(bob_input, "B")
alice.setGC(gc_comp, gc_exch)
bob.setGC(gc_comp_copy, gc_exch_copy)
# both own same network, will not alter values
alice.setSortingNetwork(network)
bob.setSortingNetwork(network)

print("Alice shares:\n", alice.my_shares)
print("Bob shares:\n", bob.my_shares)

# evaluate circuits concurrently.
if __name__ == '__main__':
    i = 0
    j = 1
    parent_conn, child_conn = Pipe()
    q = Queue()
    lock = Lock()
    p_a = Process(target=alice.executeSort, args=(parent_conn, q, lock,))
    p_b = Process(target=bob.executeSort, args=(child_conn, q, lock,))
    p_a.start()
    p_b.start()
    p_a.join()
    p_b.join()
    # should be 2 things in the queue
    if(q.empty()):
        print("ERROR QUEUE SIZE")
        exit(-1)
    res1 = q.get()
    if(q.empty()):
        print("ERROR QUEUE SIZE")
        exit(-1)
    res2 = q.get()
    print("list after swap", utils.mergeLists(res1, res2))