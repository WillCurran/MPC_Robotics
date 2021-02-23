import secrets

# return 2 secret shared lists for the input list
# assume 1 bit each for now
def splitList(a):
    r = [[secrets.randbits(1), secrets.randbits(1)] for i in range(len(a))]
    s2 = [[a[i][0] ^ r[i][0], a[i][1] ^ r[i][1]] for i in range(len(a))]
    return (r, s2)

# return 1 list for the two input secret shared lists
# assume 1 bit each for now
def mergeLists(a, b):
    return [[a[i][0] ^ b[i][0], a[i][1] ^ b[i][1]] for i in range(len(a))]