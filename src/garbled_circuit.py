from enum import Enum
import multiprocessing
from multiprocessing import Process, Pipe, Queue
import secrets
import utils
import threading
import queue
import ot4

## A GateType is a possible gate function. 
class GateType(Enum):
    NULL = -1
    NOT = 0
    XOR = 1
    AND = 2
    CIRCUIT = 3
    INPUT_BUS = 4
    OUTPUT_BUS = 5

## A Wire is a directed edge from one gate to another, along which a value is carried.
## We will use the Wire class in the Circuit's adjacency list
class Wire:
    def __init__(self, _value=None, _source=None, _destination=None):
        self.value = _value
        self.source = _source
        self.destination = _destination

## A Gate is an implementation of a logic gate, with inbound and outbound Wires.
## Implemented as a Doubly-Linked Adjacency List
class Gate:
    def __init__(self, _type=GateType.NULL):
        self.type = _type
        self.inbound_wires = []
        self.outbound_wires = []
        # self.visited = False
    
    def evalAndOnBitN(self, conn, ipc_lock, bit_i, sender_file, recver_file):
        # get n-th bit of inbound wires. if bit is there, we're dealing with a 1. else 0.
        mask = utils.bitmask(bit_i, bit_i)
        bit1 = int((mask & self.inbound_wires[0].value) > 0)
        bit0 = int((mask & self.inbound_wires[1].value) > 0)

        # other party has already encountered the gate
        if conn.poll():
            # perform 1 out of 4 OT with other party to get table
            # get table message, select proper share
            choice = bit1 * 2 + bit0
            res = ot4.receiver(conn, choice, recver_file)
            return res << bit_i
        # other party has not encountered the gate yet
        else:
            # one of us gets to make the table
            ipc_lock.acquire()
            # other party beat me to it
            if conn.poll():
                ipc_lock.release()
                choice = bit1 * 2 + bit0
                res = ot4.receiver(conn, choice, recver_file)
                return res << bit_i
            else:
                # Create table and send it over
                r = secrets.randbits(1)
                table = [r ^ ((bit1 ^ 0) & (bit0 ^ 0)),
                            r ^ ((bit1 ^ 0) & (bit0 ^ 1)),
                            r ^ ((bit1 ^ 1) & (bit0 ^ 0)),
                            r ^ ((bit1 ^ 1) & (bit0 ^ 1))
                        ]
                s = ot4.sender_sends_table(conn, table, sender_file)
                ipc_lock.release()
                ot4.sender_gets_choices_sends_corrections(conn, s, sender_file)
                return r << bit_i

    # return the gate function evaluation for this gate. Assumes 2 inputs
    def gate_function_eval(self, conn, ipc_lock, circuit_owner, n_bits, sender_file, recver_file):
        if self.type == GateType.NOT:
            if circuit_owner == "A":                                                # predetermined party (or requires coordination)
                return ~self.inbound_wires[0].value & utils.bitmask(0, n_bits-1)    # keep sign, flip all other pertinent bits
            return self.inbound_wires[0].value

        elif self.type == GateType.XOR:
            return self.inbound_wires[0].value ^ self.inbound_wires[1].value
        
        elif self.type == GateType.AND:
            val = 0
            for i in range(n_bits):
                val |= self.evalAndOnBitN(conn, ipc_lock, i, sender_file, recver_file)
            return val
        return -1                                   # gate is of type NULL

    def gate_function_eval_dummy(self, n_bits):
        if self.type == GateType.NOT:
            return ~self.inbound_wires[0].value & utils.bitmask(0, n_bits-1)    # keep sign, flip all other pertinent bits
        elif self.type == GateType.XOR:
            return self.inbound_wires[0].value ^ self.inbound_wires[1].value
        elif self.type == GateType.AND:
            return self.inbound_wires[0].value & self.inbound_wires[1].value
        return -1                                   # gate is of type NULL

    # assume gates are in topological order, so inbound wires must have a value
    def evaluate(self, conn, ipc_lock, circuit_owner, n_bits, sender_file, recver_file):
        if self.type == GateType.INPUT_BUS or self.type == GateType.OUTPUT_BUS:
            assert(self.canEvaluate())
            # pipe info thru - all inbound wires are of same value (is this property fully asserted at insertion?)
            if len(self.inbound_wires) > 0:
                for wire in self.outbound_wires:
                    wire.value = self.inbound_wires[0].value
        else:
            # print("Gate Type:", self.type)
            if self.type == GateType.NOT:
                assert(self.inbound_wires[0].value != None) # debug
            else:
                assert(self.inbound_wires[0].value != None) # debug
                assert(self.inbound_wires[1].value != None) # debug
            gate_output = self.gate_function_eval(
                conn, ipc_lock, circuit_owner, n_bits, 
                sender_file, recver_file
            )
            for outbound_wire in self.outbound_wires:
                outbound_wire.value = gate_output

    def evaluate_dummy(self, n_bits):
        if self.type == GateType.INPUT_BUS or self.type == GateType.OUTPUT_BUS:
            assert(self.canEvaluate())
            # pipe info thru - all inbound wires are of same value (is this property fully asserted at insertion?)
            if len(self.inbound_wires) > 0:
                for wire in self.outbound_wires:
                    wire.value = self.inbound_wires[0].value
        else:
            # print("Gate Type:", self.type)
            if self.type == GateType.NOT:
                assert(self.inbound_wires[0].value != None) # debug
            else:
                assert(self.inbound_wires[0].value != None) # debug
                assert(self.inbound_wires[1].value != None) # debug
            gate_output = self.gate_function_eval_dummy(n_bits)
            for outbound_wire in self.outbound_wires:
                outbound_wire.value = gate_output
                # print(outbound_wire, ":", gate_output)

    # assumption of topological order
    def canEvaluate(self):
        return True

    def print(self):
        print("Gate Type:", self.type)
        print("Inbound Wires:", self.inbound_wires)
        print("Outbound Wires:", self.outbound_wires)

