import matplotlib.pyplot as plt


run_time = ['350', '335', '410', '440', '550', '790', '1460']
w = [str(i) for i in range(1,8,1)]
OTs_time_sort = [14400, 76032, 251712, 703872, 1805760, 4400640, 10368576]
OTs_symb_sort = [23040, 50688, 105984, 216576, 437760, 880128, 1764864]
OTs_sort = [OTs_time_sort[i]+OTs_symb_sort[i] for i in range(7)]
OTs_moore = [768*(256+64) for i in range(1,8,1)] # k=256, s=64?
width = 0.35       # the width of the bars: can also be len(x) sequence

fig, ax = plt.subplots()

ax.bar(w, OTs_time_sort, width, label='time bits (sort)')
ax.bar(w, OTs_symb_sort, width, bottom=OTs_time_sort, label='symbol bits (sort)')
ax.bar(w, OTs_moore, width, bottom=OTs_sort, label='symbol bits (moore)')
for i in range(7):
    ax.text(-0.2 + i, OTs_time_sort[i]+OTs_symb_sort[i]+OTs_moore[i], run_time[i], \
        color='black', fontweight='bold')

ax.set_ylabel('OTs')
ax.set_xlabel('w')
ax.set_title('Cumulative Runtime vs. Time Window')
ax.legend()

plt.show()

# w = [str(i) for i in range(1,8,1)]
# comm_rounds = [2**(6-i) for i in range(7)]
# width = 0.35       # the width of the bars: can also be len(x) sequence

# fig, ax = plt.subplots()

# ax.bar(w, comm_rounds, width)

# ax.set_ylabel('rounds')
# ax.set_xlabel('w')
# ax.set_title('Cumulative Communication Rounds (Sensors-->Evaluators) vs. Time Window')
# ax.legend()

# plt.show()