N_REPETITIONS = 8

def get_graphing_data():
    rounds = []
    w = []
    times = []
    ots_time_sort = []
    ots_symbol_sort = []
    ot_rounds_sort = []
    ots_moore = []
    ot_rounds_moore = []
    with open('testing_output.txt', 'r') as f:
        for line in f:
            line = line.split()
            rounds.append(int(line[0]))
            w.append(int(line[1]))
            times.append(float(line[2]))
            ots_time_sort.append(int(line[3]))
            ots_symbol_sort.append(int(line[4]))
            ot_rounds_sort.append(int(line[5]))
            ots_moore.append(int(line[6]))
            ot_rounds_moore.append(int(line[7]))
    l = len(rounds)
    r_avg = [rounds[i] for i in range(0, l, N_REPETITIONS)]
    w_avg = [w[i] for i in range(0, l, N_REPETITIONS)]
    t_avg = [sum(times[i:i+N_REPETITIONS]) / float(N_REPETITIONS) for i in range(0, l, N_REPETITIONS)]
    ots_time_sort_avg = [ots_time_sort[i] for i in range(0, l, N_REPETITIONS)]
    ots_symbol_sort_avg = [ots_symbol_sort[i] for i in range(0, l, N_REPETITIONS)]
    ot_rounds_sort_avg = [ot_rounds_sort[i] for i in range(0, l, N_REPETITIONS)]
    ots_moore_avg = [ots_moore[i] for i in range(0, l, N_REPETITIONS)]
    ot_rounds_moore_avg = [ot_rounds_moore[i] for i in range(0, l, N_REPETITIONS)]
    return (r_avg, w_avg, t_avg, ots_time_sort_avg, 
        ots_symbol_sort_avg, ot_rounds_sort_avg, ots_moore_avg, 
        ot_rounds_moore_avg)

print(get_graphing_data())