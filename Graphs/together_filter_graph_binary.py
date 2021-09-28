import matplotlib as mpl
import matplotlib.pyplot as plt
import networkx as nx
#Based on https://networkx.org/documentation/stable//auto_examples/drawing/plot_directed.html
#G = nx.generators.directed.random_k_out_graph(10, 3, 0.5)
G = nx.DiGraph()
G.add_nodes_from(range(12))

#edges
G.add_edge(0,1)
G.add_edge(0,2)
G.add_edge(1,3)
G.add_edge(1,9)
G.add_edge(2,6)
G.add_edge(2,0)
G.add_edge(3,4)
G.add_edge(3,5)
G.add_edge(4,0)
G.add_edge(4,6)
G.add_edge(5,9)
G.add_edge(5,3)
G.add_edge(6,7)
G.add_edge(6,8)
G.add_edge(7,9)
G.add_edge(7,3)
G.add_edge(8,0)
G.add_edge(8,6)
G.add_edge(9,10)
G.add_edge(9,11)
G.add_edge(10,6)
G.add_edge(10,0)
G.add_edge(11,3)
G.add_edge(11,9)

pos = nx.layout.shell_layout(G)
pos[3] = [0, -.35]
pos[9] = [0, .20]
node_sizes = [300 for i in range(len(G))]
node_sizes[0] = 2000
node_sizes[3] = 2000
node_sizes[6] = 2000
node_sizes[9] = 5000
M = G.number_of_edges()
edge_colors = range(2, M + 2)
edge_alphas = [(5 + i) / (M + 4) for i in range(M)]

nodes = nx.draw_networkx_nodes(G,
        pos,
        node_size=node_sizes,
        node_color=('green','gray','gray','green','gray','gray','green','gray','gray','yellow','gray','gray',)
    )
edges = nx.draw_networkx_edges(
    G,
    pos,
    node_size=node_sizes,
    arrowstyle="->",
    arrowsize=10,
    #edge_color=edge_colors,
    #edge_cmap=plt.cm.Reds,
    width=2,
)
# set alpha value for each edge
#for i in range(M):
    #edges[i].set_alpha(edge_alphas[i])

labels={}
labels[0]=r'$\{12,21\}$'
labels[1]=''
labels[2]=''
labels[3]=r'$\{02,20\}$'
labels[4]=''
labels[5]=''
labels[6]=r'$\{01,10\}$'
labels[7]=''
labels[8]=''
labels[9]=r'$\{00\},\{11\},\{22\}$'
labels[10]=''
labels[11]=''
nx.draw_networkx_labels(G,pos,labels,font_size=9, font_color='black')

edge_labels = {
    (0,1):0,
    (0,2):1,
    (1,3):0,
    (1,9):1,
    (2,6):0,
    (2,0):1,
    (3,4):0,
    (3,5):1,
    (4,0):0,
    (4,6):1,
    (5,9):0,
    (5,3):1,
    (6,7):0,
    (6,8):1,
    (7,9):0,
    (7,3):1,
    (8,0):0,
    (8,6):1,
    (9,10):0,
    (9,11):1,
    (10,6):0,
    (10,0):1,
    (11,3):0,
    (11,9):1
}
nx.draw_networkx_edge_labels(G, pos, edge_labels)
#pc = mpl.collections.PatchCollection(edges, cmap=plt.cm.Reds)
#pc.set_array(edge_colors)
#plt.colorbar(pc)

ax = plt.gca()
ax.set_axis_off()
plt.show()