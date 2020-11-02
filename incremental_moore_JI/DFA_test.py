from DFA_matrix import *

def test():
    dfa = {'alphabet': [0, 1],
        'states': 3, # or could represent as [0, 1, 2, ..., |Q|]
        'initial': 0,
        'terminals': [1],
        'delta': [(0, 1), (2, 2), (2, 2)], # index is which state. tuple contains the delta from that state if 0 or 1
        'outputs': [0b0000, 0b0001, 0b0010] # moore machine outputs. need to have some assumption of how many bits for garbling.
		}
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
    
    alice = Alice(dfa, x_a, n, k, s) # Alice creates keypair
    bob = Bob(x_b, dfa, alice.public_key, k, s) # Bob creates garbled matrix
    alice.init_state_and_pad(bob.init_state, bob.init_pad)

    print("M")
    print_M(bob.M)
    print("PER")
    print_M(bob.PER)
    print("PM")
    print_M(bob.PM)
    print("GM")
    print_M(bob.GM)
    for i in range(3):
        print("Iteration", i)
        bob.append_GM_row()
        print("M")
        print_M(bob.M)
        print("PER")
        print_M(bob.PER)
        print("PM")
        print_M(bob.PM)
        print("GM")
        print_M(bob.GM)
    
    print("Standard Eval:", evalDfa(bob.M, n, xor_input, dfa['initial']))
    print("Permuted Eval:", evalDfa(bob.PM, n, xor_input, bob.PER[0][dfa['initial'] ]))
    
    print("Performing OT garbled key transfer...")
    choices_enc = alice.encrypt_input_i()
    strings_enc = bob.send_garbled_key(choices_enc, alice.row_i)
    print("--------------------------------------------")
    print("Garbled Eval:", alice.step3(strings_enc, bob.GM))
    print("Performing OT garbled key transfer...")
    choices_enc = alice.encrypt_input_i()
    strings_enc = bob.send_garbled_key(choices_enc, alice.row_i)
    print("Garbled Eval:", alice.step3(strings_enc, bob.GM))
    print("Performing OT garbled key transfer...")
    choices_enc = alice.encrypt_input_i()
    strings_enc = bob.send_garbled_key(choices_enc, alice.row_i)
    print("Garbled Eval:", alice.step3(strings_enc, bob.GM))
    print("Performing OT garbled key transfer...")
    choices_enc = alice.encrypt_input_i()
    strings_enc = bob.send_garbled_key(choices_enc, alice.row_i)
    print("Garbled Eval:", alice.step3(strings_enc, bob.GM))

test()
