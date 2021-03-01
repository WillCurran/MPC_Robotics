from phe import paillier
import secrets
import sys

# key creation - assume some key exchange protocol used to share pk_shared
# pk_shared, sk_only_a = paillier.generate_paillier_keypair()

def alice_send_choices_enc(choice_a, pk_shared):
    c_enc_a = pk_shared.encrypt(0B0)
    c_prime_enc_a = pk_shared.encrypt(0B1)
    if choice_a:
        t = c_enc_a
        c_enc_a = c_prime_enc_a
        c_prime_enc_a = t
    return c_enc_a, c_prime_enc_a

def bob_send_strings_enc(choice_b, strings_b, c0_enc, c1_enc, pk_shared, k):
    # Generate randoms
    r0 = secrets.randbits(k)
    r1 = secrets.randbits(k)
    strings_enc_b = [pk_shared.encrypt(x) for x in strings_b]
    d0 = d1 = None
    if choice_b:
        d0 = strings_enc_b[1] + concatenate_itself_n_times(c0_enc, r0) # supposed to concatenate r0 times: what's the purpose?
        d1 = strings_enc_b[0] + concatenate_itself_n_times(c1_enc, r1) # why addition and not addition mod 2? Overflow issue?
    else:
        d0 = strings_enc_b[0] + concatenate_itself_n_times(c0_enc, r0)
        d1 = strings_enc_b[1] + concatenate_itself_n_times(c1_enc, r1)
    return d0, d1

def alice_compute_result(choice_a, d0, d1, sk_only_a):
    if choice_a:
        return sk_only_a.decrypt(d1)
    return sk_only_a.decrypt(d0)

# Assumes global pk_shared and sk_only_a defined as pallier keys.
def example_execution_OT_with_JC(choice_a, choice_b, strings_b, pk_shared, sk_only_a):
    if (choice_a != 0 and choice_a != 1) or (choice_b != 0 and choice_b != 1):
        print("Choices must be in {0, 1}.")
        return
    expected_result_i = choice_a ^ choice_b
    expected_result = strings_b[expected_result_i]
    print("Input choices are")
    print("A: " + str(choice_a))
    print("B: " + str(choice_b))
    print("B's strings are: '" + str(strings_b[0]) + "', '" + str(strings_b[1]) + "'")
    print("Protocol should choose the " + str(expected_result_i) + 
            "-th string, which is " + str(expected_result) + ".")
    print("Executing Oblivious Transfer with Joint Choice ...")

    # Alice begins by sending Bob her choice variables
    bob_receives_c0_enc, bob_receives_c1_enc = alice_send_choices_enc(choice_a, pk_shared)
    # Bob now mixes his choice with Alice's choice and his strings and sends to Alice
    alice_receives_d0_enc, alice_receives_d1_enc = \
        bob_send_strings_enc(choice_b, strings_b, bob_receives_c0_enc, bob_receives_c1_enc, pk_shared)
    # Alice makes the final choice
    alice_plaintext_result = \
        alice_compute_result(choice_a, alice_receives_d0_enc, alice_receives_d1_enc, sk_only_a)
    print("Alice's result: " + str(alice_plaintext_result))

# performs arithmetic operations equivalent to concatenating the given bit string with itself n times
def concatenate_itself_n_times(bit_str_enc, n):
    concatenated_bit_str_enc = bit_str_enc
    for i in range(0, n):
        concatenated_bit_str_enc = concatenated_bit_str_enc * 2 + bit_str_enc # shift left, adding either a 0 or 1
    return concatenated_bit_str_enc
