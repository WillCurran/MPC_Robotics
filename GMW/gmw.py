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
    # A makes a gc
    gc_A = GarbledCircuit()
    init_gate_A = gc_A.insertGate()
    init_gate_B = gc_A.insertGate()
    xor_gate = gc_A.insertGate(GateType.XOR) # just an XOR gate to start
    end_gate = gc_A.insertGate()

    gc_A.insertWire(_source=init_gate_A, _destination=xor_gate)
    gc_A.insertWire(_source=init_gate_B, _destination=xor_gate)
    gc_A.insertWire(_source=xor_gate, _destination=end_gate)

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
    alice.gc.wires[0].value = alice.xor_share
    alice.gc.wires[1].value = alice.r_other
    # Bob sets his wire values
    bob.gc.wires[0].value = bob.xor_share
    bob.gc.wires[1].value = bob.r_other
    print("Alice shares:", alice.xor_share, ", ", alice.r_other)
    print("Bob shares:", bob.xor_share, ", ", bob.r_other)

    # evaluate circuits concurrently. use lock for coordinating on AND gates.
    # if __name__ == '__main__':
    #     lock = Lock()
    #     Process(target=alice.gc.evaluate_circuit, args=(lock,)).start()

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

execGMW()
