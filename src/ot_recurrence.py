# Goal : count actual complexity of implementation, and theoretical complexity of a
#        more efficient implementation.

# count the number of OTs by category with a recurrence based on our circuits
# also, count number of rounds of OTs necessary if we had parallelized execution
# (which we didn't, but it can be done)
import math

# recurrence relation for and gates in one compare (greater-than) circuit
def num_and_gates_compare_recursive(n_time_bits):
    # 1 AND to compute greater-than bit
    if n_time_bits == 1:
        return 1
    n1 = math.floor(n_time_bits/2.0)
    n2 = math.ceil(n_time_bits/2.0)
    # 2 additional AND gates per merge
    return num_ot_compare(n1) + num_ot_compare(n2) + 2

# arithmetic version
def num_OTs_compare_exchange(n_time_bits, n_symbol_bits):
    OTs_due_to_time_bits = 0
    OTs_due_to_symbol_bits = 0
    rounds = 0
    # compare AND gates, total
    num_and_gates_compare = 3 * n_time_bits - 2
    # compare depth
    num_and_rounds_compare = math.ceil(math.log2(n_time_bits)) + 1

    # exchange AND gates, per (n_time_bits+n_symbol_bits)-bit word
    num_and_gates_exchange_per_word = 4
    # exchange depth
    num_and_rounds_exchange = 1

    # 3 precomputed random 1/2-OTs per 1-out-of-4 chosen OT
    OTs_due_to_time_bits += 3 * num_and_gates_compare
    OTs_due_to_time_bits += 3 * num_and_gates_exchange_per_word * n_time_bits
    OTs_due_to_symbol_bits += 3 * num_and_gates_exchange_per_word * n_symbol_bits
    rounds += num_and_rounds_compare
    rounds += num_and_rounds_exchange

    return [OTs_due_to_time_bits, OTs_due_to_symbol_bits, rounds]

def num_OTs_sort(n_swaps, n_time_bits, n_symbol_bits):
    return [n_swaps * a for a in num_OTs_compare_exchange(n_time_bits, n_symbol_bits)]


# OTs in moore machine execution
# 1 round of batch OT per timeframe
# 1 OT per garbled key - 1 per symbol bit (large), or 1 per bit of security param K (small).
# OTs in non-reduced case is a multiple of time_interval, n_sensors and n_symbol_bits

# Each sensor sends one symbol for each possible time. 
# Need one garbled key exchange for each symbol bit.
def numOTs_moore_machine_eval_one_round(time_interval_max_t, n_symbol_bits, n_sensors, k_prime, s):
    return n_sensors * time_interval_max_t * n_symbol_bits * (k_prime + s)
