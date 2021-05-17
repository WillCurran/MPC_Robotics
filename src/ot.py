# perform a 1-out-of-2 OT, based on basic semi-honest OT implementation in Pragmatic MPC

# Does not perform authentication. Assumes parties are certified/authentic.
# Key exchange is also trivialized. Just sends public keys in plaintext.

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
from Crypto.Hash import SHAKE128
import utils
import math
import sys


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

def receiver_exec_OT(conn, choice, N, e):
    # print("receiver reporting for duty!")
    sk = send_pks(conn, N, e, choice, '')
    e_list = conn.recv()[1]
    msg = decrypt_selection(conn, e_list, sk, choice)
    print("receiver done. Got", msg)
    return msg

# input: x0 and x1 are bytes objects
def sender_exec_OT(conn, x0, x1, N):
    # print("sender reporting for duty!")
    # print("sender has strings x0 =", x0, ", x1 =", x1)
    (label, (pk0, pk1)) = conn.recv()
    send_msgs_enc(conn, pk0, pk1, x0, x1, N, '')
    # print("sender done")

# 1-out-of-2 OTs, where strings are m bits long and there are k choices
# return array of chosen integers
def receiver_exec_ot_k_m(conn, choice_arr, N, e):
    ret = []
    for choice in choice_arr:
        ret.append(int.from_bytes(receiver_exec_OT(conn, choice, N, e), byteorder='big'))
    return ret

# 1-out-of-2 OTs, where pair items are m bits long and there are k pairs to choose from
def sender_exec_ot_k_m(conn, pairs, N):
    for (x0, x1) in pairs:
        sender_exec_OT(conn, x0, x1, N)

# extend k OTs to m OTs of l-bit strings (Ishai, Fig. 1 algorithm)
def ishai_receiver(conn, choice_arr, N, e, k, l):
    m = len(choice_arr)
    # number of bytes to store m and k and l bits
    nBytesM = int(math.ceil(m / 8.0))
    nBytesK = int(math.ceil(k / 8.0))
    nBytesL = int(math.ceil(l / 8.0))
    r = utils.bitarrayToInt(choice_arr)
    T = [secrets.randbits(m) for i in range(k)]
    # act as sender
    pairs = [(
              (T[i]).to_bytes(nBytesM, byteorder='big'), 
              (r ^ T[i]).to_bytes(nBytesM, byteorder='big')
             ) for i in range(k)]
    sender_exec_ot_k_m(conn, pairs, N)
    Y = conn.recv()[1]
    print('Got Y=', Y)
    Z = []
    for i in range(m):
        col = utils.getIthBitInt(T, m, i)
        # get l-bit hash for the column of bit-matrix T
        h = SHAKE128.new(data=col.to_bytes(nBytesK, byteorder='big')).read(nBytesL)
        Z.append(Y[i][choice_arr[i]] ^ int.from_bytes(h, byteorder='big'))
    print('Z=', Z)
    return Z

# extend k OTs to m OTs of l-bit strings (Ishai, Fig. 1 algorithm)
def ishai_sender(conn, pairs, N, e, k, l):
    m = len(pairs)
    # number of bytes to store k and l bits
    nBytesK = int(math.ceil(k / 8.0))
    nBytesL = int(math.ceil(l / 8.0))
    s_arr = [secrets.randbits(1) for i in range(k)]
    s = utils.bitarrayToInt(s_arr)
    # act as receiver with input s. Get k m-bit vals back
    Q = receiver_exec_ot_k_m(conn, s_arr, N, e)
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
    #DEBUG
    # N = 1024
    N = 2048
    e = 65537
    k = 8
    l = 16
    parent_conn, child_conn = Pipe()
    p_a = Process(target=ishai_receiver, args=(parent_conn, choices, N, e, k, l,))
    p_b = Process(target=ishai_sender, args=(child_conn, pairs, N, e, k, l,))
    p_a.start()
    p_b.start()
    p_a.join()
    p_b.join()

