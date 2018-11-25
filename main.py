from collections import Counter

from OSMParser import read_osm
import logging
import networkx as nx

SMALL_KRK = "map_small_krak"
KRK = "map_krk_regular"

logging.basicConfig(level=logging.INFO, format="%(asctime)s: %(message)s")

MAP_FILE: str = SMALL_KRK


def main():
    logging.info("Beginning map parsing")
    with open(MAP_FILE) as f:
        G, G_small, mapping = read_osm(f)

        logging.info("Map parsed")

        c = Counter([len(values) for values in mapping.values()])
        logging.info("Mapping optimization: {}".format(c))
        logging.info("Edges: old: {}, optimized: {}".format(G.number_of_edges(), G_small.number_of_edges()))

        small_betweenness = nx.edge_betweenness_centrality(G_small, normalized=False, weight='length')
        main_betweenness = {}

        logging.info("Small betweenness computed")
        for (u, v), value in small_betweenness.items():
            edge_data = G_small.get_edge_data(u, v)
            general_edge_id = edge_data['id']
            for edge in mapping[general_edge_id]:
                main_betweenness[edge] = value

        logging.info("Main betweenness computed")

        nx.set_edge_attributes(G, main_betweenness, 'betweenness')
        #
        # logging.info("Betweenness centrality for edges computed")
        #
        dump_to_file(G)


def dump_to_file(G):
    output_file = MAP_FILE + ".gml"
    nx.write_gml(G, output_file)
    logging.info("Output saved to {}".format(output_file))


if __name__ == '__main__':
    main()
