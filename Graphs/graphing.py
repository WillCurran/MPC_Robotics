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

OTs_sort = [OTs_time_sort[i]+OTs_symb_sort[i] for i in range(7)]
width = 0.4       # the width of the bars: can also be len(x) sequence
x_scale = 0.6

# GRAPH 1: OTs

# fig, ax = plt.subplots()
# ax.ticklabel_format(axis='y', style='sci', scilimits=(0,1))


# ax.bar([x_scale*i for i in w], OTs_time_sort, width, label='time bits (sort)')
# ax.bar([x_scale*i for i in w], OTs_symb_sort, width, bottom=OTs_time_sort, label='symbol bits (sort)')
# ax.bar([x_scale*i for i in w], OTs_moore, width, bottom=OTs_sort, label='symbol bits (moore)')
# plt.xticks([x_scale*i for i in w], w)
# for i in range(7):
#     ax.text(x_scale*(i+0.62), 5000+OTs_time_sort[i]+OTs_symb_sort[i]+OTs_moore[i], str(run_time[i])[0:5], \
#         color='black', fontweight='bold')

# ax.set_ylabel('OTs')
# ax.set_xlabel('w')
# ax.set_title('Runtime OTs vs. Time Window')
# ax.set_position([0.1, 0.1, 0.7, 0.8])
# ax.legend()

# fig.tight_layout()
# fig.set_size_inches(w=4, h=3.75)
# plt.show()

# GRAPH 2: Rounds of communication sensors-->privacy peers

# w = [str(i) for i in range(1,8,1)]
# comm_rounds = [2**(6-i) for i in range(7)]

# fig, ax = plt.subplots()

# ax.bar([x_scale*i for i in w], rounds, width)
# plt.xticks([x_scale*i for i in w], w)
# ax.set_ylabel('rounds')
# ax.set_xlabel('w')
# ax.set_title('Communication Rounds vs. Time Window')

# ax.set_position([0.09, 0.1, 0.75, 0.8])
# fig.tight_layout()
# fig.set_size_inches(w=4, h=3.75)

# plt.show()


# Graph 3: Rounds of OTs

# fig, ax = plt.subplots()
# ax.ticklabel_format(axis='y', style='sci', scilimits=(0,3))


# ax.bar([x_scale*i for i in w], OT_rounds_sort, width, label='OT rounds (sort)')
# ax.bar([x_scale*i for i in w], OT_rounds_moore, width, bottom=OT_rounds_sort, label='OT rounds (moore)')
# plt.xticks([x_scale*i for i in w], w)
# for i in range(7):
#     ax.text(x_scale*(i+0.6), 100+OT_rounds_sort[i]+OT_rounds_moore[i], str(run_time[i])[0:5], \
#         color='black', fontweight='bold')

# ax.set_ylabel('OT rounds')
# ax.set_xlabel('w')
# ax.set_title('OT Rounds vs. Time Window')
# ax.set_position([0.1, 0.1, 0.7, 0.8])
# ax.legend()

# fig.tight_layout()
# fig.set_size_inches(w=4, h=3.75)
# plt.show()

# matplotlib.use("pgf")
# matplotlib.axes.Axes.bar
# matplotlib.pyplot.bar
# matplotlib.axes.Axes.annotate
# matplotlib.pyplot.annotate
# matplotlib.rcParams.update({
#     "pgf.texsystem": "pdflatex",
#     'font.family': 'serif',
#     'text.usetex': True,
#     'pgf.rcfonts': False,
# })
# plt.savefig('runtime_v_window.pgf', bbox_inches='tight')