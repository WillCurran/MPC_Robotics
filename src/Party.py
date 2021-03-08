from garbled_circuit import *
import secrets
import utils
import DFA_test as mm

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
        self.sender_file = None
        self.recver_file = None

    def setGC(self, gc_comp, gc_exch, gc_eq):
        self.gc_comp = gc_comp
        self.gc_exch = gc_exch
        self.gc_eq = gc_eq

    def setSortingNetwork(self, network):
        self.network = network

    def setOTFiles(self, sender_file_, recver_file_):
        self.sender_file = sender_file_
        self.recver_file = recver_file_

    def configEquality(self, i, j):
        for k in range(0, 2*self.n_time_bits, 2):
            bit = self.n_symbol_bits + self.n_time_bits - k//2 - 1
            self.gc_eq.input_busses[k].outbound_wires[0].value = (self.my_shares[i] >> bit) & 1
            self.gc_eq.input_busses[k+1].outbound_wires[0].value = (self.my_shares[j] >> bit) & 1
        # print("vals are:")
        # for k in range(2*self.n_time_bits):
        #     print(self.gc_eq.input_busses[k].outbound_wires[0].value)

    # i and j are indices of array we wish to compare
    # set wires to time values (extract time bits)
    def configCompare(self, i, j):
        # OLD for 1-bit times
        # for wire in self.gc_comp.input_busses[0].outbound_wires:
        #     wire.value = (self.my_shares[i] & self.time_bitmask) >> self.n_symbol_bits
        # for wire in self.gc_comp.input_busses[1].outbound_wires:
        #     wire.value = (self.my_shares[j] & self.time_bitmask) >> self.n_symbol_bits
        for k in range(0, 2*self.n_time_bits, 2):
            bit = self.n_symbol_bits + self.n_time_bits - k//2 - 1
            for wire in self.gc_comp.input_busses[k].outbound_wires:
                wire.value = (self.my_shares[i] >> bit) & 1
            for wire in self.gc_comp.input_busses[k+1].outbound_wires:
                wire.value = (self.my_shares[j] >> bit) & 1
        # print("vals are:")
        # for k in range(2*self.n_time_bits):
        #     print(self.gc_comp.input_busses[k].outbound_wires[0].value)

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
    def compareExchange(self, connections, ipc_lock, i, j):
        self.configCompare(i, j)
        # 1 bit wires on a tournament-wise evaluation!
        self.gc_comp.evaluate(
            connections, ipc_lock, self.id, 1, 
            self.sender_file, self.recver_file
        )
        if self.gc_comp.output_busses[0].inbound_wires[0].value == 1:
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
        self.gc_exch.evaluate(
            connections, ipc_lock, self.id, self.n_time_bits+self.n_symbol_bits,
            self.sender_file, self.recver_file
        )
        self.my_shares[i] = self.gc_exch.output_busses[0].inbound_wires[0].value
        self.my_shares[j] = self.gc_exch.output_busses[1].inbound_wires[0].value
        # print(self.id, self.my_shares[i], self.my_shares[j])

    # TODO - busy waiting issue with IPC? Did this go away with precomputed OTs?
    # execute a sort with another party on my sorting network
    # assume 2 bits of each element in list (1 time || 1 symbol) - run 2 GMW instances in parallel
    def executeSort(self, connections, q, ipc_lock):
        for level in self.network.swaps:
            for swap in level:
                self.compareExchange(connections, ipc_lock, swap[0], swap[1])
        q.put(self.my_shares)

    def executeMooreMachineEval(self, conn, k, s):
        moore_machine = {'alphabet': [0, 1],
        'states': 3, # or could represent as [0, 1, 2, ..., |Q|]
        'initial': 0,
        'delta': [(0, 1), (2, 2), (2, 2)], # index is which state. tuple contains the delta from that state if 0 or 1
        'outputs': [0b0000, 0b0001, 0b0010] # moore machine outputs. need to have some assumption of how many bits for garbling.
		}
        shared_input_str = ''
        # leading 0s in front of bits
        bit_format = '0' + str(self.n_symbol_bits) + 'b'
        for share in self.my_shares:
            shared_input_str += format(share & utils.bitmask(0, self.n_symbol_bits-1), bit_format)
        # print('bit format', bit_format)
        # print("symbols are", [share & utils.bitmask(0, self.n_symbol_bits) for share in self.my_shares])
        print(self.id, "Input is", shared_input_str)
        n = len(shared_input_str)
        if self.id == "A":
            mm.runAlice(conn, shared_input_str, n, k, s, moore_machine)
        else:
            mm.runBob(conn, moore_machine, shared_input_str, n, k, s, '')

    # execute sort and then moore machine eval
    def executePipeline(self, connections, q, ipc_lock, k, s):
        self.executeSort(connections, q, ipc_lock)
        # self.executeMooreMachineEval(connections[0], k, s)

    def executeSortDummy(self):
        for level in self.network.swaps:
            for swap in level:
                i = swap[0]
                j = swap[1]
                self.configCompare(i, j)
                self.gc_comp.evaluate_dummy(self.n_time_bits)
                if self.gc_comp.output_busses[0].inbound_wires[0].value > 0:
                    self.comparison_bit = self.max_val
                else:
                    self.comparison_bit = 0
                self.configExchange(i, j)
                self.gc_exch.evaluate_dummy(self.n_time_bits+self.n_symbol_bits)
                self.my_shares[i] = self.gc_exch.output_busses[0].inbound_wires[0].value
                self.my_shares[j] = self.gc_exch.output_busses[1].inbound_wires[0].value
        output_list = [(num >> self.n_symbol_bits, num & utils.bitmask(0, self.n_symbol_bits-1)) for num in self.my_shares]
        print(output_list)

    def executeEqualityDummy(self):
        self.configEquality(0, 1)
        # 1 bit wires on a tournament-wise evaluation!
        self.gc_eq.evaluate_dummy(1)
        return bool(self.gc_eq.output_busses[0].inbound_wires[0].value)
    
    def executeComparisonDummy(self):
        self.configCompare(0, 1)
        # 1 bit wires on a tournament-wise evaluation!
        self.gc_comp.evaluate_dummy(1)
        return bool(self.gc_comp.output_busses[0].inbound_wires[0].value)

    # # dynamic programming solution. store answers in array that I wipe every time we're looking at 2 different numbers
    # def equality(self, connections, ipc_lock, a, b, n_bits)
    #     return 0
    
    # # compare two numbers a, b (indices i, j of start of bit string we're looking at)
    # def compare(self, connections, ipc_lock, a, b, i, j, n_bits_i, n_bits_j):
    #     # just compute a greater than circuit for one bit
    #     if(n_bits_i == n_bits_j == 1):
    #         bit_a = a & utils.bitmask(i,i) >> i
    #         bit_b = b & utils.bitmask(j,j) >> j
    #         for wire in self.gc_comp.gates[0].outbound_wires:
    #             wire.value = bit_a
    #         for wire in self.gc_comp.gates[1].outbound_wires:
    #             wire.value = bit_b
    #         self.gc_comp.evaluate(connections, ipc_lock, self.id, self.n_time_bits)
    #         return self.gc_comp.gates[-1].inbound_wires[2].value
    #     # spawn a thread for each, not quite this simple.
    #     return self.compare(connections, ipc_lock, a, b, n_bits//2, i, j + n_bits//2) ^ 
    #         self.equality(connections, ipc_lock, a, b, n_bits, i, j) & 
    #         self.compare(connections, ipc_lock, a, b, n_bits//2, j, j - n_bits//2)
    