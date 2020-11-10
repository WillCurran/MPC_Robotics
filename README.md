## Moore Machine notes:
- In M and PM representations of a DFA, the third number in the tuple is whatever output you want at that state. The default for output is a 4-bit number indicating which state we are at, which makes it clear that the garbled matrix evaluation is operating correctly. It also highlights the fact that there may be security issues if a state’s output gives too much away about which state we are at.
- We have to assume some bit string length for the output because in our garbled matrix representation, we mix the outputs in with the deltas in order to encrypt them. Of the form: (delta_index_0_concat_output, delta_index_1_concat_output) , where output is the same for both deltas. 
- Output currently indicates the output at the current state, not the next state which the corresponding delta index points to. However, we could implement a “Mealy Machine” version, where outputs happen along arcs in the DFA rather than at states
- Currently only supports inputs of length 3
- Oblivious Transfer is not fully randomized
- Security parameter is set to a low number. Need to add ability to crank 'k' up higher.

Run with 'python3 incremental_moore_JI/DFA_test.py'. Must have python-paillier installed.

## GMW Protocol current status:
- 2-party digital comparator of a single bit is implemented
- caveat: Need to implement 1-out-of-4 OT still. Ran into issues implementing Malek and Miri 2013 protocol with python-paillier. May go an (easier?) route which uses several 1-out-of-2 OT calls if it is simpler.
  - (https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=1512846)
