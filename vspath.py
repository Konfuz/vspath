#!/usr/bin/env python3
"""vspath find shortest route between two points."""
import argparse
import sys
import re
import logging
import pickle
import time
import gc

import graph_tool as gt
import graph_tool.util.libgraph_tool_util
from graph_tool.draw import graph_draw
from graph_tool.search import AStarVisitor, astar_search, dijkstra_search, DijkstraVisitor
from lib.pathfinder.importers import get_importer
from lib.pathfinder.datastructures import Node, Route
from lib.pathfinder.util import cardinal_dir, manhattan

logging.basicConfig(level=logging.DEBUG)
MAX_DIST = 16000  # Maximum allowed distance of the next TL in a chain
MAX_TIME = 6  # Maximum time allowed to find a route in seconds
tls = set()
landmarks = {}
traders = {}

class PathSolver():

    def describe_route(self, route):
        """Generate written description of a path."""
        hops = 0
        total_dist = 0
        old_wp = route.pop(0)
        print(f"You are starting at {old_wp}")
        next_wp = route.pop(0)

        def as_origin(a):
            if type(a) == Node:
                return a.destination
            return a

        def as_destination(a):
            if type(a) == Node:
                return a.origin
            return a

        while route:
            dist = manhattan(as_origin(old_wp), as_destination(next_wp))
            origin = as_origin(old_wp)
            destination = as_destination(next_wp)
            direction = cardinal_dir(origin, destination)

            total_dist += dist
            hops += 1
            print(f"Move {int(dist)}m {direction} to {next_wp.origin} and Teleport to {next_wp.destination}")
            old_wp = next_wp
            next_wp = route.pop(0)

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
    epilog = """Imports points_of_interest.tsv from the Map folder and translocators_lines.geojson from the webmap"""
    parser = argparse.ArgumentParser(description=__doc__,
                                     epilog=epilog)
    parser.add_argument('-i', '--import',
                        metavar='dbfile',
                        dest='dbfile',
                        help='file to import')
    parser.add_argument('-t', '--timelimit',
                        metavar='seconds',
                        type=int,
                        default=1,
                        help='seconds after which the search gets aborted with an approximate-result')
    parser.add_argument('-c', '--clean',
                        action='store_true',
                        help='clears the entire database')
    parser.add_argument('origin',
                        help='origin coordinate x,y or landmark',
                        nargs='?')
    parser.add_argument('goal',
                        help='target coordinate x,y or landmark',
                        nargs='?')
    parser.add_argument('--listlandmarks', action='store_true', help='output known landmarks')
    parser.add_argument('-d', '--data',
                        metavar='graphfile',
                        dest='graphfile',
                        default='navgraph.gt',
                        help='database file in graphtool format *.gt')

    # Hack to prevent negative coordinates to be parsed as options by argparse
    args = sys.argv
    pat = '-?[0-9]+,-?[0-9]+'
    try:
        if re.match(pat, args[-2]) or re.match(pat, args[-1]):
            args.insert(-2, '--')
    except IndexError:
        pass  # Lack of parameters

    args = parser.parse_args()

    # Populate Data
    try :
        print(args.graphfile)
        graph = gt.load_graph(args.graphfile)
    except IOError:
        graph = None

    # import new data
    if args.dbfile:
        importer = get_importer(args.dbfile, graph)
        existing = importer.graph.num_vertices()
        importer.do_import()
        importer.make_connections()
        new = importer.graph.num_vertices()
        logging.info(f"Added {new - existing} Nodes for a total of {new}.")
        importer.graph.save(args.graphfile)
        graph = importer.graph

    if args.clean:
        # override Graph file with empty Graph
        # TODO: Need to add all property maps, generator for new Graph required for importer and this
        gt.Graph.save(args.graphfile, Graph(directed=True))

    if args.listlandmarks:
        pass  #TODO: Landmarks currently no thing

    def parse_coord(coord_str):
        try:
            x, y = re.split(',', coord_str)
            x = int(x)
            y = int(y)
            return (x, y)
        except ValueError:
            logging.debug("coordinate could not be parsed as x,y")
        try:
            return landmarks[coord_str]
        except KeyError:
            logging.error(f"Unknown coordinate: {coord_str}")
        return None


    # Check for an actual pathfinding task and conduct it
    origin = destination = None
    if args.origin:
        origin = parse_coord(args.origin)
    if args.goal:
        destination = parse_coord(args.goal)
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
        weight = graph.ep.weight
        dist = graph.new_vertex_property('int', val=999999)
        maxdist = manhattan(graph.vp.coord[ovt], graph.vp.coord[dvt])
        logging.info(f"walking from {graph.vp.coord[ovt]} to {graph.vp.coord[dvt]}")
        logging.info(f"Trivial distance would be {maxdist} to walk")
        visitor = Visitor(graph, dvt, dist)
        visitor = DijkstraVisitor()
        link_vertex(graph, ovt, maxdist)
        link_vertex(graph, dvt, maxdist)
        starttime = time.time()
        dist, pred = dijkstra_search(graph, weight, ovt, visitor, dist_map=dist, infinity=999999)
        logging.info(f"search took {time.time() - starttime} seconds")
        logging.debug(f"ovt has degree {ovt.out_degree()}, dvt has degree {dvt.out_degree()}")
        p = pred[dvt]
        print(f"Shortest distance: {dist[dvt]}")
        while not p == ovt:
            print(p)
            p = pred[p]
    logging.debug(f"Edges: {graph.num_edges()}")

    if args.draw_graph:
        graph_draw(graph, pos=graph.vp.coord.copy('vector<double>'), nodesfirst=False, ink_scale=0.5,
                       output_size=(2048, 2048), output='graph.png')
    sys.exit()
