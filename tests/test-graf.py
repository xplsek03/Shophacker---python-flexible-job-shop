'''
xplsek03 | 2021 | FIT VUT Brno, bakalarska prace Razeni manipulaci pro morici linky
'''

import bellmanford as bf
import networkx as nx
import matplotlib.pyplot as plt


# testovani disjunktivniho grafu na pozitivni cyklus - pomocne

G = nx.MultiDiGraph()  # G = C U Vm
G.add_node("start")

G.add_node("start")
G.add_node("end")
G.add_node(1)
G.add_node(2)
G.add_node("fake1")
G.add_node(4)
G.add_node(5)
G.add_node("fake2")
G.add_node("fakea")
G.add_node("fakeb")

G.add_edge("start", 1, weight = 0)
G.add_edge(1, 2, weight=3)
G.add_edge(2,1,weight=-4)
G.add_edge(2,"fake1", weight=2)
G.add_edge("fake1", 2, weight=-3)
G.add_edge("fake1", "end", weight=0)

G.add_edge("start", 4, weight = 0)
G.add_edge(4, 5, weight=5)
G.add_edge(5,4,weight=-7)
G.add_edge(5,"fake2", weight=1)
G.add_edge("fake2", 5, weight=-2)
G.add_edge("fake2", "fakea", weight=51)
G.add_edge("fakea", "fakeb", weight=34520)
G.add_edge("fakeb", "end", weight=0)

# broken
#G.add_edge(2, 4, weight=5)
#G.add_edge(5, 1, weight=5)
#G.add_edge("fake1", 5, weight=21)  

G.add_edge("start", "fake2", weight=100000)
#G.add_edge(4, "fake1", weight=100000) 
    
for u, v, weight in G.edges(data="weight", keys=False):
    G[u][v][0]['weight'] *= -1 
    
length, nodes, negative_cycle = bf.bellman_ford(G, "start", "end", weight='weight')
print(negative_cycle)
print(length)
print(nodes) 
            
