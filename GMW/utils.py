import secrets

# return 2 secret shared lists for the input list
# assume 1 bit each for now
def splitList(a):
    r = [secrets.randbits(1) for i in range(len(a))]
    s2 = [a[i] ^ r[i] for i in range(len(a))]
    return (r, s2)

# return 1 list for the two input secret shared lists
# assume 1 bit each for now
def mergeLists(a, b):
    return [a[i] ^ b[i] for i in range(len(a))]