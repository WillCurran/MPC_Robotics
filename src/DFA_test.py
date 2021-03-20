from DFA_matrix import *
import time
from multiprocessing import Process, Pipe, Queue, Lock


# conn is a bidirectional Pipe() open with Alice
# Bob's input in string form
# n is length of input
# k, s security parameters
def runBob(conn, moore_machine, bob_input, n, k, s):
    # recv alice's public key
    alice_pk = conn.recv()
    bob = Bob(conn, bob_input, moore_machine, alice_pk, k, s) # Bob creates garbled matrix, sends init state&pad

    for i in range(n):
        bob.append_GM_row()
    # send GM to Alice
    conn.send(bob.GM)

    for i in range(n):
        # bob must now receive choices_enc
        choices_enc = conn.recv()
        bob.send_garbled_key(choices_enc, i)

# conn is a bidirectional Pipe() open with Alice
# Bob's input in string form
# n is length of input
# k, s security parameters
def runBobDebug(conn, moore_machine, bob_input, n, k, s, xor_input):
    # recv alice's public key
    alice_pk = conn.recv()
    bob = Bob(conn, bob_input, moore_machine, alice_pk, k, s) # Bob creates garbled matrix, sends init state&pad

    # print("M")
    # print_M(bob.M)
    # print("PER")
    # print_M(bob.PER)
    # print("PM")
    # print_M(bob.PM)
    # print("GM")
    # print_M(bob.GM)
    for i in range(n):
        # print("Iteration", i)
        bob.append_GM_row()
    print("M")
    print_M(bob.M)
    print("PER")
    print_M(bob.PER)
    print("PM")
    print_M(bob.PM)
    print("GM")
    print_M(bob.GM)
    # send GM to Alice
    conn.send(bob.GM)
    # print("Standard Eval:", evalDfa(bob.M, n, xor_input, moore_machine['initial']))
    # print("Permuted Eval:", evalDfa(bob.PM, n, xor_input, bob.PER[0][moore_machine['initial'] ]))

    for i in range(n):
        # bob must now receive choices_enc
        choices_enc = conn.recv()
        bob.send_garbled_key(choices_enc, i)

# TODO - take moore machine out
# conn is a bidirectional Pipe() open with Bob
# Alice's input in string form
# n is length of input
# k, s security parameters
def runAlice(conn, q, alice_input, n, k, s):
    alice = Alice(conn, q, alice_input, n, k, s) # Alice creates keypair and sends public key to Bob
    # Alice waits for GM, initial state and pad from Bob
    (init_state, init_pad) = conn.recv()
    GM = conn.recv()
    alice.init_state_and_pad(init_state, init_pad)
    color_stream = []
    color_stream.append(alice.revealColor(GM))
    for i in range(n):
        # send encrypted choice
        alice.encrypt_input_i()
        # wait for garbled keys
        strings_enc = conn.recv()
        color_stream.append(alice.step3(strings_enc, GM))
    print("Color stream:", color_stream)
    return color_stream

# conn is a bidirectional Pipe() open with Bob
# Alice's input in string form
# n is length of input
# k, s security parameters
def runAliceDebug(conn, alice_input, n, k, s, moore_machine):
    alice = Alice(conn, moore_machine, alice_input, n, k, s) # Alice creates keypair and sends public key to Bob
    # Alice waits for GM, initial state and pad from Bob
    (init_state, init_pad) = conn.recv()
    GM = conn.recv()
    alice.init_state_and_pad(init_state, init_pad)
    print("Alice Initial Color:", alice.revealColor(GM))
    for i in range(n):
        print("Alice initiating OT garbled key transfer...")
        # send encrypted choice
        alice.encrypt_input_i()
        # wait for garbled keys
        strings_enc = conn.recv()
        print("Alice Garbled Eval:", alice.step3(strings_enc, GM))

def test():
    moore_machine = {'alphabet': [0, 1],
        'states': 3, # or could represent as [0, 1, 2, ..., |Q|]
        'initial': 0,
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

    # hopefully more scalable when we move OTs to batch precomputation
    k = 8 # security parameter
    s = 16 # statistical security parameter
    parent_conn, child_conn = Pipe()
    p_a = Process(target=runAlice, args=(parent_conn, x_a, n, k, s, moore_machine,))
    p_b = Process(target=runBob, args=(child_conn, moore_machine, x_b, n, k, s, xor_input,))
    start = time.time()
    p_a.start()
    p_b.start()
    p_a.join()
    p_b.join()
    end = time.time()
    print("Moore machine eval took", end-start, "seconds.")

# test()
