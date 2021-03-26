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
moore_ots = []
for i in range(128):
    a = ot_recurrence.num_OTs_sort(network_sizes[which_network[i]], tao, n_symbol_bits)
    
    sort_ots.append((a[0]+a[1]))
    # print(sort_ots[-1], a[0], a[1])
    
    b = ot_recurrence.numOTs_moore_machine_eval_one_round(i+1, n_symbol_bits, n_sensors, k_prime, s)
    moore_ots.append(b)
    print(b)
ots = [sort_ots[i] + moore_ots[i] for i in range(128)]


fig, ax = plt.subplots()
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

plt.plot([math.log2(l) for l in L], ots)
plt.plot([0, 7],[moore_ots[-1], moore_ots[-1]])
plt.plot([0, 7],[0, moore_ots[-1]])

fig.tight_layout()
fig.set_size_inches(w=4, h=3.75)
plt.show()

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