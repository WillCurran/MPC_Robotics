import ot_from_precomputed as ot
import secrets
import sys
from multiprocessing import Process, Pipe

# alice sends k+s choices (1 overall choice) - need to keep track of r_d
def alice_send_choices_enc(conn, choice_a, k, ot_receiver_open_file):
    # return ot.send_choice(conn, choice_a, ot_receiver_open_file)
    return ot.send_choice_big(conn, choice_a, k, ot_receiver_open_file)

# bob sends 2 strings, masked with original OT bits
def bob_send_strings_enc(conn, choice_b, strings_b, k, ot_sender_open_file):
    if choice_b:
        # ot.recv_choice_send_correction(conn, strings_b[1], strings_b[0], ot_sender_open_file)
        return ot.recv_choice_send_correction_big(conn, strings_b[1], strings_b[0], k, ot_sender_open_file)
    else:
        # ot.recv_choice_send_correction(conn, strings_b[0], strings_b[1], ot_sender_open_file)
        return ot.recv_choice_send_correction_big(conn, strings_b[0], strings_b[1], k, ot_sender_open_file)
        
# alice decrypts string
def alice_compute_result(conn, choice_a, r_d, k):
    # return ot.recv_correction_decrypt(conn, choice_a, r_d)
    return ot.recv_correction_decrypt_big(conn, choice_a, r_d, k)

# Assumes global pk_shared and sk_only_a defined as pallier keys.
def example_execution_OT_with_JC(choice_a, choice_b, strings_b, fd_a, fd_b, k, s):
    if (choice_a != 0 and choice_a != 1) or (choice_b != 0 and choice_b != 1):
        print("Choices must be in {0, 1}.")
        return
    expected_result_i = choice_a ^ choice_b
    expected_result = strings_b[expected_result_i]
    print("Input choices are")
    print("A: " + str(choice_a))
    print("B: " + str(choice_b))
    print("B's strings are: '" + str(strings_b[0]) + "', '" + str(strings_b[1]) + "'")
    print("Protocol should choose the " + str(expected_result_i) + 
            "-th string, which is " + str(expected_result) + ".")
    print("Executing Oblivious Transfer with Joint Choice ...")
    a, b = Pipe()
    # Alice begins by sending Bob her choice correction
    r_d = alice_send_choices_enc(a, choice_a, k, s, fd_a)
    # Bob now mixes his choice with his string order and sends to Alice
    bob_send_strings_enc(b, choice_b, strings_b, k, s, fd_b)
    # Alice decrypts
    alice_plaintext_result = alice_compute_result(a, choice_a, r_d, k, s)
    print("Alice's result: " + str(alice_plaintext_result))

# fd_alice = open('b.txt')
# fd_bob = open('a.txt')
# choice_a = 1
# choice_b = 1
# strings = [10000000, 1]
# k = 1
# s = 1034
# example_execution_OT_with_JC(choice_a, choice_b, strings, fd_alice, fd_bob, k, s)
# fd_alice.close()
# fd_bob.close()