from phe import paillier

# This file does a standard 1-out-of-2 OT, then uses it repeatedly to do 1-out-of-4 OT.
# Based on Malek and Miri 2013, https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=1512846
#   - difficulty understanding how they use Paillier but still do exponentiations with encrypted numbers

# key creation - assume some key exchange protocol used to share pk_shared
pk_shared, sk_only_a = paillier.generate_paillier_keypair()

# assumes choice is 0/1 (1-out-of-2 OT)
def alice_send_choices_enc(choice_a, pk_shared):
    c_enc_0 = pk_shared.encrypt(1 - choice_a)
    c_enc_1 = pk_shared.encrypt(choice_a)
    return c_enc_0, c_enc_1

def bob_send_strings_enc(strings_b, c_enc_0, c_enc_1, pk_shared):
    # strings_enc_b = [pk_shared.encrypt(x) for x in strings_b]
    # d = [strings_enc_b[i] + concatenate_itself_n_times(c_enc[i], r[i]) for i in range(4)]
    d0 = strings_b[0] * c_enc_0
    d1 = strings_b[1] * c_enc_1
    return d0 + d1

def alice_compute_result(choice_a, d, sk_only_a):
    return sk_only_a.decrypt(d)

# Assumes global pk_shared and sk_only_a defined as pallier keys.
def example_execution_OT(choice_a, strings_b, pk_shared, sk_only_a):
    expected_result = strings_b[choice_a]
    print("Input choice is", choice_a)
    print("B's strings are: '" + str(strings_b[0]) + "', '" + str(strings_b[1]) + "'")
    print("Protocol should choose " + str(expected_result) + ".")

    # Alice begins by sending Bob her choice variables
    bob_receives_c0_enc, bob_receives_c1_enc = alice_send_choices_enc(choice_a, pk_shared)
    # Bob now mixes his choice with Alice's choice and his strings and sends to Alice
    alice_receives_d_enc = \
        bob_send_strings_enc(strings_b, bob_receives_c0_enc, bob_receives_c1_enc, pk_shared)
    # Alice makes the final choice
    alice_plaintext_result = \
        alice_compute_result(choice_a, alice_receives_d_enc, sk_only_a)
    print("Alice's result: " + str(alice_plaintext_result))



example_execution_OT(1, [0, 100], pk_shared, sk_only_a)

# zero = pk_shared.encrypt(0)
# one = pk_shared.encrypt(1)
# one_double_enc = pk_shared.encrypt(one.ciphertext()) # does not work
# print(sk_only_a.decrypt(sk_only_a.decrypt(one_double_enc).ciphertext()))
# two = paillier.EncryptedNumber(pk_shared, one.ciphertext() * one.ciphertext())
# print(sk_only_a.decrypt(two))