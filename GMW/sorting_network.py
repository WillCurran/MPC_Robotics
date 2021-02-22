
# Specify a sorting network, and provide constructors for different instances
# A sorting network is a static structure which specifies a topological order of swaps
# to make to sort a list.
# It is represented as a 2D list of index tuples - each sub-list is at the same topological level, 
# and thus can be parallelized if desired.
class SortingNetwork:
    # types are 'BUBBLE' and 'EVEN-ODD'
    def __init__(self, type, n):
        self.swaps = []
        if type == 'BUBBLE':
            for i in range(n-1):
                self.swaps.append([])
                for j in range(n-i-1):
                    self.swaps[i].append((j, j+1))
            print(self.swaps)

# s = SortingNetwork('BUBBLE', 6)
