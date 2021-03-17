from DFA_matrix import *

def test():
    dfa = {'alphabet': [0, 1],
        'states': 3, # or could represent as [0, 1, 2, ..., |Q|]
        'initial': 0,
        'terminals': [1],
        'delta': [(0, 1), (2, 2), (2, 2)], # index is which state. tuple contains the delta from that state if 0 or 1
        'outputs': [0b0000, 0b0001, 0b0010] # moore machine outputs. need to have some assumption of how many bits for garbling.
		}
    together_filter = {'alphabet': [0,1,2,3], # 3 is null, null must be all 1s in bits
        'states': 6, # or could represent as [0, 1, 2, ..., |Q|]
        'initial': 0,
        'delta': [(1,2,3,0), (0,3,2,1), (3,0,5,2), (2,4,0,3),(0,3,2,4),(0,3,2,5)], # index is which state. tuple contains the delta from that state if 0 or 1
        'outputs': ['blue','red','blue','blue','red', 'red']#(01,10)(11,00)(20,02)(12,21)(11,22)(22,00)
		}
    binary_together_filter = {'alphabet': [0,1],
        'states': 18, #each non-binary state needs two states per number of bits needed for alphabet
        'initial': 0,
        # index is which state. tuple contains the delta from that state if 0 or 1
        'delta': [
        (1,2),(3,6),(9,0),(4,5),(0,9),(6,3),(7,8),(9,0),(15,6),(10,11),(6,12),(0,9),(13,14),(0,9),(6,12),(16,17),(0,9),(6,15)],
        'outputs': [0,2,2,1,2,2,0,2,2,0,2,2,1,2,2,1,2,2] # 0 is blue, 1 is red, 2 is bogus
		}
    minimal_together_filter = {'alphabet': [0,1,2,3], # 3 is null, null must be all 1s in bits
        'states': 4, # or could represent as [0, 1, 2, ..., |Q|]
        'initial': 0,
        'delta': [(1,3,2,0), (0,2,3,1), (3,1,0,2), (2,0,1,3)], # index is which state. tuple contains the delta from that state if 0 or 1
        'outputs': ['blue','blue','blue','red'] # moore machine outputs. need to have some assumption of how many bits for garbling.
		}
    minimal_binary_together_filter = {'alphabet': [0,1],
        'states': 12, #each non-binary state needs two states per number of bits needed for alphabet
        'initial': 0,
        # index is which state. tuple contains the delta from that state if 0 or 1
        'delta': [(1,2),(3,9),(6,0), (4,5),(0,6),(9,3), (7,8),(9,3),(0,6), (10,11),(6,0),(3,9)],
        'outputs': [0,2,2,0,2,2,0,2,2,1,2,2] # 0 is blue, 1 is red, 2 is bogus
		}
    dfa = minimal_binary_together_filter
    x_a = input("Alice's input: ")
    x_b = input("Bob's input: ")
    n = len(x_a)
    if n != len(x_b):
        print('non-matching input size.')
        return
    xor_input = ''
    for i in range(n):
        xor_input += str(int(x_a[i]) ^ int(x_b[i]))

    k = 4 # security parameter
    s = 8 # statistical security parameter

    M = DfaMat(dfa,n)
    print("Standard Eval:", evalDfa(M, n, xor_input, dfa['initial']))
    
test()
