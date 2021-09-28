import matplotlib as mpl
import matplotlib.pyplot as plt
import networkx as nx
#Based on https://networkx.org/documentation/stable//auto_examples/drawing/plot_directed.html
#G = nx.generators.directed.random_k_out_graph(10, 3, 0.5)
G = nx.DiGraph()
G.add_nodes_from([0,1,2,3])

#edges
G.add_edge(0,1)
G.add_edge(0,3)
G.add_edge(0,2)
G.add_edge(1,0)
G.add_edge(1,2)
G.add_edge(1,3)
G.add_edge(2,3)
G.add_edge(2,1)
G.add_edge(2,0)
G.add_edge(3,2)
G.add_edge(3,0)
G.add_edge(3,1)

pos = nx.layout.circular_layout(G, scale=1)
pos[3] = [0, .40]
node_sizes = [2000 for i in range(len(G))]
node_sizes[3] = 8000
M = G.number_of_edges()
edge_colors = range(2, M + 2)
edge_alphas = [(5 + i) / (M + 4) for i in range(M)]

nodes = nx.draw_networkx_nodes(G,
        pos,
        node_size=node_sizes,
        node_color=('green','green','green','yellow')
    )
edges = nx.draw_networkx_edges(
    G,
    pos,
    node_size=node_sizes,
    arrowstyle="->",
    arrowsize=10,
    #edge_color=edge_colors,
    #edge_cmap=plt.cm.Reds,
    width=3,
)
# set alpha value for each edge
#for i in range(M):
    #edges[i].set_alpha(edge_alphas[i])

labels={}
labels[0]=r'$\{12,21\}$'
labels[1]=r'$\{02,20\}$'
labels[2]=r'$\{01,10\}$'
labels[3]=r'$\{00\},\{11\},\{22\}$'
nx.draw_networkx_labels(G,pos,labels,font_size=11, font_color='black')

edge_labels = {
    (0,1): 'a',
    (0,3): 'b',
    (0,2): 'c',
    (2,3): 'a',
    (2,1): 'b',
    (1,3): 'c',
}
nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=15)
#pc = mpl.collections.PatchCollection(edges, cmap=plt.cm.Reds)
#pc.set_array(edge_colors)
#plt.colorbar(pc)

ax = plt.gca()
ax.set_axis_off()
plt.show()