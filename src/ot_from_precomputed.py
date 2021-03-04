# based on Precomputing Oblivious Transfer paper by Beaver.
import secrets
from multiprocessing import Process, Pipe

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
