from enum import Enum
from multiprocessing import Process, Pipe, Queue
import secrets
import utils
import threading
import queue
import ot

## A GateType is a possible gate function. 
class GateType(Enum):
    NULL = -1
    NOT = 0
    XOR = 1
    AND = 2
    CIRCUIT = 3
    INPUT_BUS = 4
    OUTPUT_BUS = 5

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
        # self.visited = False
    
    def evalAndOnBitN(self, conn, ipc_lock, bit_i, q):
        # get n-th bit of inbound wires. if bit is there, we're dealing with a 1. else 0.
        mask = utils.bitmask(bit_i, bit_i)
        # itc_lock.acquire()
        bit1 = int((mask & self.inbound_wires[0].value) > 0)
        bit0 = int((mask & self.inbound_wires[1].value) > 0)
        # itc_lock.release()

        # other party has already encountered the gate
        if conn.poll():
            # perform 1 out of 4 OT with other party to get table
            # send public keys, then wait for encrypted 
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
    def gate_function_eval(self, connections, ipc_locks, circuit_owner, n_bits):
        if self.type == GateType.NOT:
            if circuit_owner == "A":                                                # predetermined party (or requires coordination)
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
    def evaluate(self, connections, ipc_locks, circuit_owner, n_bits):
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
            gate_output = self.gate_function_eval(connections, ipc_locks, circuit_owner, n_bits)
            # ipc_locks[0].acquire()
            # print(circuit_owner, ": Value for gateType", self.type, "computed to be", gate_output)
            # ipc_locks[0].release()
            for outbound_wire in self.outbound_wires:
                outbound_wire.value = gate_output

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
    def evaluate(self, connections, ipc_locks, circuit_owner, n_bits):
        for gate in self.gates:
            # wait to execute a circuit until all components are ready.
            if gate.canEvaluate():
                gate.evaluate(connections, ipc_locks, circuit_owner, n_bits)
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
