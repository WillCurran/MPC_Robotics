from garbled_circuit import *
import secrets
import copy
from multiprocessing import Process, Pipe, Queue, Lock

class Party:
    def __init__(self, _input, _id):
        self.gc_comp = None
        self.gc_exch = None
        self.my_shares = _input
        self.comparison_bit = None              # Saved secret share result of the compare GC eval.
        self.id = _id

    def setGC(self, gc_comp):
        self.gc_comp = gc_comp
        # self.gc_exch = gc_exch

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
    def compareExchange(self, conn, q, lock, comp_circ, exch_circ):
        self.gc_comp = comp_circ
        self.gc_exch = exch_circ
        self.configCompare(0, 1)
        self.gc_comp.evaluate_circuit(conn, q, lock, self.id)
        self.comparison_bit = self.gc_comp.gates[-1].inbound_wires[0].value
        lock.acquire()
        print("ID:", self.id)
        print("comparison share:", self.comparison_bit)
        lock.release()
        self.configExchange(0, 1)
        self.gc_exch.evaluate_circuit(conn, q, lock, self.id)
        lock.acquire()
        print("ID:", self.id)
        print("X =", self.gc_exch.gates[-1].inbound_wires[0].value)
        print("Y =", self.gc_exch.gates[-1].inbound_wires[1].value)
        lock.release()


# input 2 bits (secret-shared form): A, B. output 3 bits (secret-shared form): A < B, A == B, A > B
def comparatorCirc():
    # A --NOT1--AND1-- ---------(A < B)
    #   \  ----^    v
    #    \/         XOR--NOT3---(A = B)
    #    /\         ^
    #   /  ----v    |
    # B --NOT2--AND2-- ---------(A > B)
    gc = GarbledCircuit([],[])
    init_gate_A = gc.insertGate()
    init_gate_B = gc.insertGate()
    not_1 = gc.insertGate(GateType.NOT)
    not_2 = gc.insertGate(GateType.NOT)
    and_1 = gc.insertGate(GateType.AND)
    and_2 = gc.insertGate(GateType.AND)
    xor = gc.insertGate(GateType.XOR)
    not_3 = gc.insertGate(GateType.NOT)
    end_gate = gc.insertGate()

    gc.insertWire(_source=init_gate_A, _destination=not_1)
    gc.insertWire(_source=init_gate_B, _destination=not_2)
    gc.insertWire(_source=init_gate_A, _destination=and_2)
    gc.insertWire(_source=init_gate_B, _destination=and_1)

    gc.insertWire(_source=not_1, _destination=and_1)
    gc.insertWire(_source=not_2, _destination=and_2)
    gc.insertWire(_source=and_1, _destination=xor)
    gc.insertWire(_source=and_2, _destination=xor)
    gc.insertWire(_source=xor, _destination=not_3)

    gc.insertWire(_source=and_1, _destination=end_gate)
    gc.insertWire(_source=not_3, _destination=end_gate)
    gc.insertWire(_source=and_2, _destination=end_gate)
    return gc

# input 3 bits (secret-shared form): X, Y, C. Output 2 bits (secret-shared form): if C, then Y, X. else X, Y
# a translation from Jonsson paper into a GMW garbled circuit
def exchangeCirc():
    # images available in resources/compare_exchange_logic
    gc = GarbledCircuit([],[])
    init_gate_X = gc.insertGate()
    init_gate_Y = gc.insertGate()
    init_gate_C = gc.insertGate()
    not_1 = gc.insertGate(GateType.NOT)
    and_1 = gc.insertGate(GateType.AND)
    and_2 = gc.insertGate(GateType.AND)
    and_3 = gc.insertGate(GateType.AND)
    and_4 = gc.insertGate(GateType.AND)
    xor_1 = gc.insertGate(GateType.XOR)
    xor_2 = gc.insertGate(GateType.XOR)
    end_gate = gc.insertGate()

    gc.insertWire(_source=init_gate_C, _destination=not_1)

    gc.insertWire(_source=init_gate_X, _destination=and_1)
    gc.insertWire(_source=init_gate_X, _destination=and_2)
    gc.insertWire(_source=init_gate_Y, _destination=and_3)
    gc.insertWire(_source=init_gate_Y, _destination=and_4)

    gc.insertWire(_source=init_gate_C, _destination=and_1)
    gc.insertWire(_source=not_1, _destination=and_2)
    gc.insertWire(_source=not_1, _destination=and_3)
    gc.insertWire(_source=init_gate_C, _destination=and_4)

    gc.insertWire(_source=and_1, _destination=xor_2)
    gc.insertWire(_source=and_2, _destination=xor_1)
    gc.insertWire(_source=and_3, _destination=xor_2)
    gc.insertWire(_source=and_4, _destination=xor_1)

    gc.insertWire(_source=xor_1, _destination=end_gate)
    gc.insertWire(_source=xor_2, _destination=end_gate)
    return gc

# create a test circuit and run it across 2 parties with GMW
def execGMW():
    gc_exch = exchangeCirc()
    gc_comp = comparatorCirc()

    alice_input = [0, 0]
    bob_input = [0, 0]
    alice_input[0] = int(input("Alice share1: ")[0]) # assumes single bit
    alice_input[1] = int(input("Alice share2: ")[0]) # assumes single bit
    bob_input[0] = int(input("Bob share1: ")[0])     # assumes single bit
    bob_input[1] = int(input("Bob share2: ")[0])     # assumes single bit: TODO - support larger numbers
    # both parties own the same gc
    alice = Party(alice_input, "A")
    bob = Party(bob_input, "B")

    # alice.setGC(gc_comp)
    # bob.setGC(copy.deepcopy(gc_comp))
    # set wire values, preparing comparison of items 0 and 1 in the secret-shared array
    # alice.configCompare(0, 1)
    # bob.configCompare(0, 1)

    print("Alice shares:", alice.my_shares)
    print("Bob shares:", bob.my_shares)

    # evaluate circuits concurrently.
    if __name__ == '__main__':
        parent_conn, child_conn = Pipe()
        q = Queue()
        lock = Lock()
        p_a = Process(target=alice.compareExchange, args=(parent_conn, q, lock, gc_comp, gc_exch,))
        p_b = Process(target=bob.compareExchange, args=(child_conn, q, lock, copy.deepcopy(gc_comp), copy.deepcopy(gc_exch),))
        p_a.start()
        p_b.start()
        p_a.join()
        p_b.join()
        # should be 2 things in the queue for 1 output wire in this particular circuit
        while(not q.empty()):
            res = q.get()
            print(res.party, "got", res.wire_vals)
        # combine shares to compute result (reveal secret output) together
        # result = [res1.wire_vals[i] ^ res2.wire_vals[i] for i in range(len(res1.wire_vals))]
        # print("Actual result:", result)
        # if result[0]:
        #     print("Item0 < Item1")
        # elif result[1]:
        #     print("Item0 = Item1")
        # else:
        #     print("Item0 > Item1")

execGMW()
