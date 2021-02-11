from garbled_circuit import *
import secrets
import copy
from multiprocessing import Process, Pipe, Queue, Lock

class Party:
    def __init__(self, _gc, _input):
        self.gc = _gc                           # my copy of the garbled circuit
        self.input = _input                     # my input (1-bit total for now)
        self.r = secrets.randbelow(2)
        self.xor_share = self.input ^ self.r
        self.r_other = None                     # the random share of the other party's secret input

# input 2 bits (secret-shared form): A, B. output 3 bits (secret-shared form): A < B, A == B, A > B
def comparatorCirc():
    # A --NOT1--AND1-- ---------(A < B)
    #   \  ----^    v
    #    \/         XOR--NOT3---(A = B)
    #    /\         ^
    #   /  ----v    |
    # B --NOT2--AND2-- ---------(A > B)
    gc = GarbledCircuit()
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
def compareExchangeCirc():
    # images available in resources/compare_exchange_logic
    gc = GarbledCircuit()
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
    gc_A = comparatorCirc()

    # B makes an identical gc
    gc_B = copy.deepcopy(gc_A)

    alice_input = int(input("Alice input: ")[0]) # assumes single bit
    bob_input = int(input("Bob input: ")[0])     # assumes single bit: TODO - support larger numbers
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
        lock = Lock()
        p_a = Process(target=alice.gc.evaluate_circuit, args=(parent_conn, q, lock, "A",))
        p_b = Process(target=bob.gc.evaluate_circuit, args=(child_conn, q, lock, "B",))
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
