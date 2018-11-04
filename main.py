from OSMParser import read_osm

SMALL_KRK = "map_small_krak"
KRK = "map_krk_regular"

MAP_FILE: str = SMALL_KRK
with open(MAP_FILE) as f:
    G = read_osm(f)
    print("finished parsing")

    import networkx as nx

    nx.write_gml(G, MAP_FILE + ".gml")
