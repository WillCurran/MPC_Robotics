from garbled_circuit import *
import secrets
import threading

class Party:
    def __init__(self, _input, _id):
        self.gc_comp = None
        self.gc_exch = None
        self.network = None
        self.my_shares = _input
        self.comparison_bit = None              # Saved secret share result of the compare GC eval.
        self.id = _id

    def setGC(self, gc_comp, gc_exch):
        self.gc_comp = gc_comp
        self.gc_exch = gc_exch

    def setSortingNetwork(self, network):
        self.network = network

    # i and j are indices of array we wish to compare
    def configCompare(self, i, j):
        for wire in self.gc_comp.gates[0].outbound_wires:
            wire.value = self.my_shares[i][0]
        for wire in self.gc_comp.gates[1].outbound_wires:
            wire.value = self.my_shares[j][0]

    # i and j are indices of array we wish to swap
    # threadsafe, as long as no other thread with same k? rationale - not changing data at top array level
    def configExchange(self, i, j, k):
        for wire in self.gc_exch[k].gates[0].outbound_wires:    # X
            wire.value = self.my_shares[i][k]
        for wire in self.gc_exch[k].gates[1].outbound_wires:    # Y
            wire.value = self.my_shares[j][k]
        for wire in self.gc_exch[k].gates[2].outbound_wires:    # C
            wire.value = self.comparison_bit

    def exchange(self, conn, locks_cross_process, lock_cross_thread, i, j, k):
        self.configExchange(i, j, k)
        self.gc_exch[k].evaluate_circuit(conn, locks_cross_process[k], self.id)
        # update list with circuit's evaluation
        lock_cross_thread.acquire()
        self.my_shares[i][k] = self.gc_exch[k].gates[-1].inbound_wires[0].value
        self.my_shares[j][k] = self.gc_exch[k].gates[-1].inbound_wires[1].value
        lock_cross_thread.release()

    # assumes one other party is also running this program concurrently in another process.
    # evaluate both compare and exchange circuits. Update values accordingly.
    def compareExchange(self, connections, locks, i, j):
        self.configCompare(i, j)
        self.gc_comp.evaluate_circuit(connections[0], locks[0], self.id)
        self.comparison_bit = self.gc_comp.gates[-1].inbound_wires[2].value
        # lock.acquire()
        # print("ID:", self.id)
        # print("comparison share:", self.comparison_bit)
        # lock.release()

        # spawn a thread for each bit / circuit
        # connections[0] pipe end is ready, since compare circuit must have been computed at this point.
        t0 = threading.Thread(target=self.exchange, args=(connections[0], [locks[0], locks[1]], locks[2], i, j, 0,))
        t1 = threading.Thread(target=self.exchange, args=(connections[1], [locks[0], locks[1]], locks[2], i, j, 1,))
        t0.start()
        t1.start()
        t0.join()
        t1.join()

    # execute a sort with another party on my sorting network
    # assume 2 bits of each element in list (1 time || 1 symbol) - run 2 GMW instances in parallel
    def executeSort(self, connections, q, locks):
        for level in self.network.swaps:
            for swap in level:
                self.compareExchange(connections, locks, swap[0], swap[1])
        q.put(self.my_shares)
