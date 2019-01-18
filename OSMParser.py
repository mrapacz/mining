"""
Read directional graph from Open Street Maps osm format

Based on the osm to networkx tool from aflaxman : https://gist.github.com/aflaxman/287370/
Use python3.6

Added : 
- : Python3.6 compatibility
- : Cache for avoiding to download again the same osm tiles
- : distance computation to estimate length of each ways (useful to compute the shortest path)

Copyright (C) 2017 Loïc Messal (github : Tofull)
Copyright (C) 2019 Maciej Rapacz, Jakub Tustanowski (github : mrapacz)
"""

## Modules
# Elementary modules
from math import radians, cos, sin, asin, sqrt
import copy

# Graph module
from typing import Tuple, Dict

import networkx

# Specific modules
import xml.sax  # parse osm file
from pathlib import Path  # manage cached tiles


def haversine(lon1, lat1, lon2, lat2, unit_m=True):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    default unit : km
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers. Use 3956 for miles
    if (unit_m):
        r *= 1000
    return c * r


def read_osm(filename_or_stream, only_roads=True) -> Tuple[networkx.DiGraph, networkx.DiGraph, Dict]:
    """Read graph in OSM format from file specified by name or by stream object.
    Parameters
    ----------
    filename_or_stream : filename or stream object

    Returns
    -------
    G : Graph

    Examples
    --------
    # >>> G=nx.read_osm(nx.download_osm(-122.33,47.60,-122.31,47.61))
    # >>> import matplotlib.pyplot as plt
    # >>> plt.plot([G.node[n]['lat']for n in G], [G.node[n]['lon'] for n in G], 'o', color='k')
    # >>> plt.show()
    """
    osm = OSM(filename_or_stream)
    G = networkx.DiGraph()

    # optimization
    G_small = networkx.DiGraph()
    mapping = {}

    highway_types = (
        'motorway',
        'trunk',
        'primary',
        'secondary',
        'tertiary',
        'unclassified',
        'residential',
    )

    ## Add ways
    for w in osm.ways.values():
        if only_roads and 'highway' not in w.tags:
            continue

        if w.tags['highway'] not in highway_types:
            continue

        if 'oneway' in w.tags and w.tags['oneway'] == 'yes':
            w.add_to_graph(G, G_small, mapping, oneway=True)
        else:
            w.add_to_graph(G, G_small, mapping)

    def complete_information(G, osm):
        # Complete the used nodes' information
        for n_id in G.nodes():
            n = osm.nodes[n_id]
            G.node[n_id]['lat'] = n.lat
            G.node[n_id]['lon'] = n.lon
            G.node[n_id]['id'] = n.id

        # Estimate the length of each way
        for u, v, d in G.edges(data=True):
            distance = haversine(
                G.node[u]['lon'],
                G.node[u]['lat'],
                G.node[v]['lon'],
                G.node[v]['lat'],
                unit_m=True,
            )  # Give a realistic distance estimation (neither EPSG nor projection nor reference system are specified)

            G.add_weighted_edges_from([(u, v, distance)], weight='length')

    complete_information(G, osm)
    complete_information(G_small, osm)

    return G, G_small, mapping


class Node:
    def __init__(self, id, lon, lat):
        self.id = id
        self.lon = lon
        self.lat = lat
        self.tags = {}

    def __str__(self):
        return "Node (id : %s) lon : %s, lat : %s " % (self.id, self.lon, self.lat)


class Way:
    def __init__(self, id, osm):
        self.osm = osm
        self.id = id
        self.nds = []
        self.tags = {}

    def split(self, dividers):
        # slice the node-array using this nifty recursive function
        def slice_array(ar, dividers):
            for i in range(1, len(ar) - 1):
                if dividers[ar[i]] > 1:
                    left = ar[:i + 1]
                    right = ar[i:]

                    rightsliced = slice_array(right, dividers)

                    return [left] + rightsliced
            return [ar]

        slices = slice_array(self.nds, dividers)

        # create a way object for each node-array slice
        ret = []
        i = 0
        for slice in slices:
            littleway = copy.copy(self)
            littleway.id += "-%d" % i
            littleway.nds = slice
            ret.append(littleway)
            i += 1

        return ret

    def add_to_graph(self, graph, graph_small, mapping, oneway=False):
        nodes = self.nds
        if 'name' not in self.tags:
            name = ""
        else:
            name = self.tags['name']

        middle_edge_idx = len(nodes) // 2

        related_edges = []
        for node_index, node in enumerate(nodes):
            if node_index < len(nodes) - 1:
                next_node = nodes[node_index + 1]

                current_name = name if node_index == middle_edge_idx else ""

                edge_id = "{}_{}".format(self.id, node_index)
                graph.add_edge(
                    node,
                    next_node,
                    id=edge_id,
                    name=current_name,
                )
                related_edges.append((node, next_node))

                if not oneway:
                    edge_id = "{}_{}_d".format(self.id, node_index)
                    graph.add_edge(
                        next_node,
                        node,
                        id=edge_id,
                        name="",
                    )
                    related_edges.append((next_node, node))

        mapping[self.id] = related_edges
        graph_small.add_edge(
            nodes[0],
            nodes[-1],
            id=self.id
        )


class OSM:
    def __init__(self, filename_or_stream):
        """ File can be either a filename or stream/file object."""
        nodes = {}
        ways = {}

        superself = self

        class OSMHandler(xml.sax.ContentHandler):
            @classmethod
            def setDocumentLocator(self, loc):
                pass

            @classmethod
            def startDocument(self):
                pass

            @classmethod
            def endDocument(self):
                pass

            @classmethod
            def startElement(self, name, attrs):
                if name == 'node':
                    self.currElem = Node(attrs['id'], float(attrs['lon']), float(attrs['lat']))
                elif name == 'way':
                    self.currElem = Way(attrs['id'], superself)
                elif name == 'tag':
                    self.currElem.tags[attrs['k']] = attrs['v']
                elif name == 'nd':
                    self.currElem.nds.append(attrs['ref'])

            @classmethod
            def endElement(self, name):
                if name == 'node':
                    nodes[self.currElem.id] = self.currElem
                elif name == 'way':
                    ways[self.currElem.id] = self.currElem

            @classmethod
            def characters(self, chars):
                pass

        xml.sax.parse(filename_or_stream, OSMHandler)

        self.nodes = nodes
        self.ways = ways

        # count times each node is used
        node_histogram = dict.fromkeys(self.nodes.keys(), 0)
        for way in self.ways.values():
            if len(way.nds) < 2:  # if a way has only one node, delete it out of the osm collection
                del self.ways[way.id]
            else:
                for node in way.nds:
                    node_histogram[node] += 1

        # use that histogram to split all ways, replacing the member set of ways
        new_ways = {}
        for id, way in self.ways.items():
            split_ways = way.split(node_histogram)
            for split_way in split_ways:
                new_ways[split_way.id] = split_way
        self.ways = new_ways
