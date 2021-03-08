
# Specify a sorting network, and provide constructors for different instances
# A sorting network is a static structure which specifies a topological order of swaps
# to make to sort a list.
# represented as a list of index tuples to compare and swap if necessary.
# TODO - could group swaps into parallelizable bundles.
class SortingNetwork:
    # types are 'BUBBLE' and 'ODD-EVEN'
    def __init__(self, type, n):
        self.swaps = []
        if type == 'BUBBLE':
            for i in range(n-1):
                for j in range(n-i-1):
                    self.swaps.append((j, j+1))
            # print(self.swaps)
        elif type == 'ODD-EVEN':
            if n == 16:
                self.swaps = [(0, 1), (2, 3), (0, 2), (1, 3), (1, 2), (4, 5), (6, 7), 
                (4, 6), (5, 7), (5, 6), (0, 4), (2, 6), (2, 4), (1, 5), (3, 7), 
                (3, 5), (1, 2), (3, 4), (5, 6), (8, 9), (10, 11), (8, 10), 
                (9, 11), (9, 10), (12, 13), (14, 15), (12, 14), (13, 15), 
                (13, 14), (8, 12), (10, 14), (10, 12), (9, 13), (11, 15), 
                (11, 13), (9, 10), (11, 12), (13, 14), (0, 8), (4, 12), 
                (4, 8), (2, 10), (6, 14), (6, 10), (2, 4), (6, 8), (10, 12), 
                (1, 9), (5, 13), (5, 9), (3, 11), (7, 15), (7, 11), (3, 5),
                (7, 9), (11, 13), (1, 2), (3, 4), (5, 6), (7, 8), (9, 10),
                (11, 12), (13, 14)
            ]
            else:
                print("ODD-EVEN NOT IMPLEMENTED")
                exit
# s = SortingNetwork('BUBBLE', 6)
