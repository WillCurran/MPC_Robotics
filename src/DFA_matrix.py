import random
from phe import paillier
import math
import otJC
import secrets

MOORE_MACHINE_OUTPUT_BITS = 4 # need to make some assumption on this for garbled matrix element size

# p. 7 of Mohassel ODFA paper (Moore Variation)
def DfaMat(dfa, n):
    m = dfa['states']
    M = []
    for i in range(0, n + 1):
        row = []
        for j in range(0, m):
            res_0 = dfa['delta'][j][0]
            res_1 = dfa['delta'][j][1]
            output = dfa['outputs'][j]
            row.append((res_0, res_1, output))
        M.append(row)
    return M

# p. 7 of Mohassel ODFA paper (Moore Variation)
def singleMooreRow(dfa):
    m = dfa['states']
    row = []
    for j in range(0, m):
        res_0 = dfa['delta'][j][0]
        res_1 = dfa['delta'][j][1]
        output = dfa['outputs'][j]
        row.append((res_0, res_1, output))
    return row

# pretty print util
def print_M(M):
    for line in M:
        print(*line)

# M : DFA matrix
# n : number of bits in input string
# x : the input bit string
# q0 : initial state index
def evalDfa(M, n, x, q0):
    j = q0
    print('evaluating DFA matrix ...')
    for i in range(0, n):
        print('current output', M[i][j][2])
        j = M[i][j][int(x[i])]
    print('current output', M[n][j][2])
    return M[n][j][2]

# generate a matrix with n rows m cols, row elements are scrambled indices ranging [0, m).
def genPerm(n, m):
    Q = list(range(0, m))
    PER = []
    for i in range(0, n):
        random.shuffle(Q)
        PER.append(Q[:])
    return PER

# Permute a DFA matrix M (with length n+1) with permutation matrix PER (with length n+2)
def permDfaMat(M, PER, n, q):
    PM = [[(-1, -1) for j in range(q)] for i in range(n)]
    for i in range(n):
        for j in range(q):
            j_permuted = PER[i][j] # pick a random index in this row of PM
            # make the i-th element of PM point to the same states in the next row as M[i][j] does.
            # These states will be placed at the PER[i + 1][M[i][j]]-th index of PM in the next iteration,
            # so point there with the promise that we will place them there next iteration.
            res_0 = PER[i + 1][M[i][j][0] ]
            res_1 = PER[i + 1][M[i][j][1] ]
            output = M[i][j][2]
            PM[i][j_permuted] = (res_0, res_1, output)
    return PM

# assume num2 is of n_digits digits. That is, 0b1 || 0b1 = 0b1 || 0b0001 = 0b10001 = 17 if n_digits = 4.
def numConcat(num1, num2, n_digits): 
     # add zeroes to the end of num1 
     num1 = num1 << n_digits
     # add num2 to num1 
     num1 += num2 
     return num1


# for now, skip this step since we are doing OT in one thread on one machine
def step1(X, n, k):
    (public_key, private_key) = paillier.generate_paillier_keypair() # G_OT
    q = [0] * n
    # for i in range (0,n):
        #q[i] = Q_ot(public_Key, 1, 1, X[i]) # generate queries Q_OT
    return (public_key, private_key, q)

def split_bits(n1_concat_n2, bits_n2):
    n1 = n1_concat_n2 >> bits_n2
    n2 = n1_concat_n2 ^ (n1 << bits_n2)
    return (n1, n2)

# return true if there are n zeros at the end of the given number.
def hasNTrailingZeros(number, n):
    return (number & (2**n - 1)) == 0 # AND bitmask with n-ones

