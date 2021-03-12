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
    def configCompare(self, i, j, round_num):
        for k in range(0, 2*self.n_time_bits, 2):
            bit = self.n_symbol_bits + self.n_time_bits - k//2 - 1
            for wire in self.gc_comp.input_busses[k].outbound_wires:
                wire.value = (self.my_shares[round_num][i] >> bit) & 1
            for wire in self.gc_comp.input_busses[k+1].outbound_wires:
                wire.value = (self.my_shares[round_num][j] >> bit) & 1
        # print("vals are:")
        # for k in range(2*self.n_time_bits):
        #     print(self.gc_comp.input_busses[k].outbound_wires[0].value)

    # i and j are indices of array we wish to swap
    # First two wires get full payload.
    # Comparison inbound wire gets max value (0^k) or min value (1^k) so that 
    # each bit has access to comparison data.
    def configExchange(self, i, j, round_num):
        for wire in self.gc_exch.input_busses[0].outbound_wires:
            wire.value = self.my_shares[round_num][i]
        for wire in self.gc_exch.input_busses[1].outbound_wires:
            wire.value = self.my_shares[round_num][j]
        for wire in self.gc_exch.input_busses[2].outbound_wires:
            wire.value = self.comparison_bit

    # assumes one other party is also running this program concurrently in another process.
    # evaluate both compare and exchange gates. Update values accordingly.
    def compareExchange(self, connections, ipc_lock, i, j, round_num):
        self.configCompare(i, j, round_num)
        # 1 bit wires on a tournament-wise evaluation!
        self.gc_comp.evaluate(
            connections, ipc_lock, self.id, 1, 
            self.sender_file, self.recver_file
        )
        if self.gc_comp.output_busses[0].inbound_wires[0].value == 1:
            self.comparison_bit = self.max_val
        else:
            self.comparison_bit = 0

        # connections[0] pipe end is ready, since compare circuit must have been computed at this point.
        self.configExchange(i, j, round_num)
        self.gc_exch.evaluate(
            connections, ipc_lock, self.id, self.n_time_bits+self.n_symbol_bits,
            self.sender_file, self.recver_file
        )
        self.my_shares[round_num][i] = self.gc_exch.output_busses[0].inbound_wires[0].value
        self.my_shares[round_num][j] = self.gc_exch.output_busses[1].inbound_wires[0].value
        # print(self.id, self.my_shares[i], self.my_shares[j])

    # TODO - busy waiting issue with IPC? Did this go away with precomputed OTs?
    # execute a sort with another party on my sorting network
    # assume 2 bits of each element in list (1 time || 1 symbol) - run 2 GMW instances in parallel
    def executeSort(self, connections, q, ipc_lock, round_num):
        for swap in self.network.swaps:
            self.compareExchange(connections, ipc_lock, swap[0], swap[1], round_num)
        q.put(self.my_shares[round_num])

    def executeMooreMachineEval(self, conn, k, s, round_num):
        moore_machine = {'alphabet': [0, 1],
        'states': 3, # or could represent as [0, 1, 2, ..., |Q|]
        'initial': 0,
        'delta': [(0, 1), (2, 2), (2, 2)], # index is which state. tuple contains the delta from that state if 0 or 1
        'outputs': [0b0000, 0b0001, 0b0010] # moore machine outputs. need to have some assumption of how many bits for garbling.
		}
        shared_input_str = ''
        # leading 0s in front of bits
        bit_format = '0' + str(self.n_symbol_bits) + 'b'
        for share in self.my_shares[round_num]:
            shared_input_str += format(share & utils.bitmask(0, self.n_symbol_bits-1), bit_format)
        # print('bit format', bit_format)
        # print("symbols are", [share & utils.bitmask(0, self.n_symbol_bits) for share in self.my_shares])
        # print(self.id, "Input is", shared_input_str)
        n = len(shared_input_str)
        if self.id == "A":
            mm.runAlice(conn, moore_machine['states'], shared_input_str, n, k, s)
        else:
            mm.runBob(conn, moore_machine, shared_input_str, n, k, s)

    # execute sort and then moore machine eval
    def executePipeline(self, connections, q, ipc_lock, k, s):
        # for all rounds
        for i in range(len(self.my_shares)):
            if self.id == "A":
                print("Sort, round", i, "...")
            self.executeSort(connections, q, ipc_lock, i)
            if self.id == "A":
                print("Moore machine, round", i, "...")
            self.executeMooreMachineEval(connections, k, s, i)

    def executeSortDummy(self):
        for swap in self.network.swaps:
            i = swap[0]
            j = swap[1]
            self.configCompare(i, j, 0)
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
        self.configEquality(0, 1, 0)
        # 1 bit wires on a tournament-wise evaluation!
        self.gc_eq.evaluate_dummy(1)
        return bool(self.gc_eq.output_busses[0].inbound_wires[0].value)
    
    def executeComparisonDummy(self):
        self.configCompare(0, 1, 0)
        # 1 bit wires on a tournament-wise evaluation!
        self.gc_comp.evaluate_dummy(1)
        return bool(self.gc_comp.output_busses[0].inbound_wires[0].value)

    