## A GarbledCircuit is a data structure to represent a logical circuit. It is a topologically sorted graph.
## In this case, we support NOT, AND, and XOR gates.
## A GarbledCircuit is a collection of gates and wires, where gates may also be other circuits!
## Actual inheritance property is mostly a formality to show that a circuit may be treated as a gate.
class GarbledCircuit(Gate):
    # evaluate a circuit from left to right, and return final wire values
    #   - assumes initial wire values are set and gates are in topological order
    #   - assumes only 1 gate holds all of the output wires, can easily make a dummy gate to satisfy.
    def evaluate(self, conn, ipc_lock, circuit_owner, n_bits, sender_file, recver_file):
        for gate in self.gates:
            # wait to execute a circuit until all components are ready.
            if gate.canEvaluate():
                gate.evaluate(
                    conn, ipc_lock, circuit_owner, n_bits, 
                    sender_file, recver_file
                )
                # wipe inbound wires if circuit needs to be reused
                if isinstance(gate, GarbledCircuit):
                    gate.wipeInboundWires()

    def evaluate_dummy(self, n_bits):
        for gate in self.gates:
            # wait to execute a circuit until all components are ready.
            if gate.canEvaluate():
                gate.evaluate_dummy(n_bits)
                # wipe inbound wires if circuit needs to be reused
                if isinstance(gate, GarbledCircuit):
                    gate.wipeInboundWires()

    def __init__(self, _type):
        super().__init__(_type)
        self.input_busses = []       # used as docking ports for inbound wires from other circuits
        self.output_busses = []     # used as docking ports, when this circuit is a source of a wire
        self.gates = []
        self.wires = []

    def insertGate(self, _type=GateType.NULL, _gate=None):
        if _type == GateType.INPUT_BUS:
            new_gate = Gate(_type)
            self.gates.append(new_gate)
            self.input_busses.append(new_gate)
            return new_gate
        elif _type == GateType.OUTPUT_BUS:
            new_gate = Gate(_type)
            self.gates.append(new_gate)
            self.output_busses.append(new_gate)
            return new_gate
        elif _type == GateType.CIRCUIT:
            self.gates.append(_gate)
        else:
            new_gate = Gate(_type)
            self.gates.append(new_gate)
            return new_gate

    def canEvaluate(self):
        for bus in self.input_busses:
            for wire in bus.inbound_wires:
                if wire.value == None:
                    return False
        return True

    def wipeInboundWires(self):
        for bus in self.input_busses:
            for wire in bus.inbound_wires:
                wire.value = None

    # _source_group/_dest_group are used if the source or destination is a circuit to route wire properly.
    # it is the index of the wire that we desire the value for, on input side or output side.
    def insertWire(self, _value=None, _source=None, _destination=None, _source_group=None, _dest_group=None):
        assert((_source in self.gates) and (_destination in self.gates))
        if isinstance(_source, GarbledCircuit):
            assert(_source_group >= 0)
            assert(_source_group < len(_source.output_busses))
            if isinstance(_destination, GarbledCircuit):
                assert(_dest_group >= 0)
                assert(_dest_group < len(_destination.input_busses))
                new_wire = Wire(_value, _source.output_busses[_source_group], _destination.input_busses[_dest_group])
                _source.output_busses[_source_group].outbound_wires.append(new_wire)
                _destination.input_busses[_dest_group].inbound_wires.append(new_wire)
                self.wires.append(new_wire)
                return new_wire
            else:
                new_wire = Wire(_value, _source.output_busses[_source_group], _destination)
                _source.output_busses[_source_group].outbound_wires.append(new_wire)
                _destination.inbound_wires.append(new_wire)
                self.wires.append(new_wire)
                return new_wire
        elif isinstance(_destination, GarbledCircuit):
            assert(_dest_group >= 0)
            assert(_dest_group < len(_destination.input_busses))
            new_wire = Wire(_value, _source, _destination.input_busses[_dest_group])
            _source.outbound_wires.append(new_wire)
            _destination.input_busses[_dest_group].inbound_wires.append(new_wire)
            self.wires.append(new_wire)
            return new_wire
        else:
            new_wire = Wire(_value, _source, _destination)
            _source.outbound_wires.append(new_wire)
            _destination.inbound_wires.append(new_wire)
            self.wires.append(new_wire)
            return new_wire

    def print(self):
        print(self.gates)
        print(self.wires)

    def printGatesRecursive(self):
        for gate in self.gates:
            if isinstance(gate, GarbledCircuit):
                gate.printGatesRecursive()
            else:
                gate.print()
            print("\n")
