# based on Precomputing Oblivious Transfer paper by Beaver.
import secrets
from multiprocessing import Process, Pipe
import utils

# Receiver sends choice correction
def send_choice(conn, choice, ot_receiver_open_file):
    assert(choice == 0 or choice == 1)
    s = ot_receiver_open_file.readline()
    [d, r_d] = [int(x) for x in s.split()]
    conn.send(("e", choice ^ d))
    return r_d

# Sender receives B's choice and sends masked bits
def recv_choice_send_correction(conn, b0, b1, ot_sender_open_file):
    s = ot_sender_open_file.readline()
    r = [int(x) for x in s.split()]
    e = conn.recv()[1]
    assert(e == 0 or e == 1)
    conn.send(("x", (b0 ^ r[e], b1 ^ r[1-e])))
    
# Receiver receives masked bits and decrypts his choice
def recv_correction_decrypt(conn, choice, r_d):
    x = conn.recv()[1]
    return x[choice] ^ r_d

# Receiver sends choice correction
def send_choice_big(conn, choice, k, s, ot_receiver_open_file):
    # length of garbled key
    l = k + s
    # l choices concatenated for l bits
    choice_concat = 0
    # r_d concatenated
    r_d_concat = 0
    assert(choice == 0 or choice == 1)
    for i in range(l):
        s = ot_receiver_open_file.readline()
        [d, r_d] = [int(x) for x in s.split()]
        choice_concat = (choice_concat << 1) | (choice ^ d)
        r_d_concat = (r_d_concat << 1) | r_d
    # print("e", bin(choice_concat), "r_d", bin(r_d_concat))
    conn.send(("e", choice_concat))
    return r_d_concat

# Sender receives B's choice and sends masked strings, each of length k+s
def recv_choice_send_correction_big(conn, s0, s1, k, _s, ot_sender_open_file):
    l = k + _s
    # concatenated random bits from random OT file r = [r_0, r_1]
    e = conn.recv()[1]
    masked_s0 = 0
    masked_s1 = 0
    for i in range(l):
        s = ot_sender_open_file.readline()
        r = [int(x) for x in s.split()]
        e_bit = (e & utils.bitmask(l-i-1,l-i-1)) >> (l-i-1)
        masked_s0 = (masked_s0 << 1) | (((s0 & utils.bitmask(l-i-1,l-i-1)) >> (l-i-1)) ^ r[e_bit])
        masked_s1 = (masked_s1 << 1) | (((s1 & utils.bitmask(l-i-1,l-i-1)) >> (l-i-1)) ^ r[1-e_bit])
    # print("masked_s0", bin(masked_s0), "masked_s1", bin(masked_s1))
    conn.send(("x", (masked_s0, masked_s1)))
    
# Receiver receives masked bits and decrypts his choice
def recv_correction_decrypt_big(conn, choice, r_d_concat, k, s):
    x = conn.recv()[1]
    # print("x[", choice, "] =", x[choice])
    return x[choice] ^ r_d_concat

def sender(conn, b0, b1, ot_sender_open_file):
    print("Sender reporting for duty!")
    recv_choice_send_correction(conn, b0, b1, ot_sender_open_file)
    print("Sender done.")

def recver(conn, choice, ot_receiver_open_file):
    print("Receiver reporting for duty!")
    r_d = send_choice(conn, choice, ot_receiver_open_file)
    msg = recv_correction_decrypt(conn, choice, r_d)
    print("Receiver got", msg)

def test(b0, b1, choice):
    recver_file = open('b.txt', 'r')
    sender_file = open('a.txt', 'r')
    parent_conn, child_conn = Pipe()
    p_a = Process(target=recver, args=(parent_conn, choice, recver_file))
    p_b = Process(target=sender, args=(child_conn, b0, b1, sender_file))
    p_a.start()
    p_b.start()
    p_a.join()
    p_b.join()
    recver_file.close()
    sender_file.close()