class Alice:
    # Client encrypts her input at her current row_i and sends it to server in the form
    # (c_enc_a, c_prime_enc_a)
    def encrypt_input_i(self):
        self.conn.send(otJC.alice_send_choices_enc(int(self.input[self.row_i]), self.public_key))

    # used for getting the output at current state, without advancing to the next state yet.
    # we use this for revealing the output at the last row of the GM
    def revealColor(self):
        pass

    # Client retrieves the keys and computes the final result.
    def step3(self, key_enc, GM):
        # decrypt garbled key
        k_i = otJC.alice_compute_result(int(self.input[self.row_i]), key_enc[0], key_enc[1], self.private_key)

        # get the corresponding random nums
        random.seed(self.pad)
        pad0_pad1 = (random.getrandbits(self.k_prime + self.s), random.getrandbits(self.k_prime + self.s))
        # navigate to the next state (first guess)
        newstate_concat_output_concat_newpad = k_i ^ pad0_pad1[0] ^ GM[self.row_i][self.state][0]
        if not hasNTrailingZeros(newstate_concat_output_concat_newpad, self.s):
            newstate_concat_output_concat_newpad = k_i ^ pad0_pad1[1] ^ GM[self.row_i][self.state][1]
        (newstate_concat_output_concat_newpad, _) = split_bits(newstate_concat_output_concat_newpad, self.s)
        # If last row, discard pad since it is meaningless. This is because we lack a next input at this point.
        if self.row_i == self.n:
            (state_concat_output, _) = split_bits(newstate_concat_output_concat_newpad, self.k)
        else:
            (state_concat_output, self.pad) = split_bits(newstate_concat_output_concat_newpad, self.k)
        (self.state, output) = split_bits(state_concat_output, MOORE_MACHINE_OUTPUT_BITS)
        self.row_i += 1
        return output

    def init_state_and_pad(self, init_state_index, init_pad):
        self.state = init_state_index
        self.pad = init_pad

    def __init__(self, conn, dfa, alice_input, n, k, s):
        # we need an extra input (can be meaningless) to get the output at the last state
        # this is because the garbled key for the last row must exist, even if it doesn't need to point to the correct delta.
        self.input = alice_input + str(secrets.randbits(1))
        self.n = n
        self.q = dfa['states']
        self.k = k
        self.k_prime = (self.k + math.floor(math.log(self.q, 2)) + 1) + MOORE_MACHINE_OUTPUT_BITS
        self.s = s
        self.state = None
        self.pad = None
        self.row_i = 0 # which row am I in?
        (self.public_key, self.private_key) = paillier.generate_paillier_keypair()
        self.conn = conn
        # send pk to bob
        self.conn.send(self.public_key)
		
