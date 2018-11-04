from OSMParser import read_osm

SMALL_KRK = "map_small_krak"
KRK = "map_krk_regular"

MAP_FILE: str = SMALL_KRK
with open(MAP_FILE) as f:
    G = read_osm(f)
    print("finished parsing")

    import networkx as nx
    bb = nx.betweenness_centrality(G)
    nx.set_node_attributes(G, bb, 'nodeBetweenness')
    print("node_betweenness done")

    bbe = nx.edge_betweenness_centrality(G, normalized=False)
    nx.set_edge_attributes(G, bbe, 'edgeBetweenness')
    print("edge_betweenness done")

    nx.write_gml(G, MAP_FILE + "3.gml")
