from enum import Enum
## A GateType is a possible gate function. 
class GateType(Enum):
    NULL = -1 # what do I need for this?
    NOT = 0
    XOR = 1
    AND = 2

## A Wire is a directed edge from one gate to another, along which a value is carried.
## We will use the Wire class in the Circuit's adjacency list
class Wire():
    def __init__(self, _value, _source=None, _destination=None):
        self.value = _value
        self.source = _source
        self.destination = _destination


## A Gate is an implementation of a logic gate, with inbound and outbound Wires.
## Assume that id increases topologically from left to right in a circuit. Must create gates in increasing order.
class Gate():
    id_counter = 0

    # return the gate function for this gate. Assumes 2 inputs max
    def gateFunction(self):
        if self.type == GateType.NOT:
            return lambda x, y : ~x     # careful, this assumes we have an unsigned integer value
        elif self.type == GateType.XOR:
            return lambda x, y : x ^ y
        elif self.type == GateType.AND: # TODO
            return lambda x, y : x

    def __init__(self, _type=GateType.NULL):
        self.id = id_counter
        self.type = _type
        self.adjacency_list = []
        Gate.id_counter += 1
    
    # if inbound wires have values, then set outbound wire values
    def evalGate():
        pass

## A GarbledCircuit is a data structure to represent a logical circuit. It is a topologically sorted graph.
## In this case, we support NOT, AND, and XOR gates.
class GarbledCircuit():

    # evaluate a circuit from left to right, and return final wire values
    def evaluateCircuit(self):
        pass

    def __init__(self, _gates=[], _wires=[]):
        self.gates = _gates
        self.wires = _wires