class Bob:
    # Server mixes his inputs with client's and sends back to client in the form
    # (d_0_enc, d_1_enc). Alice tells us which row of the matrix she is currently looking at.
    def send_garbled_key(self, alice_choices, alice_i):
        self.conn.send(
            otJC.bob_send_strings_enc(
            int(self.input[alice_i]), 
            self.K_enc[alice_i], 
            alice_choices[0], 
            alice_choices[1], 
            self.public_key, 
            self.k
            )
        )

    # Server Computes a Garbled DFA Matrix GM
    def step2(self, dfa, n, k):
        #Generating random pads and a permuted DFA matrix PMΓ
        q = dfa['states']
        k_prime = (k + math.floor(math.log(q, 2)) + 1) + MOORE_MACHINE_OUTPUT_BITS
        GM = [[(0,0)] * q for i in range(n + 1)]
        #Server generates n + 1 random key pairs for garbling:
        a = random.sample(range(0,2**k_prime), n + 1)
        b = random.sample(range(0,2**k_prime), n + 1)
        K = list(zip(a,b))
        #Server generates a random pad matrix PADn×|Q|:
        PAD = [random.sample(range(0,2**k), q) for i in range(n + 2)]
        #server generates a DFA matrix MΓ of length n+1:
        M = DfaMat(dfa, n)
        #server generates a random permutation matrix PERn×|Q|:
        PER = genPerm(n + 2, q)
        #server generates a permuted DFA matrix PMΓ:
        PM = permDfaMat(M, PER, self.n, self.q)
        #Computing the Garbled DFA Matrix GMΓ from PMΓ
        for i in range (0, n + 1):
            for j in range (0, q):
                # could impliment a Mealy Machine with outputs on arcs of the DFA same way,
                # right now we just have the Moore Machine output copied twice
                a = numConcat(PM[i][j][0], PM[i][j][2], MOORE_MACHINE_OUTPUT_BITS)
                a = numConcat(a, PAD[i+1][PM[i][j][0] ], k)
                b = numConcat(PM[i][j][1], PM[i][j][2], MOORE_MACHINE_OUTPUT_BITS)
                b = numConcat(b, PAD[i+1][PM[i][j][1] ], k)
                a = a ^ K[i][0]
                b = b ^ K[i][1]
                GM[i][j] = (a,b)
                # Pseudo Random Number Generator G 
                # ****NOT SECURE BECAUSE SYSTEM RAND DOES NOT HAVE A SET SEED FUNCTION*****
                # Would need to replace with a cryptographically secure pseudo-random number generator.
                random.seed(PAD[i][j])
                a = random.getrandbits(k_prime)
                b = random.getrandbits(k_prime)
                pad = (a,b)
                a = GM[i][j][0] ^ pad[0]
                b = GM[i][j][1] ^ pad[1]
                GM[i][j] = (a,b)
        K_enc = K # TODO - encrypt with OT public key and transfer via OT
        init_state = PER[0][dfa['initial'] ]
        init_pad = PAD[0][init_state]
        return (M, PER, PM, K_enc, GM, init_state, init_pad) # TODO - remove M, PER, PM when not testing/debugging

    def append_GM_row(self):
        new_gm_row = [(0,0)] * self.q
        # Server generates 1 random keypair for garbling:
        # (This is a cryptographically secure RNG, in the order of security bits)
        a = secrets.randbits(self.k_prime + self.s)
        b = secrets.randbits(self.k_prime + self.s)
        garbled_keypair = (a,b)
        # Server generates a new row to append to PAD:
        next_pad_row = random.sample(range(0,2**self.k), self.q)
        # server generates a new row to append to PER:
        next_per_row = genPerm(1, self.q)[0]
        # server generates a row to append to PM:
        new_pm_row = permDfaMat([self.m_row], [self.PER[len(self.PER) - 1], next_per_row], 1, self.q)[0]
        # Computing the Garbled DFA Matrix GMΓ from PMΓ
        for j in range (0, self.q):
            # could impliment a Mealy Machine with outputs on arcs of the DFA same way,
            # right now we just have the Moore Machine output copied twice
            a = numConcat(new_pm_row[j][0], new_pm_row[j][2], MOORE_MACHINE_OUTPUT_BITS)
            a = numConcat(a, next_pad_row[new_pm_row[j][0] ], self.k)
            a = numConcat(a, 0, self.s)
            b = numConcat(new_pm_row[j][1], new_pm_row[j][2], MOORE_MACHINE_OUTPUT_BITS)
            b = numConcat(b, next_pad_row[new_pm_row[j][1] ], self.k)
            b = numConcat(b, 0, self.s) 
            a = a ^ garbled_keypair[0]
            b = b ^ garbled_keypair[1]
            new_gm_row[j] = (a,b)
            # Pseudo Random Number Generator G
            random.seed(self.PAD[len(self.PAD) - 1][j])
            a = random.getrandbits(self.k_prime + self.s)
            b = random.getrandbits(self.k_prime + self.s)
            pad = (a,b)
            a = new_gm_row[j][0] ^ pad[0]
            b = new_gm_row[j][1] ^ pad[1]
            new_gm_row[j] = (a,b)
        garbled_keypair_enc = garbled_keypair # TODO - encrypt with OT public key and transfer via OT

        self.M.append(self.m_row)
        self.PER.append(next_per_row)
        self.PAD.append(next_pad_row)
        self.PM.append(new_pm_row)
        self.GM.append(new_gm_row)
        self.K_enc.append(garbled_keypair_enc)
        self.n += 1


    def __init__(self, conn, bob_input, dfa, public_key, k, s):
        self.input = bob_input
        self.input += str(secrets.randbits(1)) # or random choice
        self.dfa = dfa
        self.public_key = public_key
        self.k = k
        self.s = s
        self.n = 0
        self.conn = conn

        # start with 1 row of M, 1 row of PM, 1 row GM, 2 rows PER, 2 rows PAD, 1 garbled keypair
        self.q = dfa['states']
        self.k_prime = (self.k + math.floor(math.log(self.q, 2)) + 1) + MOORE_MACHINE_OUTPUT_BITS
        new_gm_row = [(0,0)] * self.q
        # Server generates 1 random keypair for garbling:
        a = secrets.randbits(self.k_prime + self.s)
        b = secrets.randbits(self.k_prime + self.s)
        garbled_keypair = (a,b)
        self.m_row = singleMooreRow(self.dfa)
        # need to start with two rows for pad and permutation matrix
        # the best we can do is to start with cryptographically secure pad, for now.
        # later, we must use a cryptographically secure PRNG which supports a setseed operation.
        self.PAD = [[secrets.randbits(self.k) for j in range(self.q)] for i in range(2)]
        print(self.PAD)
        self.PER = genPerm(2, self.q)
        self.PM = permDfaMat([self.m_row], self.PER, 1, self.q)
        for j in range (0, self.q):
            # could impliment a Mealy Machine with outputs on arcs of the DFA same way,
            # right now we just have the Moore Machine output copied twice
            a = numConcat(self.PM[0][j][0], self.PM[0][j][2], MOORE_MACHINE_OUTPUT_BITS)
            a = numConcat(a, self.PAD[1][self.PM[0][j][0] ], k)
            a = numConcat(a, 0, self.s)
            b = numConcat(self.PM[0][j][1], self.PM[0][j][2], MOORE_MACHINE_OUTPUT_BITS)
            b = numConcat(b, self.PAD[1][self.PM[0][j][1] ], k)
            b = numConcat(b, 0, self.s)
            a = a ^ garbled_keypair[0]
            b = b ^ garbled_keypair[1]
            new_gm_row[j] = (a,b)
            # Pseudo Random Number Generator G
            random.seed(self.PAD[0][j])
            a = random.getrandbits(self.k_prime + self.s)
            b = random.getrandbits(self.k_prime + self.s)
            pad = (a,b)
            a = new_gm_row[j][0] ^ pad[0]
            b = new_gm_row[j][1] ^ pad[1]
            new_gm_row[j] = (a,b)

        self.init_state = self.PER[0][dfa['initial'] ]
        self.init_pad = self.PAD[0][self.init_state]

        self.conn.send((self.init_state, self.init_pad))

        self.M = [self.m_row]
        self.GM = [new_gm_row]
        self.K_enc = [garbled_keypair]