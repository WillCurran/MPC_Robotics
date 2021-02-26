from garbled_circuit import *
import secrets
import utils

class Party:
    def __init__(self, _n_time_bits, _n_symbol_bits, _input, _id):
        self.n_time_bits = _n_time_bits
        self.n_symbol_bits = _n_symbol_bits
        self.gc_comp = None
        self.gc_exch = None
        self.gc_eq = None
        self.network = None
        self.my_shares = _input
        self.comparison_bit = None              # Saved secret share result of the compare GC eval.
        self.id = _id
        self.time_bitmask = utils.bitmask(self.n_symbol_bits, self.n_time_bits + self.n_symbol_bits - 1)
        self.symbol_bitmask = utils.bitmask(0, self.n_symbol_bits - 1)
        self.max_val = (1 << (self.n_symbol_bits + self.n_time_bits)) - 1

    def setGC(self, gc_comp, gc_exch, gc_eq):
        self.gc_comp = gc_comp
        self.gc_exch = gc_exch
        self.gc_eq = gc_eq

    def setSortingNetwork(self, network):
        self.network = network

    def configEquality(self, i, j):
        self.gc_eq.input_busses[0].outbound_wires[0].value = self.my_shares[i] >> self.n_symbol_bits & utils.bitmask(0,0)
        self.gc_eq.input_busses[1].outbound_wires[0].value = self.my_shares[j] >> self.n_symbol_bits & utils.bitmask(0,0)
        # for k in range(self.n_time_bits//2):
        #     for wire in self.gc_eq.input_busses[k].outbound_wires:
        #         wire.value = (self.my_shares[i] & utils.bitmask(k,k)) >> (self.n_symbol_bits + k)
        # for k in range(self.n_time_bits//2, self.n_time_bits):
        #     for wire in self.gc_eq.input_busses[k].outbound_wires:
        #         wire.value = (self.my_shares[j] & utils.bitmask(k,k)) >> (self.n_symbol_bits + k)

    def executeEquality(self, connections, q, ipc_locks):
        self.configEquality(0, 1)
        self.gc_eq.evaluate(connections, ipc_locks, self.id, 1)
        print(self.gc_eq.output_busses[0].inbound_wires[0].value)

    # i and j are indices of array we wish to compare
    # set wires to time values (extract time bits)
    def configCompare(self, i, j):
        for wire in self.gc_comp.input_busses[0].outbound_wires:
            wire.value = (self.my_shares[i] & self.time_bitmask) >> self.n_symbol_bits
        for wire in self.gc_comp.input_busses[1].outbound_wires:
            wire.value = (self.my_shares[j] & self.time_bitmask) >> self.n_symbol_bits

    # i and j are indices of array we wish to swap
    # First two wires get full payload.
    # Comparison inbound wire gets max value (0^k) or min value (1^k) so that 
    # each bit has access to comparison data.
    def configExchange(self, i, j):
        for wire in self.gc_exch.input_busses[0].outbound_wires:
            wire.value = self.my_shares[i]
        for wire in self.gc_exch.input_busses[1].outbound_wires:
            wire.value = self.my_shares[j]
        for wire in self.gc_exch.input_busses[2].outbound_wires:
            wire.value = self.comparison_bit

    # assumes one other party is also running this program concurrently in another process.
    # evaluate both compare and exchange gates. Update values accordingly.
    def compareExchange(self, connections, ipc_locks, i, j):
        self.configCompare(i, j)
        self.gc_comp.evaluate(connections, ipc_locks, self.id, self.n_time_bits)
        if self.gc_comp.output_busses[2].inbound_wires[0].value > 0:
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
        self.gc_exch.evaluate(connections, ipc_locks, self.id, self.n_time_bits+self.n_symbol_bits)
        self.my_shares[i] = self.gc_exch.output_busses[0].inbound_wires[0].value
        self.my_shares[j] = self.gc_exch.output_busses[1].inbound_wires[0].value
        # print(self.id, self.my_shares[i], self.my_shares[j])

    # execute a sort with another party on my sorting network
    # assume 2 bits of each element in list (1 time || 1 symbol) - run 2 GMW instances in parallel
    def executeSort(self, connections, q, ipc_locks):
        for level in self.network.swaps:
            for swap in level:
                self.compareExchange(connections, ipc_locks, swap[0], swap[1])
        q.put(self.my_shares)

    # # dynamic programming solution. store answers in array that I wipe every time we're looking at 2 different numbers
    # def equality(self, connections, ipc_locks, a, b, n_bits)
    #     return 0
    
    # # compare two numbers a, b (indices i, j of start of bit string we're looking at)
    # def compare(self, connections, ipc_locks, a, b, i, j, n_bits_i, n_bits_j):
    #     # just compute a greater than circuit for one bit
    #     if(n_bits_i == n_bits_j == 1):
    #         bit_a = a & utils.bitmask(i,i) >> i
    #         bit_b = b & utils.bitmask(j,j) >> j
    #         for wire in self.gc_comp.gates[0].outbound_wires:
    #             wire.value = bit_a
    #         for wire in self.gc_comp.gates[1].outbound_wires:
    #             wire.value = bit_b
    #         self.gc_comp.evaluate(connections, ipc_locks, self.id, self.n_time_bits)
    #         return self.gc_comp.gates[-1].inbound_wires[2].value
    #     # spawn a thread for each, not quite this simple.
    #     return self.compare(connections, ipc_locks, a, b, n_bits//2, i, j + n_bits//2) ^ 
    #         self.equality(connections, ipc_locks, a, b, n_bits, i, j) & 
    #         self.compare(connections, ipc_locks, a, b, n_bits//2, j, j - n_bits//2)
    