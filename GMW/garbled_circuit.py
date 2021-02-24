from enum import Enum
from multiprocessing import Process, Pipe, Queue
import secrets
import utils
import threading
import queue

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

    def __init__(self, _type=GateType.NULL):
        self.type = _type
        self.inbound_wires = []
        self.outbound_wires = []
    
    def evalAndOnBitN(self, conn, ipc_lock, bit_i, q):
        # get n-th bit of inbound wires. if bit is there, we're dealing with a 1. else 0.
        mask = utils.bitmask(bit_i, bit_i)
        # itc_lock.acquire()
        bit1 = int((mask & self.inbound_wires[0].value) > 0)
        bit0 = int((mask & self.inbound_wires[1].value) > 0)
        # itc_lock.release()

        # other party has already encountered the gate
        if conn.poll():
            # get table message, select proper share
            table = conn.recv()
            i = bit1 * 2 + bit0
            q.put(table[i] << bit_i)
        # other party has not encountered the gate yet
        else:
            # one of us gets to make the table
            ipc_lock.acquire()
            # other party beat me to it
            if conn.poll():
                ipc_lock.release()
                table = conn.recv()
                i = bit1 * 2 + bit0
                q.put(table[i] << bit_i)
            else:
                # Create table and send it over
                r = secrets.randbelow(2)
                table = [r ^ ((bit1 ^ 0) & (bit0 ^ 0)),
                            r ^ ((bit1 ^ 0) & (bit0 ^ 1)),
                            r ^ ((bit1 ^ 1) & (bit0 ^ 0)),
                            r ^ ((bit1 ^ 1) & (bit0 ^ 1))
                        ]
                conn.send(table)
                ipc_lock.release()
                q.put(r << bit_i)

    # return the gate function evaluation for this gate. Assumes 2 inputs
    def gate_function_eval(self, connections, ipc_locks, is_alice, n_bits):
        if self.type == GateType.NOT:
            if is_alice:                                                            # predetermined party (or requires coordination)
                return ~self.inbound_wires[0].value & utils.bitmask(0, n_bits-1)    # keep sign, flip all other pertinent bits
            return self.inbound_wires[0].value

        elif self.type == GateType.XOR:
            return self.inbound_wires[0].value ^ self.inbound_wires[1].value
        
        ##### INSECURE WITHOUT OT ######
        elif self.type == GateType.AND:             # TODO - Implement 1-out-of-4 OT
            q = queue.Queue()
            # spawn a thread for each bit to execute OTs in parallel
            threads = [threading.Thread(target=self.evalAndOnBitN, args=(connections[i], ipc_locks[i], i, q,))
                        for i in range(n_bits)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            val = 0
            while(not q.empty()):
                val |= q.get()
            return val
        return -1                                   # gate is of type NULL

    # assume gates are in topological order, so inbound wires must have a value
    def evalGate(self, connections, ipc_locks, is_alice, n_bits):
        if self.type != GateType.NULL:
            # print("Gate Type:", self.type)
            if self.type == GateType.NOT:
                assert(self.inbound_wires[0].value != None) # debug
            else:
                assert(self.inbound_wires[0].value != None) # debug
                assert(self.inbound_wires[1].value != None) # debug
            gate_output = self.gate_function_eval(connections, ipc_locks, is_alice, n_bits)
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
    def evaluate_circuit(self, connections, ipc_locks, circuit_owner, n_bits):
        for gate in self.gates:
            gate.evalGate(connections, ipc_locks, circuit_owner=="A", n_bits)

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