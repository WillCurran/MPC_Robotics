
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
            pass
# s = SortingNetwork('BUBBLE', 6)
