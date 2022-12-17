#!/usr/bin/env python3
"""vspath find shortest route between two points."""
import argparse
import sys
import re
import logging
import time
import yaml

import graph_tool as gt
import graph_tool.util.libgraph_tool_util
from graph_tool.draw import graph_draw
from graph_tool.search import AStarVisitor, astar_search, dijkstra_search, DijkstraVisitor
from graph_tool.topology import shortest_path
from lib.pathfinder.narrate import narrate_path
from lib.pathfinder.importers import get_importer
from lib.pathfinder.util import cardinal_dir, manhattan, parse_coord
from lib.pathfinder.config import config

logging.basicConfig(level=logging.DEBUG)
MAX_DIST = 16000  # Maximum allowed distance of the next TL in a chain
tls = set()
landmarks = {}
traders = {}

def describe_route(vertex_list, edge_list):
    """Generate written description of a path."""
    hops = 0
    total_dist = 0
    v1 = vertex_list.pop(0)
    print(f"You are starting at {coord[v1]}")
    v2 = vertex_list.pop(0)
    edg = edge_list.pop(0)

    while route:
        dist = weight[edg]
        org = coord[v1]
        dst = coord[v2]
        direction = cardinal_dir(org, dst)

        total_dist += dist
        hops += 1
        print(f"Move {int(dist)}m {direction} to {next_wp.origin} and Teleport to {next_wp.destination}")
        old_wp = next_wp
        next_wp = vertex_list.pop(0)

    dist = manhattan(as_origin(old_wp), as_destination(next_wp))
    total_dist += dist
    origin = as_origin(old_wp)
    destination = as_destination(next_wp)
    print(f"Move {int(dist)}m {cardinal_dir(origin, destination)} to your destination {next_wp}.")
    print(f"The route is {(total_dist / 1000):.2f}km long and uses {hops} hops.")

class Visitor(AStarVisitor):
    """Perform actions during A* Algorithm"""
    def __init__(self, g, target, dist, vfilt=None):
        self.graph = gt.GraphView(g, vfilt=vfilt)
        self.target = target
        self.target_coord = self.graph.vp.coord[self.target]
        self.starttime = time.time()
        self.dist = dist
        vertices = self.graph.num_vertices()
        edges = self.graph.num_edges()
        self.touched = 0
        self.added = 0
        self.expanded = {}
        logging.info(f"Searching path through {vertices} vertices with {edges} edges")

    def edge_relaxed(self, e):
        logging.debug(f"Current dist: {self.dist[e.target()]}")
        if e.target() == self.target:
            dur = time.time() - self.starttime
            logging.info(f"Finished search in {dur} seconds")
            #raise gt.search.StopSearch()

    def manhattan_heuristic(v, target):
        dist = manhattan(self.graph.vp.coord[v], self.graph.vp.coord[target])
        logging.debug(f"dist of {v} est: {dist}")
        return dist


def link_vertex(g, u, maxdist=MAX_DIST):
    for v in g.iter_vertices():
        dist = manhattan(g.vp.coord[u], g.vp.coord[v])

        if dist < maxdist and v != u:
            #logging.debug(f"{u}->{v} {dist}")
            edg = g.add_edge(u, v)
            g.ep.weight[edg] = dist
    return


if __name__ == "__main__":
    logging.debug(f"Storing Data under {config.data_file}")
    # Populate Data
    try :
        graph = gt.load_graph(config.data_file)
    except IOError:
        graph = None
        logging.warning('No existing Navgraph found')

    # import new data
    if config.dbfile:
        importer = get_importer(config.dbfile, graph)
        existing = importer.graph.num_vertices()
        importer.do_import()
        importer.make_connections()
        new = importer.graph.num_vertices()
        logging.info(f"Added {new - existing} Nodes for a total of {new}.")
        importer.graph.save(config.data_file)
        graph = importer.graph

    if config.clean:
        # override Graph file with empty Graph
        # TODO: Need to add all property maps, generator for new Graph required for importer and this
        gt.Graph.save(config.data_file, Graph(directed=True))

    if config.listlandmarks:
        pass  #TODO: Landmarks currently no thing




    # Check for an actual pathfinding task and conduct it
    origin = destination = None
    if config.origin:
        origin = parse_coord(config.origin)
    if config.goal:
        destination = parse_coord(config.goal)
    if origin and destination:
        if not graph:
            logging.error("No Graph-Data available. Try importing some data first before searching in it")
        # obtain origin vertex
        ovt = graph_tool.util.find_vertex(graph, graph.vp.coord, origin)
        if ovt:
            assert(len(ovt)==1)
            ovt = ovt[0]
            logging.debug(f"found origin to be preexisting as vertex {ovt}")
        else:
            ovt = graph.add_vertex()
            graph.vp.coord[ovt] = origin
        # obtain destination vertex
        dvt = graph_tool.util.find_vertex(graph, graph.vp.coord, destination)
        if dvt:
            assert (len(dvt) == 1)
            dvt = dvt[0]
            logging.debug(f"found destination to be preexisting as vertex {dvt}")
        else:
            dvt = graph.add_vertex()
            graph.vp.coord[dvt] = destination
        edg = graph.add_edge(ovt, dvt)
        graph.ep.weight[edg] = manhattan(origin, destination)
        coord = graph.vp.coord
        weight = graph.ep.weight
        e_is_tl = graph.ep.is_tl
        dist = graph.new_vertex_property('int', val=999999)
        maxdist = manhattan(coord[ovt], coord[dvt])
        logging.info(f"walking from {coord[ovt]} to {coord[dvt]}")
        logging.info(f"Trivial distance would be {maxdist} to walk")
        link_vertex(graph, ovt, maxdist)
        link_vertex(graph, dvt, maxdist)
        starttime = time.time()
        vertex_list, edge_list = shortest_path(graph, ovt, dvt, weight)
        logging.info(f"search took {time.time() - starttime} seconds")

        narrate_path(graph, vertex_list, edge_list)


    if config.drawgraph:
        graph_draw(graph, pos=graph.vp.coord.copy('vector<double>'), nodesfirst=False, ink_scale=0.5,
                       output_size=(2048, 2048), output='graph.png')
    sys.exit()
