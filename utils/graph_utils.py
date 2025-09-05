import networkx as nx
from config import CAMPUS_POS, college_b1_interior

def create_campus_graph():
    G = nx.Graph()
    G.add_nodes_from(CAMPUS_POS.keys())
    edges = [
        ("Gate 1", "Gate 2", 45), ("Gate 2", "Gate 3", 50),
        ("Gate 2", "Library", 18), ("Gate 2", "College B1", 25),
        ("Gate 1", "College B2", 25), ("Gate 3", "Library", 18),
        ("Library", "Canteen", 22), ("Canteen", "Gym", 15),
        ("College B1", "College B3", 12), ("College B3", "College B2", 15),
        ("College B2", "Canteen", 20),
    ]
    for u, v, w in edges:
        G.add_edge(u, v, weight=w)
    return G

def dijkstra_nx(G, src, dst):
    try:
        return nx.single_source_dijkstra(G, src, dst)
    except Exception:
        return float("inf"), []

def dijkstra_interior(start, dest):
    G = nx.Graph()
    for u, nbrs in college_b1_interior.items():
        for v, w in nbrs.items():
            G.add_edge(u, v, weight=w)
    try:
        return nx.single_source_dijkstra(G, start, dest)
    except Exception:
        return float("inf"), []
