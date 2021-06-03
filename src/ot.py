# This is the nuts and bolts file which does actual oblivious transfer in a multiprocessing context.
# Performs a 1-out-of-2 OT, based on basic semi-honest OT implementation in Pragmatic MPC.
# The end goal for us is to use a 1-out-of-2 OT to do a large batch of OTs which the main
# program can consume. Uses Ishai 2003 for OT extension.
# Does not perform authentication. Assumes parties are certified/authentic.
# Key exchange is also trivialized. Just sends public keys in plaintext.
# A multiprocessing context is what we decided provides the minimum platform for demonstrating our methods,
# and does not make sense from a practical standpoint or a security standpoint.
# A fully functional practical implementation would involve replacing multi-process communication with 
# TCP/IP communication protocols, in addition to using a language more suited to efficient oblivious transfer.

# receiver: 
#   input - two bits b0, b1.
#   output - nothing
# sender: 
#   input - nothing
#   output - bit d; one of receiver's input strings, b_d.

import secrets
from multiprocessing import Process, Pipe
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHAKE128        # Asharov/Lindell/Schneider/Zohner 2013 use SHA-1 so SHA-3 should be fine
import utils
import math
import sys
import random

# receiver generates RSA keypair and sends sender one legitimate key and one garbage one.
# choice is given by the swapping of the key order
def send_pks(conn, N, e, choice, label):
    sk_receiver = RSA.generate(N)
    # modulus must be odd, and greater than e.
    rand_modulus = -1
    while rand_modulus < e:
        # print("here")
        rand_modulus = 2*(secrets.randbits(N)//2)+1
    garbage_key = RSA.construct((rand_modulus, 65537))
    # public keys in bytes format
    pk = sk_receiver.publickey().export_key('PEM')
    pk_prime = garbage_key.export_key('PEM')
    if choice:
        conn.send((label, (pk_prime, pk)))
    else:
        conn.send((label, (pk, pk_prime)))
    return sk_receiver

# sender encrypts his messages and sends them back
def send_msgs_enc(conn, _pk0, _pk1, x0, x1, N, label):
    pk0 = RSA.import_key(_pk0)
    pk1 = RSA.import_key(_pk1)
    cipher0 = PKCS1_OAEP.new(pk0)
    cipher1 = PKCS1_OAEP.new(pk1)
    e0 = cipher0.encrypt(x0)
    e1 = cipher1.encrypt(x1)
    conn.send((label, [e0, e1]))

# receiver decrypts the message of her choice
def decrypt_selection(conn, e_list, sk_receiver, choice):
    cipher = PKCS1_OAEP.new(sk_receiver)
    return cipher.decrypt(e_list[choice])

# choice is binary integer [0, 1]
def receiver_exec_OT(conn, choice, N, e):
    # print("receiver reporting for duty!")
    sk = send_pks(conn, N, e, choice, '')
    e_list = conn.recv()[1]
    msg = decrypt_selection(conn, e_list, sk, choice)
    # print("receiver done. Got", msg)
    return msg

# input: x0 and x1 are bytes objects
def sender_exec_OT(conn, x0, x1, N):
    # print("sender reporting for duty!")
    # print("sender has strings x0 =", x0, ", x1 =", x1)
    (label, (pk0, pk1)) = conn.recv()
    send_msgs_enc(conn, pk0, pk1, x0, x1, N, '')
    # print("sender done")

# 1-out-of-2 OTs, where strings are k bits long and there are k choices
# choices are binary integers
# return array of chosen integers
def receiver_exec_ot_k_k(conn, choice_arr, N, e):
    ret = []
    for choice in choice_arr:
        ret.append(int.from_bytes(receiver_exec_OT(conn, choice, N, e), byteorder='big'))
    print("OTk_k got", ret)
    return ret

# 1-out-of-2 OTs, where pair items are k bits long and there are k pairs to choose from
# pair items are integers
def sender_exec_ot_k_k(conn, pairs, N):
    k = len(pairs)
    nBytesK = int(math.ceil(k / 8.0))
    # RSA works with bytes objects
    pairs = [(pairs[i][0].to_bytes(nBytesK, byteorder='big'), pairs[i][1].to_bytes(nBytesK, byteorder='big'))
            for i in range(k)]
    for (x0, x1) in pairs:
        sender_exec_OT(conn, x0, x1, N)

# 1-out-of-2 OTs, where strings are m bits long and there are k choices
# pair items are integers
# return array of chosen integers
def receiver_exec_ot_k_m(conn, choice_arr, m, N, e):
    k = len(choice_arr)
    # OT with seeds
    seeds = receiver_exec_ot_k_k(conn, choice_arr, N, e)
    # receive masked m-bit strings
    masked = conn.recv()[1]
    ret = []
    for i in range(k):
        random.seed(seeds[i])
        ret.append(masked[i][choice_arr[i]] ^ random.getrandbits(m))
    # print(ret)
    return ret

# 1-out-of-2 OTs, where pair items are m bits long and there are k pairs to choose from
# pair items are integers
def sender_exec_ot_k_m(conn, pairs, m, N):
    k = len(pairs)
    rand_strs = [(secrets.randbits(k), secrets.randbits(k)) for i in range(k)]
    # OT with seeds
    sender_exec_ot_k_k(conn, rand_strs, N)
    # Send masked strings
    masked = [None]*k
    for i in range(k):
        random.seed(rand_strs[i][0])
        masked0 = random.getrandbits(m) ^ pairs[i][0]
        random.seed(rand_strs[i][1])
        masked1 = random.getrandbits(m) ^ pairs[i][1]
        masked[i] = (masked0, masked1)
    conn.send(('masked', masked))

# extend k OTs to m OTs of l-bit strings (Ishai, Fig. 1 algorithm)
# pair items are integers
def ishai_receiver(conn, choice_arr, N, e, k, l):
    m = len(choice_arr)
    # number of bytes to store m and k and l bits
    # nBytesM = int(math.ceil(m / 8.0))
    nBytesK = int(math.ceil(k / 8.0))
    nBytesL = int(math.ceil(l / 8.0))
    r = utils.bitarrayToInt(choice_arr)         # huge bottleneck here - shifting very long integers
    T = [secrets.randbits(m) for i in range(k)] # bottleneck? TODO - get times associated with different ops
    # act as sender
    pairs = [(T[i], r ^ T[i]) for i in range(k)]
    sender_exec_ot_k_m(conn, pairs, m, N)       # bottleneck? (2*m pseudorandom generator invocations + k OTs)
    Y = conn.recv()[1]
    # print('Got Y=', Y)
    # Data is often too big (m > 100000, for example) to be pickled and sent over pipe.
    # So, write Z to memory instead.
    fd_z = open('z.txt', 'w')
    for i in range(m):
        col = utils.getIthBitInt(T, m, i)       # How much time do these util functions take? very inefficeint matrix operation here (Schneider 2015 addresses)
        # get l-bit hash for the column of bit-matrix T
        h = SHAKE128.new(data=col.to_bytes(nBytesK, byteorder='big')).read(nBytesL)
        fd_z.write(str(Y[i][choice_arr[i]] ^ int.from_bytes(h, byteorder='big')) + '\n')
    fd_z.close()
    conn.send('ACK')

# extend k OTs to m OTs of l-bit strings (Ishai, Fig. 1 algorithm)
# pair items are integers
def ishai_sender(conn, pairs, N, e, k, l):
    m = len(pairs)
    # number of bytes to store k and l bits
    nBytesK = int(math.ceil(k / 8.0))
    nBytesL = int(math.ceil(l / 8.0))
    s_arr = [secrets.randbits(1) for i in range(k)]
    s = utils.bitarrayToInt(s_arr)
    # act as receiver with input s. Get k m-bit vals back
    Q = receiver_exec_ot_k_m(conn, s_arr, m, N, e) # bottleneck? (2*m pseudorandom generator invocations + k OTs)
    Y = []
    for i in range(m):
        col = utils.getIthBitInt(Q, m, i)
        # get l-bit hash for the column of m x k bit-matrix Q
        hash0 = SHAKE128.new(data=col.to_bytes(nBytesK, byteorder='big')).read(nBytesL)
        hash1 = SHAKE128.new(data=(col ^ s).to_bytes(nBytesK, byteorder='big')).read(nBytesL)
        y0 = pairs[i][0] ^ int.from_bytes(hash0, byteorder='big')
        y1 = pairs[i][1] ^ int.from_bytes(hash1, byteorder='big')
        Y.append((y0, y1))
    conn.send(('Y', Y))

# pairs is of format [(int, int) ...] and choices is of format [int, ...]
def test(pairs, choices):
    assert(len(pairs) == len(choices))
    N = 2048
    e = 65537
    k = 8
    l = 16
    parent_conn, child_conn = Pipe()
    p_a = Process(target=ishai_receiver, args=(parent_conn, choices, N, e, k, l,))
    p_b = Process(target=ishai_sender, args=(child_conn, pairs, N, e, k, l,))
    # p_a = Process(target=receiver_exec_ot_k_m, args=(parent_conn, choices, m, N, e,))
    # p_b = Process(target=sender_exec_ot_k_m, args=(child_conn, pairs, m, N,))
    p_a.start()
    p_b.start()
    p_a.join()
    p_b.join()

# k seed OTs of length k, n 1-bit random OTs
def generatePrecomputedFiles(k, n):
    f_a = open('a.txt', 'w')
    pairs = [(secrets.randbits(1), secrets.randbits(1)) for i in range(n)]
    choices = [secrets.randbits(1) for i in range(n)]
    # TODO - fix bottleneck by never working with long binary array
    # choices = secrets.randbits(n)
    for i in range(n):
        s_a = str(pairs[i][0]) + ' ' + str(pairs[i][1]) + '\n'
        f_a.write(s_a)
    f_a.close()
    N = 2048
    e = 65537
    l = 1
    parent_conn, child_conn = Pipe()
    p_a = Process(target=ishai_receiver, args=(parent_conn, choices, N, e, k, l,))
    p_b = Process(target=ishai_sender, args=(child_conn, pairs, N, e, k, l,))
    p_a.start()
    p_b.start()
    p_a.join()
    p_b.join()
    print("both done")
    # Need to get the received seeds (written by receiver to disk in this demo)
    child_conn.recv() # ACK that z.txt is writted
    fd_z = open('z.txt', 'r')
    Z = []
    for line in fd_z:
        Z.append(int(line))

    print("Got Z in main")
    f_b = open('b.txt', 'w')
    for i in range(n):
        s_b = str(choices[i]) + ' ' + str(Z[i]) + '\n'
        f_b.write(s_b)
    f_b.close()

