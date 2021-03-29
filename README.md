## Disclaimer
- This is an implementation of the protocol defined by Bobadilla, Shell, Rojas and Curran (2021)
- It includes rudimentary from-scratch implementations of GMW Protocol and Oblivious DFA evaluation [Zhao et. al], with two parties simulated by separate processes on the same machine.
- We make no claims of real security in this implementation because we are not CPython experts, nor are we practical security experts.
- The main purpose of this repository is to act as a local proof of concept implementation, and it does not consider some practical necessities which are normally a given when communicating over a public channel.

## User notes
- src/main.py is the primary program. It offers several modes of operation, but the primary one is 'Automatic' Mode, which consumes data from the data/ directory, then performs several rounds of execution of a secure sort, followed by a secure moore machine evaluation.
- If you're interested in how the code works, some good places to start are src/Party.py, src/DFA_matrix.py and src/garbled_circuit.py
- BeamReader/BeamReader.py provides a way to generate secret-shared files if given files containing times of sensor observations. We run a simulator in a separate private repository to generate the sensor observations. Once the secret-shared files are generated in shares_a and shares_b, they can be transferred to the data/ directory to be consumed by the main program.
- A key component of both sorting and moore machine evaluation is oblivious transfer. We assume that single-bit random oblivious transfers have already been precomputed between the two parties, and the results are stored in the files a.txt, b.txt, a1.txt, b1.txt, where 'a' means sender and 'b' means receiver. OTs can be very expensive, since they require asymmetric operations and sometimes many rounds of communication between parties.

## Moore Machine notes:
- Security parameter 'k' and statistical security parameter 's' can be set to different values depending on security requirements. They provide a tradeoff between security and performance

## Beam Reader:
Usage Example: 
py BeamReader.py {START TIME} {END TIME(NON-INCLUSIVE)} {PAD UP TO PWR OF 2 (T/F)} [LIST OF BEAM LABELS]
py BeamReader.py 5 10 a b c

## Python Packages: 
atomicwrites    1.4.0
attrs           20.3.0
certifi         2020.12.5
cffi            1.14.5
chardet         4.0.0
colorama        0.4.4
crypto          1.4.1
cycler          0.10.0
decorator       4.4.2
dill            0.3.3
gmpy2           2.0.8
idna            2.10
iniconfig       1.1.1
kiwisolver      1.3.1
libnum          1.7.1
lxml            4.6.3
matplotlib      3.3.4
multiprocess    0.70.11.1
Naked           0.1.31
networkx        2.5
numpy           1.20.1
packaging       20.9
pandas          1.2.3
phe             1.4.0
Pillow          8.1.2
pip             21.0.1
pluggy          0.13.1
py              1.10.0
pyasn1          0.4.8
pycparser       2.20
pycryptodome    3.10.1
pydot           1.4.2
pygame          2.0.1
pygraphviz      1.7
pyparsing       2.4.7
PySDL2          0.9.7
pytest          6.2.2
python-dateutil 2.8.1
pytz            2021.1
PyYAML          5.4.1
requests        2.25.1
rsa             4.7.1
scipy           1.6.1
setuptools      49.2.1
shellescape     3.8.1
six             1.15.0
thread6         0.2.0
toml            0.10.2
urllib3         1.26.3
websockets      8.1
wheel           0.36.2
