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
from lib.pathfinder.importers import do_import
from lib.pathfinder.util import cardinal_dir, manhattan, parse_coord
from lib.pathfinder.config import config
from lib.pathfinder.ui import Terminal, Prompt
from lib.pathfinder.commander import MasterCommander
from textual.app import App
from textual.widgets import Header

logging.basicConfig(level=logging.DEBUG)

MAX_DIST = config.link_dist_tl


def link_vertex(g, u, maxdist=MAX_DIST):
    for v in g.iter_vertices():
        dist = manhattan(g.vp.coord[u], g.vp.coord[v])

        if dist < maxdist and v != u:
            #logging.debug(f"{u}->{v} {dist}")
            edg = g.add_edge(u, v)
            g.ep.weight[edg] = dist
    return

class VSPath(App):
    CSS_PATH='config/ui.css'
    def __init__(self):
        self.commander = MasterCommander()
        self.graph = None
        super().__init__()

    def compose(self):
        """Compose app-widgets"""
        yield Header(id='header', show_clock=True)
        yield Terminal(id='textlog')
        yield Prompt(id='prompt', classes='box')

    def on_prompt_submitted(self, message):
        self.query_one(Terminal).write(message.user_input)
        self.commander.process(message.user_input)

    def action_import_file(self, filename):
        self.graph = do_import(filename, self.graph)

    def action_pathfind(self, origin, destination):
        pass


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
        graph = do_import()

    if config.clean:
        # override Graph file with empty Graph
        # TODO: Need to add all property maps, generator for new Graph required for importer and this
        gt.Graph.save(config.data_file, Graph(directed=True))

    if config.listlandmarks:
        logging.warning("Landmark listing not a feature at the moment")
        pass  #TODO: Landmarks currently no thing

    # Check for an actual pathfinding task and conduct it
    origin = destination = None
    if config.origin:
        origin = parse_coord(config.origin, graph)
    if config.goal:
        destination = parse_coord(config.goal, graph)
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

        # add the trivial connection (walking from origin to destination)
        edg = graph.add_edge(ovt, dvt)
        graph.ep.weight[edg] = manhattan(origin, destination)

        coord = graph.vp.coord
        weight = graph.ep.weight
        e_is_tl = graph.ep.is_tl

        # Link the temporary vertices for start and endpoint
        maxdist = manhattan(coord[ovt], coord[dvt])
        logging.info(f"Trivial distance would be {maxdist} to walk")
        link_vertex(graph, ovt, maxdist)
        link_vertex(graph, dvt, maxdist)
        starttime = time.time()
        vertex_list, edge_list = shortest_path(graph, ovt, dvt, weight)
        logging.info(f"search took {time.time() - starttime} seconds")

        narrate_path(graph, vertex_list, edge_list)
    else:
        app = VSPath()
        app.run()


    if config.drawgraph:
        graph_draw(graph, pos=graph.vp.coord.copy('vector<double>'), nodesfirst=False, ink_scale=0.5,
                       output_size=(2048, 2048), output='graph.png')
    sys.exit()
