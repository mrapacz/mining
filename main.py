from OSMParser import read_osm
import logging
import networkx as nx

SMALL_KRK = "map_small_krak"
KRK = "map_krk_regular"

logging.basicConfig(level=logging.INFO)

MAP_FILE: str = SMALL_KRK
with open(MAP_FILE) as f:
    G = read_osm(f)
    logging.info("Map parsed")

    bb = nx.betweenness_centrality(G)
    nx.set_node_attributes(G, bb, 'betweenness_centrality_n')

    logging.info("Betweenness centrality for nodes computed")

    bbe = nx.edge_betweenness_centrality(G, normalized=False)
    nx.set_edge_attributes(G, bbe, 'betweenness_centrality_e')

    logging.info("Betweenness centrality for edges computed")

    output_file = MAP_FILE + ".gml"
    nx.write_gml(G, output_file)
    
    logging.info("Output saved to {}".format(output_file))
