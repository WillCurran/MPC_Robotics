from garbled_circuit import *
import secrets
import utils

class Party:
    def __init__(self, _n_time_bits, _n_symbol_bits, _input, _id):
        self.n_time_bits = _n_time_bits
        self.n_symbol_bits = _n_symbol_bits
        self.gc_comp = None
        self.gc_exch = None
        self.network = None
        self.my_shares = _input
        self.comparison_bit = None              # Saved secret share result of the compare GC eval.
        self.id = _id
        self.time_bitmask = utils.bitmask(self.n_symbol_bits, self.n_time_bits + self.n_symbol_bits - 1)
        self.symbol_bitmask = utils.bitmask(0, self.n_symbol_bits - 1)
        self.max_val = (1 << (self.n_symbol_bits + self.n_time_bits)) - 1

    def setGC(self, gc_comp, gc_exch):
        self.gc_comp = gc_comp
        self.gc_exch = gc_exch

    def setSortingNetwork(self, network):
        self.network = network

    # i and j are indices of array we wish to compare
    # set wires to time values (extract time bits)
    def configCompare(self, i, j):
        for wire in self.gc_comp.gates[0].outbound_wires:
            wire.value = (self.my_shares[i] & self.time_bitmask) >> self.n_symbol_bits
        for wire in self.gc_comp.gates[1].outbound_wires:
            wire.value = (self.my_shares[j] & self.time_bitmask) >> self.n_symbol_bits

    # i and j are indices of array we wish to swap
    # First two wires get full payload.
    # Comparison inbound wire gets max value (0^k) or min value (1^k) so that 
    # each bit has access to comparison data.
    def configExchange(self, i, j):
        for wire in self.gc_exch.gates[0].outbound_wires:    # X
            wire.value = self.my_shares[i]
        for wire in self.gc_exch.gates[1].outbound_wires:    # Y
            wire.value = self.my_shares[j]
        for wire in self.gc_exch.gates[2].outbound_wires:    # C
            wire.value = self.comparison_bit

    # assumes one other party is also running this program concurrently in another process.
    # evaluate both compare and exchange circuits. Update values accordingly.
    def compareExchange(self, connections, ipc_locks, i, j):
        self.configCompare(i, j)
        self.gc_comp.evaluate_circuit(connections, ipc_locks, self.id, self.n_time_bits)
        if self.gc_comp.gates[-1].inbound_wires[2].value > 0:
            self.comparison_bit = self.max_val
        else:
            self.comparison_bit = 0
        # print(self.id, self.comparison_bit)
        # lock.acquire()
        # print("ID:", self.id)
        # print("comparison share:", self.comparison_bit)
        # lock.release()

        # connections[0] pipe end is ready, since compare circuit must have been computed at this point.
        self.configExchange(i, j)
        self.gc_exch.evaluate_circuit(connections, ipc_locks, self.id, self.n_time_bits+self.n_symbol_bits)
        self.my_shares[i] = self.gc_exch.gates[-1].inbound_wires[0].value
        self.my_shares[j] = self.gc_exch.gates[-1].inbound_wires[1].value
        # print(self.id, self.my_shares[i], self.my_shares[j])

    # execute a sort with another party on my sorting network
    # assume 2 bits of each element in list (1 time || 1 symbol) - run 2 GMW instances in parallel
    def executeSort(self, connections, q, ipc_locks):
        for level in self.network.swaps:
            for swap in level:
                self.compareExchange(connections, ipc_locks, swap[0], swap[1])
        q.put(self.my_shares)
