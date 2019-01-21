import random
from collections import Counter

from OSMParser import read_osm, haversine
import logging
import networkx as nx

SMALL_KRK = "map_small_krak"
KRK = "map_krk_regular"

logging.basicConfig(level=logging.INFO, format="%(asctime)s: %(message)s")

MAP_FILE: str = KRK


def main():
    logging.info("Beginning map parsing")
    with open(MAP_FILE) as f:
        G, G_small, mapping = read_osm(f)

        logging.info("Map parsed")

        node_ids = (
            ("283114559", "206373246"),
            ("1606819475", "251691058"),
            ("1714504148", "272496167"),
            ("1243483338", "4993281883"),
        )

        for idx, (node_a, node_b) in enumerate(node_ids):
            edge_id = "new_edge_{}".format(idx)
            length = haversine(
                G.node[node_a]['lon'],
                G.node[node_a]['lat'],
                G.node[node_b]['lon'],
                G.node[node_b]['lat'],
            )
            logging.info("Adding edge between {} and {} with length {}m".format(node_a, node_b, length))
            G.add_edge(
                node_a,
                node_b,
                name="NEW STREET",
                id=edge_id,
                length=length,
            )

            G_small.add_edge(
                node_a,
                node_b,
                name="NEW STREET",
                id=edge_id,
                length=length,
            )

            mapping[edge_id] = [(node_a, node_b)]

        c = Counter([len(values) for values in mapping.values()])
        logging.info("Mapping optimization: {}".format(c))
        logging.info("Edges: old: {}, optimized: {}".format(G.number_of_edges(), G_small.number_of_edges()))

        # pagerank

        small_pagerank = nx.pagerank(G_small, weight='length')
        main_pagerank = {}

        nx.set_node_attributes(G, small_pagerank, 'pagerank')

        logging.info("Small pagerank computed")

        # for node_id, value in small_pagerank.items():
        #     edge_data = G_small.get_edge_data(u, v)
        #     general_edge_id = edge_data['id']
        #     for edge in mapping[general_edge_id]:
        #         main_pagerank[edge] = value

        logging.info("Main pagerankcomputed")

        # betweenness centrality

        small_betweenness = nx.edge_betweenness_centrality(G_small, normalized=False, weight='length')
        logging.info("Small betweenness computed")
        main_betweenness = {}

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
