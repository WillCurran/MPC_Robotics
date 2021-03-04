# Quickly generate 10M random 1/2 OTs, which should be plenty for our entire execution.
# In a*.txt files, we have the sender.
# In b*.txt files, we have the receiver.
# The idea is that we could do these legitimately in a pre-computation phase if we cared to.
# (Use an OT protocol of your choice)
# notation based on Precomputing Oblivious Transfer paper by Beaver.

import secrets

N_OTs = 10000000

f_a = open('a1.txt', 'w')
f_b = open('b1.txt', 'w')

for i in range(N_OTs):
    r = [secrets.randbits(1), secrets.randbits(1)]
    d = secrets.randbits(1)
    s_a = str(r[0]) + ' ' + str(r[1]) + '\n'
    s_b = str(d) + ' ' +  str(r[d]) + '\n'
    f_a.write(s_a)
    f_b.write(s_b)

f_a.close()
f_b.close()
