# perform a (random) 1-out-of-2 OT, based on original found here : http://www.lix.polytechnique.fr/~catuscia/teaching/papers_and_books/SigningContracts.pdf
# "It is not essential that a user A randomly generates a new instance 
# of PKCS every time he plays the role of S" - can we still take this seriously?

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


# Alice generates RSA keypair and sends public part to Bob, along with two random bits
# conn is an outbound side of a pipe open with Bob.
def send_pk(conn, N, e):
    sk_alice = rsa.generate_private_key(public_exponent=e, key_size=N)
    m0 = secrets.randbits(190*8)
    m1 = secrets.randbits(190*8)
    # public key in bytes format, which is picklable/sendable
    E = sk_alice.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    m = [m0, m1]
    conn.send(("[E, m]", [E, m]))
    print("Alice sent [E, m].")
    return (sk_alice, m0, m1)

# Bob has received Alice's keys and will now encrypt his choice
# conn is an outbound side of a pipe open with Alice
def send_choice_enc(conn, E, m, N):
    # TODO - why is 190 bytes the max size? why not 255?
    k = secrets.randbits(190*8).to_bytes(190, byteorder=sys.byteorder, signed=False)
    # k = secrets.randbits(N).to_bytes(N//8, 'big', signed=False)
    c = secrets.randbelow(2)
    pk = serialization.load_pem_public_key(E)
    k_enc = pk.encrypt(
        k,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    print("k_enc size:", sys.getsizeof(k_enc))
    print("m[c] size:", sys.getsizeof(m[c]))
    print("k_enc size to int:", sys.getsizeof(int.from_bytes(k_enc, byteorder=sys.byteorder, signed=False)))
    q = int.from_bytes(k_enc, byteorder=sys.byteorder, signed=False) ^ m[c]
    print("q size:", sys.getsizeof(q))
    conn.send(("q", q))
    return (c, k, pk)

# Alice decrypts what bob has sent (two possibilities), then 
# encrypts her bits with both possibilities and sends the encrypted result
def send_bits_enc(conn, q, m0, m1, sk_alice, b0, b1, N):
    # TODO - Here, does the reduction of message space compromise correctness as well?
    print("q size:", sys.getsizeof(q))
    cipher1 = (q ^ m0).to_bytes(N//8, byteorder=sys.byteorder, signed=False)
    cipher2 = (q ^ m1).to_bytes(N//8, byteorder=sys.byteorder, signed=False)
    print("m0 size:", sys.getsizeof(m0))
    print("m1 size:", sys.getsizeof(m1))
    print("cipher1 size:", sys.getsizeof(cipher1))
    print("cipher2 size:", sys.getsizeof(cipher2))
    k0 = int.from_bytes(
        bytes=sk_alice.decrypt(
            cipher1,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()), 
                algorithm=hashes.SHA256(), 
                label=None
            )
        ),
        byteorder=sys.byteorder
    )
    k1 = int.from_bytes(
        bytes=sk_alice.decrypt(
            cipher2,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()), 
                algorithm=hashes.SHA256(), 
                label=None
            )
        ),
        byteorder=sys.byteorder
    )
    s = secrets.randbelow(2)
    m = None
    if s == 1:
        m = [k1 ^ m0, k0 ^ m1]
    else:
        m = [k0 ^ m0, k1 ^ m1]
    conn.send(("m, s", (m, s)))

# Bob decrypts
def decrypt_bit(m, c, s, k):
    return m[s^c] ^ k

def alice_exec_example_OT(conn, b0, b1, N, e):
    print("alice reporting for duty!")
    (sk, m0, m1) = send_pk(conn, N, e)
    q = conn.recv()[1]
    send_bits_enc(conn, q, m0, m1, sk, b0, b1, N)
    print("Alice done")

def bob_exec_example_OT(conn, N):
    print("bob reporting for duty!")
    (E, m) = conn.recv()[1]
    (c, k, pk) = send_choice_enc(conn, E, m, N)
    (m, s) = conn.recv()[1]
    b_d = decrypt_bit(m, c, s, k)
    print("choice:", c ^ s, "bit:", b_d)
    print("Bob done")

def test(b0, b1):
    N = 2048
    e = 65537
    parent_conn, child_conn = Pipe()
    p_a = Process(target=alice_exec_example_OT, args=(parent_conn, b0, b1, N, e,))
    p_b = Process(target=bob_exec_example_OT, args=(child_conn, N,))
    p_a.start()
    p_b.start()
    p_a.join()
    p_b.join()

