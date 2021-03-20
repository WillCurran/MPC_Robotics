#!/bin/bash

#<Mode> [total_time] [time_window_bits] [n_sensors] [n_symbols]
file=main.py
mode=A
total_time=127
n_sensors=3
n_symbols=3
for w in {1..7}; do 
    for i in {1..1}; do 
        python3 $file $mode $total_time $w $n_sensors $n_symbols; 
    done
done
