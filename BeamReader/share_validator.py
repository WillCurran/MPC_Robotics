# input shares_a, shares_b
# output shares_a_XOR_b

f_a = open('shares_a', 'r')
f_b = open('shares_b', 'r')
f_ab = open('shares_a_XOR_b', 'w')

while True:
    try:
        a = int(f_a.readline())
        b = int(f_b.readline())
        f_ab.writelines(str(a ^ b) + "\n")
    except:
        break

f_a.close()
f_b.close()
f_ab.close()