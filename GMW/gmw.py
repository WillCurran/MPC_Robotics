from garbled_circuit import *

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

