# Based on lecture materials by Sanjam Garg of UC Berkely

import ot
import secrets
from multiprocessing import Process, Pipe

N = 2048
e = 65537

# Bob generates a garbled table, sends to alice.
# Then, Bob performs 3 OTs with Alice, initiated by Alice.
def sender(conn, table):
    s = [secrets.randbits(1) for i in range(6)]
    print("Bob secrets", s)
    table[0] = s[0] ^ s[2] ^ table[0]
    table[1] = s[0] ^ s[3] ^ table[1]
    table[2] = s[1] ^ s[4] ^ table[2]
    table[3] = s[1] ^ s[5] ^ table[3]
    print("Bob sending table...")
    conn.send(("table", table))

    # OTs
    for i in range(0, 5, 2):
        print("Bob on OT", i//2)
        (label, (pk0, pk1)) = conn.recv()
        x0 = (s[i]).to_bytes(1, 'big')
        x1 = (s[i+1]).to_bytes(1, 'big')
        ot.send_msgs_enc(conn, pk0, pk1, x0, x1, N, label)

# Alice receives garbled table, performs 3 OTs with Bob to decrypt chosen element
# 1 OT for most significant bit (2 options), 2 OTs for least significant bit (4 options)
# choice between 0 and 3
def receiver(conn, choice):
    assert(choice >= 0 and choice <= 3)
    print("Alice waiting for table...")
    # get garbled table
    table = conn.recv()[1]
    print("Alice got table.", table)
    # optimization with only 1 key gen once this works
    sks = [ot.send_pks(conn, N, e, (choice & 2) >> 1, '0'),
        ot.send_pks(conn, N, e, choice & 1, '1'),
        ot.send_pks(conn, N, e, choice & 1, '2')]
    labels = [None, None, None]
    e_lists = [None, None, None]
    print("Alice waiting for encrypted Bob data...")
    # wait
    (labels[0], e_lists[0]) = conn.recv()
    (labels[1], e_lists[1]) = conn.recv()
    (labels[2], e_lists[2]) = conn.recv()
    labels = [int(l) for l in labels]

    # bubble sort by label
    if labels[2] < labels[1]:
        t = labels[1]
        labels[1] = labels[2]
        labels[2] = t
        s = e_lists[1]
        e_lists[1] = e_lists[2]
        e_lists[2] = s
    if labels[1] < labels[0]:
        t = labels[0]
        labels[0] = labels[1]
        labels[1] = t
        s = e_lists[0]
        e_lists[0] = e_lists[1]
        e_lists[1] = s
    if labels[2] < labels[1]:
        s = e_lists[1]
        e_lists[1] = e_lists[2]
        e_lists[2] = s
    print("Alice decrypting")
    s_i = int.from_bytes(ot.decrypt_selection(conn, e_lists[0], sks[0], (choice & 2) >> 1), 'big')
    s_j = int.from_bytes(ot.decrypt_selection(conn, e_lists[1], sks[1], choice & 1), 'big')
    s_k = int.from_bytes(ot.decrypt_selection(conn, e_lists[2], sks[2], choice & 1), 'big')
    print("Alice s:", s_i, s_j, s_k)
    # reconstruct chosen table entry
    if choice & 2:
        print("Alice got", s_i ^ s_k ^ table[choice])
        return s_i ^ s_k ^ table[choice]
    print("Alice got", s_i ^ s_j ^ table[choice])
    return s_i ^ s_j ^ table[choice]

def test(table, choice):
    parent_conn, child_conn = Pipe()
    p_a = Process(target=receiver, args=(parent_conn, choice,))
    p_b = Process(target=sender, args=(child_conn, table,))
    p_a.start()
    p_b.start()
    p_a.join()
    p_b.join()

