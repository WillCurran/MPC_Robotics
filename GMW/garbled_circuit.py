from enum import Enum
## A GateType is a possible gate function. 
class GateType(Enum):
    NULL = -1
    NOT = 0
    XOR = 1
    AND = 2

## A Wire is a directed edge from one gate to another, along which a value is carried.
## We will use the Wire class in the Circuit's adjacency list
class Wire:
    # id_counter = 0

    def __init__(self, _value=None, _source=None, _destination=None):
        # self.id = id_counter
        self.value = _value
        self.source = _source
        self.destination = _destination
        # Wire.id_counter += 1


## A Gate is an implementation of a logic gate, with inbound and outbound Wires.
## Implemented as a Doubly-Linked Adjacency List?
class Gate:
    # return the gate function evaluation for this gate. Assumes 2 inputs max
    def gate_function_eval(self):
        if self.type == GateType.NOT:
            return ~self.inbound_wires[0].value     # careful, this assumes we have an unsigned integer value
        elif self.type == GateType.XOR:
            print("Wire vals:", self.inbound_wires[0].value, self.inbound_wires[1].value)
            print("Computing XOR. Got", self.inbound_wires[0].value ^ self.inbound_wires[1].value)
            return self.inbound_wires[0].value ^ self.inbound_wires[1].value
        elif self.type == GateType.AND: # TODO
            return self.inbound_wires[0].value
        return -1                                   # gate is of type NULL

    def __init__(self, _type=GateType.NULL):
        self.type = _type
        self.inbound_wires = []
        self.outbound_wires = []

    # assume gates are in topological order, so inbound wires must have a value
    def evalGate(self):
        if self.type != GateType.NULL:
            print("Gate Type:", self.type)
            if self.type == GateType.NOT:
                assert(self.inbound_wires[0].value != None) # debug
            else:
                assert(self.inbound_wires[0].value != None) # debug
                assert(self.inbound_wires[1].value != None) # debug
            gate_output = self.gate_function_eval()
            for outbound_wire in self.outbound_wires:
                outbound_wire.value = gate_output

## A GarbledCircuit is a data structure to represent a logical circuit. It is a topologically sorted graph.
## In this case, we support NOT, AND, and XOR gates.
class GarbledCircuit:
    # evaluate a circuit from left to right, and return final wire values
    # assumes initial wire values are set and gates are in topological order
    ########### CONSIDER INPUT/OUTPUT GATE LABELS ##############
    def evaluate_circuit(self):
        print("Evaluating circuit...")
        for gate in self.gates:
            gate.evalGate()
        return [wire.value for wire in self.gates[len(self.gates) - 1].inbound_wires] # assumes only 1 gate holds all of the output wires (false assumption)

    def __init__(self, _gates=[], _wires=[]):
        self.gates = _gates
        self.wires = _wires

    def insertGate(self, _type=GateType.NULL):
        new_gate = Gate(_type)
        self.gates.append(new_gate)
        return new_gate

    def insertWire(self, _value=None, _source=None, _destination=None):
        assert(_source in self.gates) # debug
        assert(_destination in self.gates) # debug
        new_wire = Wire(_value, _source, _destination)
        self.wires.append(new_wire)
        _source.outbound_wires.append(new_wire) # python immutability/pointer question. will this work for us?
        _destination.inbound_wires.append(new_wire) # python immutability/pointer question. will this work for us?
        return new_wire