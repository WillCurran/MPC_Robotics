# Based on lecture materials by Sanjam Garg of UC Berkely

import ot_from_precomputed as ot
import secrets
from multiprocessing import Process, Pipe

def sender(conn, table, ot_sender_open_file):
    s = sender_sends_table(conn, table, ot_sender_open_file)
    sender_gets_choices_sends_corrections(conn, s, ot_sender_open_file)

# Bob generates a garbled table, sends to alice.
def sender_sends_table(conn, table, ot_sender_open_file):
    s = [secrets.randbits(1) for i in range(6)]
    table[0] = s[0] ^ s[2] ^ table[0]
    table[1] = s[0] ^ s[3] ^ table[1]
    table[2] = s[1] ^ s[4] ^ table[2]
    table[3] = s[1] ^ s[5] ^ table[3]
    conn.send(("table", table))
    return s
# Bob performs 3 OTs with Alice, initiated by Alice.
def sender_gets_choices_sends_corrections(conn, s, ot_sender_open_file):
    for i in range(0, 5, 2):
        ot.recv_choice_send_correction(conn, s[i], s[i+1], ot_sender_open_file)

# Alice receives garbled table, performs 3 OTs with Bob to decrypt chosen element
# 1 OT for most significant bit (2 options), 2 OTs for least significant bit (4 options)
# choice between 0 and 3
def receiver(conn, choice, ot_receiver_open_file):
    assert(choice >= 0 and choice <= 3)
    # get garbled table
    table = conn.recv()[1]
    # get values r_d for each OT
    r_d = [
        ot.send_choice(conn, (choice & 2) >> 1, ot_receiver_open_file),
        ot.send_choice(conn, choice & 1, ot_receiver_open_file),
        ot.send_choice(conn, choice & 1, ot_receiver_open_file)
    ]
    s_i = ot.recv_correction_decrypt(conn, (choice & 2) >> 1, r_d[0])
    s_j = ot.recv_correction_decrypt(conn, choice & 1, r_d[1])
    s_k = ot.recv_correction_decrypt(conn, choice & 1, r_d[2])
    # reconstruct chosen table entry
    if choice & 2:
        # print("Alice got", s_i ^ s_k ^ table[choice])
        return s_i ^ s_k ^ table[choice]
    # print("Alice got", s_i ^ s_j ^ table[choice])
    return s_i ^ s_j ^ table[choice]

def test(table, choice):
    recver_file = open('b.txt', 'r')
    sender_file = open('a.txt', 'r')
    parent_conn, child_conn = Pipe()
    p_a = Process(target=receiver, args=(parent_conn, choice, recver_file))
    p_b = Process(target=sender, args=(child_conn, table, sender_file))
    p_a.start()
    p_b.start()
    p_a.join()
    p_b.join()
    recver_file.close()
    sender_file.close()

# test([0, 1, 0, 1], 2)