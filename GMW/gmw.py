from garbled_circuit import *
import random
import copy
from multiprocessing import Process, Pipe, Queue

class Party:
    def __init__(self, _gc, _input):
        self.gc = _gc                           # my copy of the garbled circuit
        self.input = _input                     # my input (1-bit total for now)
        self.r = random.randint(0, 1)
        self.xor_share = self.input ^ self.r
        self.r_other = None                     # the random share of the other party's secret input

# create a test circuit and run it across 2 parties with GMW
def execGMW():
    # A makes a digital comparator GC
    # A --NOT1--AND1-- ---------(A < B)
    #   \  ----^    v
    #    \/         XOR--NOT3---(A = B)
    #    /\         ^
    #   /  ----v    |
    # B --NOT2--AND2-- ---------(A > B)
    gc_A = GarbledCircuit()
    init_gate_A = gc_A.insertGate()
    init_gate_B = gc_A.insertGate()
    not_1 = gc_A.insertGate(GateType.NOT)
    not_2 = gc_A.insertGate(GateType.NOT)
    and_1 = gc_A.insertGate(GateType.AND)
    and_2 = gc_A.insertGate(GateType.AND)
    xor = gc_A.insertGate(GateType.XOR)
    not_3 = gc_A.insertGate(GateType.NOT)
    end_gate = gc_A.insertGate()

    gc_A.insertWire(_source=init_gate_A, _destination=not_1)
    gc_A.insertWire(_source=init_gate_B, _destination=not_2)
    gc_A.insertWire(_source=init_gate_A, _destination=and_2)
    gc_A.insertWire(_source=init_gate_B, _destination=and_1)

    gc_A.insertWire(_source=not_1, _destination=and_1)
    gc_A.insertWire(_source=not_2, _destination=and_2)
    gc_A.insertWire(_source=and_1, _destination=xor)
    gc_A.insertWire(_source=and_2, _destination=xor)
    gc_A.insertWire(_source=xor, _destination=not_3)

    gc_A.insertWire(_source=and_1, _destination=end_gate)
    gc_A.insertWire(_source=not_3, _destination=end_gate)
    gc_A.insertWire(_source=and_2, _destination=end_gate)

    # B makes an identical gc
    gc_B = copy.deepcopy(gc_A)

    alice_input = int(input("Alice input: ")[0])
    bob_input = int(input("Bob input: ")[0])
    # both parties own the same gc
    alice = Party(gc_A, alice_input)
    bob = Party(gc_B, bob_input)
    # exchange shares
    alice.r_other = bob.r
    bob.r_other = alice.r

    # Alice sets her wire values
    for wire in alice.gc.gates[0].outbound_wires:
        wire.value = alice.xor_share
    for wire in alice.gc.gates[1].outbound_wires:
        wire.value = alice.r_other
    # Bob sets his wire values
    for wire in bob.gc.gates[0].outbound_wires:
        wire.value = bob.r_other
    for wire in bob.gc.gates[1].outbound_wires:
        wire.value = bob.xor_share
    print("Alice shares:", alice.xor_share, ", ", alice.r_other)
    print("Bob shares:", bob.xor_share, ", ", bob.r_other)

    # evaluate circuits concurrently.
    if __name__ == '__main__':
        parent_conn, child_conn = Pipe()
        q = Queue()
        p_a = Process(target=alice.gc.evaluate_circuit, args=(parent_conn, q, "A",))
        p_b = Process(target=bob.gc.evaluate_circuit, args=(child_conn, q, "B",))
        p_a.start()
        p_b.start()
        p_a.join()
        p_b.join()
        # should be 2 things in the queue for 1 output wire in this particular circuit
        res1 = q.get()
        print(res1.party, "got", res1.wire_vals)
        res2 = q.get()
        print(res2.party, "got", res2.wire_vals)
        # combine shares to compute result (reveal secret output) together
        result = [res1.wire_vals[i] ^ res2.wire_vals[i] for i in range(len(res1.wire_vals))]
        print("Actual result:", result)
        if result[0]:
            print("A < B")
        elif result[1]:
            print("A = B")
        else:
            print("A > B")

execGMW()
