import matplotlib.pyplot as plt


run_time = ['t = 28.0', 't = 28.0', 't = 28.0']
w = ['2', '4', '8']
OTs_time_sort = [900, 4752, 15732]
OTs_symb_sort = [1440, 3168, 6624]
OTs_sort = [OTs_time_sort[i]+OTs_symb_sort[i] for i in range(len(OTs_time_sort))]
OTs_moore = [48*(256+64),48*(256+64),48*(256+64)] # k=256, s=64?
width = 0.35       # the width of the bars: can also be len(x) sequence

fig, ax = plt.subplots()

ax.bar(w, OTs_time_sort, width, label='Due to time bits (sort)')
ax.bar(w, OTs_symb_sort, width, bottom=OTs_time_sort, label='Due to symbol bits (sort)')
ax.bar(w, OTs_moore, width, bottom=OTs_sort, label='Due to symbol bits (moore)')
for i in range(3):
    ax.text(-0.125 + i, OTs_time_sort[i]+OTs_symb_sort[i]+OTs_moore[i], run_time[i], \
        color='black', fontweight='bold')

ax.set_ylabel('OTs')
ax.set_xlabel('w')
ax.set_title('Runtime Statistics by Time Window')
ax.legend()

plt.show()