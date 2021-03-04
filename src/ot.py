# perform a 1-out-of-2 OT, based on basic semi-honest OT implementation in Pragmatic MPC

# Does not perform authentication. Assumes parties are certified/authentic.
# Key exchange is also trivialized. Just sends public keys in plaintext.

# Alice: 
#   input - two bits b0, b1.
#   output - nothing
# Bob: 
#   input - nothing
#   output - bit d; one of Alice's input strings, b_d.

import secrets
from multiprocessing import Process, Pipe
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import sys


# Alice generates RSA keypair and sends bob one legitimate key and one garbage one.
# choice is given by the swapping of the key order
def send_pks(conn, N, e, choice, label):
    sk_alice = RSA.generate(N)
    # modulus must be odd
    rand_modulus = 2*(secrets.randbits(N)//2)+1
    garbage_key = RSA.construct((rand_modulus, 65537))
    # public keys in bytes format
    pk = sk_alice.publickey().export_key('PEM')
    pk_prime = garbage_key.export_key('PEM')
    if choice:
        conn.send((label, (pk_prime, pk)))
    else:
        conn.send((label, (pk, pk_prime)))
    return sk_alice

# Bob encrypts his messages and sends them back
def send_msgs_enc(conn, _pk0, _pk1, x0, x1, N, label):
    pk0 = RSA.import_key(_pk0)
    pk1 = RSA.import_key(_pk1)
    cipher0 = PKCS1_OAEP.new(pk0)
    cipher1 = PKCS1_OAEP.new(pk1)
    e0 = cipher0.encrypt(x0)
    e1 = cipher1.encrypt(x1)
    conn.send((label, [e0, e1]))

# Alice decrypts the message of her choice
def decrypt_selection(conn, e_list, sk_alice, choice):
    cipher = PKCS1_OAEP.new(sk_alice)
    return cipher.decrypt(e_list[choice])

def alice_exec_example_OT(conn, choice, N, e):
    print("alice reporting for duty!")
    sk = send_pks(conn, N, e, choice, '')
    e_list = conn.recv()[1]
    msg = decrypt_selection(conn, e_list, sk, choice)
    print("Alice done. Got", msg)

def bob_exec_example_OT(conn, x0, x1, N):
    print("bob reporting for duty!")
    print("Bob has strings x0 =", x0, ", x1 =", x1)
    (label, (pk0, pk1)) = conn.recv()
    send_msgs_enc(conn, pk0, pk1, x0, x1, N, '')
    print("Bob done")

def test(x0, x1, choice):
    N = 2048
    e = 65537
    parent_conn, child_conn = Pipe()
    p_a = Process(target=alice_exec_example_OT, args=(parent_conn, choice, N, e,))
    p_b = Process(target=bob_exec_example_OT, args=(child_conn, x0, x1, N,))
    p_a.start()
    p_b.start()
    p_a.join()
    p_b.join()

