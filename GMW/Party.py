from garbled_circuit import *
import secrets

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
            wire.value = self.my_shares[i]
        for wire in self.gc_comp.gates[1].outbound_wires:
            wire.value = self.my_shares[j]

    # i and j are indices of array we wish to swap
    def configExchange(self, i, j):
        for wire in self.gc_exch.gates[0].outbound_wires:    # X
            wire.value = self.my_shares[i]
        for wire in self.gc_exch.gates[1].outbound_wires:    # Y
            wire.value = self.my_shares[j]
        for wire in self.gc_exch.gates[2].outbound_wires:    # C
            wire.value = self.comparison_bit

    # assumes one other party is also running this program concurrently in another process
    # evaluate both compare and exchange circuits. Update values accordingly.
    def compareExchange(self, conn, q, lock, i, j):
        self.configCompare(i, j)
        self.gc_comp.evaluate_circuit(conn, q, lock, self.id)
        self.comparison_bit = self.gc_comp.gates[-1].inbound_wires[2].value
        # lock.acquire()
        # print("ID:", self.id)
        # print("comparison share:", self.comparison_bit)
        # lock.release()
        self.configExchange(i, j)
        self.gc_exch.evaluate_circuit(conn, q, lock, self.id)
        # update list with circuit's evaluation
        self.my_shares[i] = self.gc_exch.gates[-1].inbound_wires[0].value
        self.my_shares[j] = self.gc_exch.gates[-1].inbound_wires[1].value
        # q.put(self.my_shares)

    # execute a sort with another party on my sorting network
    def executeSort(self, conn, q, lock):
        for level in self.network.swaps:
            for swap in level:
                self.compareExchange(conn, q, lock, swap[0], swap[1])
        q.put(self.my_shares)
