import utils
import copy
from multiprocessing import Process, Pipe, Queue, Lock
import gmw
from sorting_network import *
from Party import *

# create a test circuit and run it across 2 parties with GMW
gc_exch = gmw.exchangeCirc()
gc_comp = gmw.comparatorCirc()

times = input("Input times (space delimited): ")   # assumes single bits
symbols = input("Input symbols (space delimited): ")   # assumes single bits
times = [int(s) for s in times.split(' ')]
symbols = [int(s) for s in symbols.split(' ')]
assert(len(times) == len(symbols))
# symbols = [ord(c) for c in symbols.split(' ')]
n = len(times)
assert(n >= 2)
input_list = list(zip(times, symbols))
alice_input, bob_input = utils.splitList(input_list)
network = SortingNetwork('BUBBLE', n)

# both parties own the same gc, but will alter values
alice = Party(alice_input, "A")
bob = Party(bob_input, "B")
alice.setGC(gc_comp, [gc_exch, copy.deepcopy(gc_exch)])
bob.setGC(copy.deepcopy(gc_comp), [copy.deepcopy(gc_exch), copy.deepcopy(gc_exch)])
# both own same network, will not alter values
alice.setSortingNetwork(network)
bob.setSortingNetwork(network)

print("Alice shares:\n", alice.my_shares)
print("Bob shares:\n", bob.my_shares)

# evaluate circuits concurrently.
if __name__ == '__main__':
    i = 0
    j = 1
    connections = [Pipe() for i in range(2)]
    locks = [Lock() for i in range(3)]
    q = Queue()
    p_a = Process(target=alice.executeSort, args=([a[0] for a in connections], q, locks,))
    p_b = Process(target=bob.executeSort, args=([a[1] for a in connections], q, locks,))
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