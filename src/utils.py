import secrets
import math

# return 2 secret shared lists for the input list
def splitList(a, n_time_bits, n_symbol_bits):
    r = [secrets.randbits(n_time_bits+n_symbol_bits) for i in range(len(a))]
    s2 = [a[i] ^ r[i] for i in range(len(a))]
    return (r, s2)

# return 1 list for the two input secret shared lists
def mergeLists(a, b):
    return [a[i] ^ b[i] for i in range(len(a))]

# return an int {00..0 || 1^(j-i) || 00...0}, which has 1 values for bits in range [i,j]
# can perform logical and (&) with a number to get only those bits
def bitmask(i, j):
    assert(j >= i)
    return ((1 << (j+1 - i)) - 1) << i

def equality(a, b, n):
    # compute equality circuit (XOR -- NOT)
    if n == 1:
        # flip bits and bitmask, just like the circuit does for a NOT gate
        return ~(a ^ b) & 1
    # compute and circuit between two results
    half1 = math.floor(n/2.0)
    half2 = math.ceil(n/2.0)
    a_1 = a & bitmask(0, half1-1)
    b_1 = b & bitmask(0, half1-1)
    a_2 = (a >> half1) & bitmask(0, half2-1)
    b_2 = (b >> half1) & bitmask(0, half2-1)
    return equality(a_1, b_1, half1) & equality(a_2, b_2, half2)

def bitarrayToInt(b):
    num = 0
    for bit in b:
        assert(bit == 0 or bit == 1)
        num = (num << 1) | bit
    return num

# input: array of m-bit integers, index < m (idx is left->right)
# output: bitarray of bits found at index of each item
def getIthBitArray(a, m, idx):
    ret = []
    mask = bitmask(m - idx - 1, m - idx - 1) # from left->right
    for item in a:
        b = (mask & item) >> (m - idx - 1)
        ret.append(b)
    return ret

# input: array of m-bit integers, index < m (idx is left->right)
# output: int composed of bits found at index of each item
# essentially: if the array is treated as a bit matrix, then
#               getting a column of bits as an integer
def getIthBitInt(a, m, idx):
    ret = 0
    mask = bitmask(m - idx - 1, m - idx - 1) # from left->right
    for item in a:
        b = (mask & item) >> (m - idx - 1)
        ret = (ret << 1) | b
    return ret

# compare two numbers a, b (indices i, j of start of bit string we're looking at)
# def compare(a, b, i, j, n_bits_i, n_bits_j):
#     # just compute a greater than circuit for one bit
#     if(n_bits_i == n_bits_j == 1):
#         bit_a = a & bitmask(i,i) >> i
#         bit_b = b & bitmask(j,j) >> j
#         for wire in self.gc_comp.gates[0].outbound_wires:
#             wire.value = bit_a
#         for wire in self.gc_comp.gates[1].outbound_wires:
#             wire.value = bit_b
#         self.gc_comp.evaluate_circuit(connections, ipc_locks, self.id, self.n_time_bits)
#         return self.gc_comp.gates[-1].inbound_wires[2].value
#     # spawn a thread for each, not quite this simple.
#     return compare( a, b, n_bits//2, i, j + n_bits//2) ^ 
#         equality(a, b, n_bits, i, j) & 
#         compare(a, b, n_bits//2, j, j - n_bits//2)

