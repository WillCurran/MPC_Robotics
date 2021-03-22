import matplotlib
import matplotlib.pyplot as plt
import testing_parser

data = testing_parser.get_graphing_data()
rounds = data[0]
w = data[1]
run_time = data[2]
OTs_time_sort = data[3]
OTs_symb_sort = data[4]
OT_rounds_sort = data[5]
OTs_moore = data[6]
OT_rounds_moore = data[7]

# GRAPH 1: OTs

OTs_sort = [OTs_time_sort[i]+OTs_symb_sort[i] for i in range(7)]
width = 0.35       # the width of the bars: can also be len(x) sequence

fig, ax = plt.subplots()

ax.bar(w, OTs_time_sort, width, label='time bits (sort)')
ax.bar(w, OTs_symb_sort, width, bottom=OTs_time_sort, label='symbol bits (sort)')
ax.bar(w, OTs_moore, width, bottom=OTs_sort, label='symbol bits (moore)')
for i in range(7):
    ax.text(i+0.65, 5000+OTs_time_sort[i]+OTs_symb_sort[i]+OTs_moore[i], str(run_time[i])[0:5], \
        color='black', fontweight='bold')

ax.set_ylabel('OTs')
ax.set_xlabel('w')
ax.set_title('Cumulative Runtime vs. Time Window')
ax.legend()

fig.tight_layout()
fig.set_size_inches(w=3.5, h=4)
plt.show()

# GRAPH 2: Rounds of communication sensors-->privacy peers

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


# Graph 3: Rounds of OTs


matplotlib.use("pgf")
matplotlib.axes.Axes.bar
matplotlib.pyplot.bar
matplotlib.axes.Axes.annotate
matplotlib.pyplot.annotate
matplotlib.rcParams.update({
    "pgf.texsystem": "pdflatex",
    'font.family': 'serif',
    'text.usetex': True,
    'pgf.rcfonts': False,
})
# plt.savefig('runtime_window.pgf')