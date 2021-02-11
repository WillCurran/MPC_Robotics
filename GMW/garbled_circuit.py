from enum import Enum
from multiprocessing import Process, Pipe, Queue
import secrets

## A GateType is a possible gate function. 
class GateType(Enum):
    NULL = -1
    NOT = 0
    XOR = 1
    AND = 2

## A Msg is used to communicate between parties
class Msg:
    def __init__(self, wire_vals, party):
        self.wire_vals = wire_vals
        self.party = party

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
## Implemented as a Doubly-Linked Adjacency List
class Gate:
    # return the gate function evaluation for this gate. Assumes 2 inputs
    def gate_function_eval(self, conn, lock, is_alice):
        if self.type == GateType.NOT:
            if is_alice:                                    # predetermined party (or requires coordination)
                return 1 - self.inbound_wires[0].value      # assumes 1 bit
            return self.inbound_wires[0].value

        elif self.type == GateType.XOR:
            return self.inbound_wires[0].value ^ self.inbound_wires[1].value
        
        ##### INSECURE WITHOUT OT ######
        elif self.type == GateType.AND:             # TODO - Implement 1-out-of-4 OT
            if conn.poll():             # other party has already encountered the gate
                # get table message, select proper share
                table = conn.recv()
                i = self.inbound_wires[0].value * 2 + self.inbound_wires[1].value
                return table[i]
            else:                       # other party has not encountered the gate yet
                # race to acquire lock
                lock.acquire()
                if conn.poll():         # other party beat me to it
                    lock.release()
                    table = conn.recv()
                    i = self.inbound_wires[0].value * 2 + self.inbound_wires[1].value
                    return table[i]
                
                # Create table and send it over
                r = secrets.randbelow(2)
                table = [r ^ ((self.inbound_wires[0].value ^ 0) & (self.inbound_wires[1].value ^ 0)),
                         r ^ ((self.inbound_wires[0].value ^ 0) & (self.inbound_wires[1].value ^ 1)),
                         r ^ ((self.inbound_wires[0].value ^ 1) & (self.inbound_wires[1].value ^ 0)),
                         r ^ ((self.inbound_wires[0].value ^ 1) & (self.inbound_wires[1].value ^ 1))
                        ]
                conn.send(table)
                lock.release()
                return r
                
        return -1                                   # gate is of type NULL

    def __init__(self, _type=GateType.NULL):
        self.type = _type
        self.inbound_wires = []
        self.outbound_wires = []

    # assume gates are in topological order, so inbound wires must have a value
    def evalGate(self, conn, lock, is_alice):
        if self.type != GateType.NULL:
            # print("Gate Type:", self.type)
            if self.type == GateType.NOT:
                assert(self.inbound_wires[0].value != None) # debug
            else:
                assert(self.inbound_wires[0].value != None) # debug
                assert(self.inbound_wires[1].value != None) # debug
            gate_output = self.gate_function_eval(conn, lock, is_alice)
            for outbound_wire in self.outbound_wires:
                outbound_wire.value = gate_output

    def print(self):
        print("Gate Type:", self.type)
        print("Inbound Wires:", self.inbound_wires)
        print("Outbound Wires:", self.outbound_wires)
## A GarbledCircuit is a data structure to represent a logical circuit. It is a topologically sorted graph.
## In this case, we support NOT, AND, and XOR gates.
class GarbledCircuit:
    # evaluate a circuit from left to right, and return final wire values
    #   - assumes initial wire values are set and gates are in topological order
    #   - assumes only 1 gate holds all of the output wires, can easily make a dummy gate to satisfy.
    def evaluate_circuit(self, conn, q, lock, circuit_owner):
        # print("Evaluating circuit...")
        for gate in self.gates:
            gate.evalGate(conn, lock, circuit_owner=="A")
        q.put(Msg([wire.value for wire in self.gates[len(self.gates) - 1].inbound_wires], circuit_owner))

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

    def print(self):
        print(self.gates)
        print(self.wires)