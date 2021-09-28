import math
import ot_recurrence
import matplotlib
import matplotlib.pyplot as plt

k = 256
s = 64
n_states = 12 # moore states
k_prime = k + math.ceil(math.log2(n_states))
# total_time = 128 # total timeframe
tao = 7 # time bits
n_sensors = 3
n_symbol_bits = 2
L = [t for t in range(1,129)] # sparsity
which_network = [2**(math.ceil(math.log2(n_sensors*i))) for i in range(1,129)]
# n_rounds = [math.ceil(128 / 2**(math.ceil(math.log2(i)))) for i in range(1,129)]
network_sizes = {4: 4, 8: 12, 16: 34, 32: 90, 64: 226, 128: 546, 256: 1282, 512: 2946}

sort_ots = []
sort_time_ots = []
sort_sym_ots = []
moore_ots = []
for i in range(128):
    a = ot_recurrence.num_OTs_sort(network_sizes[which_network[i]], tao, n_symbol_bits)
    sort_time_ots.append(a[0])
    sort_sym_ots.append(a[1])
    sort_ots.append((a[0]+a[1]))
    # print(sort_ots[-1], a[0], a[1])
    
    b = ot_recurrence.numOTs_moore_machine_eval_one_round(i+1, n_symbol_bits, n_sensors, k_prime, s)
    moore_ots.append(b)
    # print(b)
ots = [sort_ots[i] + moore_ots[i] for i in range(128)]


fig, ax = plt.subplots()

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

# log scale y
ots = [math.log2(ots[i]) for i in range(128)]
# sort_time_ots = [math.log2(moore_ots[i]+sort_time_ots[i]) for i in range(128)]
sort_sym_ots = [math.log2(moore_ots[i]+sort_sym_ots[i]) for i in range(128)]
moore_ots = [math.log2(moore_ots[i]) for i in range(128)]

colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

# search for intersection
j = 0
while ots[j] < moore_ots[-1]:
    j += 1
inter_x = (math.log2(L[j-1])+math.log2(L[j])) / 2.0
print(inter_x)

plt.plot([math.log2(l) for l in L], ots, 'black', linewidth=2)
plt.plot([0, 7],[moore_ots[-1], moore_ots[-1]], 'r', linewidth=2)
plt.plot([math.log2(l) for l in L], moore_ots, 'black', linewidth=2)
plt.plot([inter_x, inter_x], [moore_ots[0], ots[-1]], '--k')

outline_x = [math.log2(l) for l in L]
outline_x.append(7)
outline_y = moore_ots
outline_y.append(moore_ots[0])
plt.fill(outline_x, outline_y, colors[2], label='symbol bits (moore)')

outline_x = [math.log2(l) for l in L]
outline_x.extend([math.log2(L[i]) for i in range(127, -1, -1)])
outline_y = sort_sym_ots
outline_y.extend([moore_ots[i] for i in range(127, -1, -1)])
plt.fill(outline_x, outline_y, colors[1], label='symbol bits (sort)')

outline_x = [math.log2(l) for l in L]
outline_x.extend([math.log2(L[i]) for i in range(127, -1, -1)])
outline_y = ots
outline_y.extend([sort_sym_ots[i] for i in range(127, -1, -1)])
plt.fill(outline_x, outline_y, colors[0], label='time bits (sort)')

ticks = [2, 4, 8, 16, 32, 64, 128]
plt.xticks([math.log2(ticks[i]) for i in range(7)], ticks)
ax.set_ylabel('OTs')
ax.set_xlabel('L')
ax.set_title('OTs (Sparse vs. Padded)')
ax.set_position([0.1, 0.1, 0.7, 0.8])
ax.legend()

handles,labels = ax.get_legend_handles_labels()

fig.tight_layout()
fig.set_size_inches(w=4, h=3.75)



plt.show()

# fig1, axe = plt.subplots()
# axe.legend(handles, labels)
# axe.xaxis.set_visible(False)
# axe.yaxis.set_visible(False)
# for v in axe.spines.values():
#     v.set_visible(False)
# axe.set_position([0.65, 0.5, 0.3, 0.5])
# fig1.set_size_inches(w=2.25, h=0.8)
# plt.show()


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