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
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
import sys


# Alice generates RSA keypair and sends bob one legitimate key and one garbage one.
# choice is given by the swapping of the key order
def send_pks(conn, N, e, choice):
    sk_alice = rsa.generate_private_key(public_exponent=e, key_size=N)
    # TODO - not secure yet. need to be able to generate public key which looks
    # indistinguishable without knowing a corresponding secret key
    garbage_key = rsa.generate_private_key(public_exponent=e, key_size=N)
    # public key in bytes format, which is picklable/sendable
    pk = sk_alice.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    pk_prime = garbage_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    if choice:
        conn.send(("(pk0, pk1)", (pk_prime, pk)))
    else:
        conn.send(("(pk0, pk1)", (pk, pk_prime)))
    print("Alice sent keys.")
    return sk_alice

# Bob encrypts his messages and sends them back
def send_msgs_enc(conn, _pk0, _pk1, x0, x1, N):
    pk0 = serialization.load_pem_public_key(_pk0)
    pk1 = serialization.load_pem_public_key(_pk1)
    e0 = pk0.encrypt(
        x0,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    e1 = pk1.encrypt(
        x1,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    conn.send(("[e0, e1]", [e0, e1]))

# Alice decrypts the message of her choice
def decrypt_selection(conn, e_list, sk_alice, choice):
    return sk_alice.decrypt(
            e_list[choice],
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()), 
                algorithm=hashes.SHA256(), 
                label=None
            )
        )

def alice_exec_example_OT(conn, choice, N, e):
    print("alice reporting for duty!")
    sk = send_pks(conn, N, e, choice)
    e_list = conn.recv()[1]
    msg = decrypt_selection(conn, e_list, sk, choice)
    print("Alice done. Got", msg)

def bob_exec_example_OT(conn, x0, x1, N):
    print("bob reporting for duty!")
    print("Bob has strings x0 =", x0, ", x1 =", x1)
    (pk0, pk1) = conn.recv()[1]
    send_msgs_enc(conn, pk0, pk1, x0, x1, N)
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

