## Moore Machine notes:
- In M and PM representations of a DFA, the third number in the tuple is whatever output you want at that state. The default for output is a 4-bit number indicating which state we are at, which makes it clear that the garbled matrix evaluation is operating correctly. It also highlights the fact that there may be security issues if a state’s output gives too much away about which state we are at.
- We have to assume some bit string length for the output because in our garbled matrix representation, we mix the outputs in with the deltas in order to encrypt them. Of the form: (delta_index_0_concat_output, delta_index_1_concat_output) , where output is the same for both deltas. 
- Output currently indicates the output at the current state, not the next state which the corresponding delta index points to. However, we could implement a “Mealy Machine” version, where outputs happen along arcs in the DFA rather than at states
- Currently only supports inputs of length 3
- Oblivious Transfer is not fully randomized
- Security parameter is set to a low number. Need to add ability to crank 'k' up higher.

## To-dos:
- Get working for larger numbers (add randomness in OT)
- Get working for larger security parameters (Python int size question?)
- Interface with an input file from beams simulation
- Generate chunks of Garbled Matrix in a smarter way (Currently adding one line at a time. In the end, will need to have dynamic size since we're processing a possibly neverending stream of inputs)
- Put Alice and Bob into different processes (This might involve linking up with the GMW code so may not need to do a lot of extra work here)
- Add in batch OT and random OT pre-computation (Same story as above)

Run with 'python3 incremental_moore_JI/DFA_test.py'. Must have python-paillier installed.

## GMW Protocol / Sorting Network notes:
- in progress

## To-dos:
- Add OT and random OT pre-computation
- Get working for larger numbers (parallelize OT)
- Add sorting network data structure and evaluation
- link with Moore Machine code
- interface with input from simulation (add additional layer of sensor parties in other processes)
