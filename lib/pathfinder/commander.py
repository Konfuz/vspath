import sys
import logging
import graph_tool
import time
from lib.pathfinder.util import manhattan, cardinal_dir
from lib.pathfinder.config import config


class MasterCommander:

    def __init__(self):
        self.commands = {
            'quit': self.do_quit
        }

    def process(self, user_input):
        input = user_input.lower().split()
        try:
            self.commands[input[0]](input[1:])
        except KeyError:
            logging.warning(f"Command {input[0]} is not known.")

    def do_quit(self, _):
        sys.exit(0)

class GraphCommander:

    def __init__(self, graph):
        self.graph = graph

    def link_vertex(self, u, maxdist=config.link_dist_tl):
        for v in self.graph.iter_vertices():
            dist = manhattan(self.graph.vp.coord[u], self.graph.vp.coord[v])

            if dist < maxdist and v != u:
                # logging.debug(f"{u}->{v} {dist}")
                edg = self.graph.add_edge(u, v)
                self.graph.ep.weight[edg] = dist
        return

    def find_path(self, origin, destination):

        if not self.graph:
            logging.error("No Graph-Data available. Try importing some data first before searching in it")

        # obtain origin vertex
        ovt = graph_tool.util.find_vertex(self.graph, self.graph.vp.coord, origin)
        if ovt:
            assert(len(ovt)==1)
            ovt = ovt[0]
            logging.debug(f"found origin to be preexisting as vertex {ovt}")
        else:
            ovt = self.graph.add_vertex()
            self.graph.vp.coord[ovt] = origin

        # obtain destination vertex
        dvt = graph_tool.util.find_vertex(self.graph, self.graph.vp.coord, destination)
        if dvt:
            assert (len(dvt) == 1)
            dvt = dvt[0]
            logging.debug(f"found destination to be preexisting as vertex {dvt}")
        else:
            dvt = self.graph.add_vertex()
            self.graph.vp.coord[dvt] = destination

        # add the trivial connection (walking from origin to destination)
        edg = self.graph.add_edge(ovt, dvt)
        self.graph.ep.weight[edg] = manhattan(origin, destination)

        coord = self.graph.vp.coord
        weight = self.graph.ep.weight
        e_is_tl = self.graph.ep.is_tl

        # Link the temporary vertices for start and endpoint
        maxdist = manhattan(coord[ovt], coord[dvt])
        logging.info(f"Trivial distance would be {maxdist} to walk")
        self.link_vertex(ovt, maxdist)
        self.link_vertex(dvt, maxdist)
        starttime = time.time()
        vertex_list, edge_list = graph_tool.topology.shortest_path(self.graph, ovt, dvt, weight)
        logging.info(f"search took {time.time() - starttime} seconds")
        return vertex_list, edge_list

    from lib.pathfinder.util import cardinal_dir

    def narrate_path(self, vertex_list, edge_list):
        """Give textual description of a path

        :param vertex_list: ordered list of vertices to visit
        :param edge_list: ordered list of edges to traverse
        """
        coord = self.graph.vp.coord
        weight = self.graph.ep.weight
        e_is_tl = self.graph.ep.is_tl
        vert = tuple(coord[vertex_list.pop(0)])
        dist = 0
        step = 0
        num_tl = 0
        route = f"\n{step}. You start at {vert}.\n"
        while vertex_list:
            step += 1
            edg = edge_list.pop(0)
            oldvert = vert
            vert = tuple(coord[vertex_list.pop(0)])
            if e_is_tl[edg]:
                route += f"    translocate\n"
                num_tl += 1
            else:
                dist += weight[edg]
                direction = cardinal_dir(oldvert, vert)
                route += f"{step}. Move {direction} {weight[edg]}m from {oldvert} to {vert}.\n"
        route += f"\nYou arrive at your destination after {(dist / 1000):.2f}km of travel using {num_tl} TL!"
        return route
