import secrets

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
    assert(j+1 > i)
    return ((1 << (j+1 - i)) - 1) << i