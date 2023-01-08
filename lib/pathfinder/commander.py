import sys
import logging
import graph_tool
import time
import re
from lib.pathfinder.util import manhattan, cardinal_dir, trader_enum, inverse_trader_enum
from lib.pathfinder.importers import get_importer
from lib.pathfinder.config import config
from textual.message_pump import MessagePump
from graph_tool import GraphView
from graph_tool.util import find_vertex
from graph_tool.topology import shortest_path, shortest_distance


class NoGraphDataError(Exception):
    pass


class MasterCommander(MessagePump):

    def __init__(self, parent, graph=None):
        super().__init__(parent)
        self.graph_commander = GraphCommander(graph)
        self.commands = {
            'quit': self.do_quit,
            'debug': self.do_debug,
            'route': self.do_route,
            'import': self.do_import,
            'closest': self.do_find_closest,
            'stats': self.do_stats,
            'help': self.do_help
        }


    def process(self, user_input):
        input = user_input.lower().split()
        try:
            self.commands[input[0]](input[1:])
        except KeyError:
            logging.warning(f"Command {input[0]} is not known.")

    def do_quit(self, _):
        sys.exit(0)

    def do_debug(self, args):
        if not args:
            return False
        if args[0] == 'log':
            self.do_log(args[1:])

    def do_log(self, args):
        call ={
            'debug': logging.debug,
            'info': logging.info,
            'warning': logging.warning,
            'error': logging.error,
            'critical': logging.critical
        }

        try:
            message = ' '.join(arg for arg in args[1:])
        except IndexError:
            message = "Debug message"
        try:
            call[args[0]](message)
        except (KeyError, IndexError):
            logging.debug(message)

    def do_route(self, args):
        if not len(args) == 2:
            logging.info("usage: route  <from> <to>")
            return
        if not self.graph_commander.graph:
            logging.error("Searching requires a Graph to be loaded")
            return
        origin = self.graph_commander.parse_coord(args.pop(0))
        destination = self.graph_commander.parse_coord(args.pop(0))
        if not origin or not destination:
            logging.error("Aborting find route.")
            return
        vertex_list, edge_list = self.graph_commander.find_path(origin, destination)
        description = self.graph_commander.narrate_path(vertex_list, edge_list)
        logging.info(description)

    def do_import(self, args):
        if not args:
            logging.info("usage: import <filepath>")
            return
        filename = ' '.join(args)
        logging.info("importing may take some time...")
        self.graph_commander.do_import(filename)
        logging.info("import done.")

    def do_find_closest(self, args):
        """Usage: closest \[tradetype] \[distance] <pos>

        List traders of given type closer than distance
        """
        if not args:
            logging.info(self.do_find_closest.__doc__)
            return
        pos = self.graph_commander.parse_coord(args.pop(-1))
        trader_type = None
        dist = 500
        if args:
            for arg in args:
                if arg in inverse_trader_enum:
                    trader_type = inverse_trader_enum[arg]
                    continue
                try:
                    dist = int(arg)
                except ValueError:
                    logging.warning(f"Argument {arg} not understood")
        closest = self.graph_commander.closest_traders(pos, trader_type=trader_type, maxdist=dist)
        for trader_type, trader_name, coord, dist in closest:
            logging.info(f"{trader_type} {trader_name} {coord} {dist}m")

    def do_stats(self, args):
        """Print various statistics"""
        graph = self.graph_commander.graph
        info = f"""Graph currently has
        {graph.num_vertices()} Nodes total
        {graph.num_edges()} Edges total
        {GraphView(graph,vfilt=graph.vp.is_tl).num_vertices()} Translocators
        {GraphView(graph,vfilt=graph.vp.is_trader).num_vertices()} Traders        
        """
        logging.info(info)

    def do_help(self, args):
        """Usage: help [command]"""
        if args:
            if args[0] in self.commands:
                logging.info(self.commands[args[0]].__doc__)
                return
        info = "Possible commands: "
        for key in sorted(self.commands):
            info += key + ' '
        logging.info(info)


class GraphCommander:

    def __init__(self, graph):
        # TODO: Generate Graph on none
        self.graph = graph

    def link_vertex(self, u, maxdist=config.link_dist_tl, graph=None):
        """Link given vertext to all Nodes in range

        Considers only TL-Nodes by default
        """

        if not graph:
            graph = graph_tool.GraphView(self.graph, vfilt=self.graph.vp.is_tl)
        u_pos = self.graph.vp.coord[u]
        for vt, vt_pos in graph.iter_vertices([self.graph.vp.coord]):
            dist = manhattan(u_pos, vt_pos)

            if dist < maxdist and vt != u:
                # logging.debug(f"{u}->{v} {dist}")
                edg = self.graph.add_edge(u, vt)
                self.graph.ep.weight[edg] = dist
        return

    def find_or_add(self, position):
        vt = graph_tool.util.find_vertex(self.graph, self.graph.vp.coord, position)
        if vt:
            if len(vt) > 1:
                logging.warning(f"Found {len(vt)} vertices for position {tuple(position)}!")
            vt = vt[0]
            logging.debug(f"found {position} to be preexisting as vertex {vt}")
        else:
            vt = self.graph.add_vertex()
            self.graph.vp.coord[vt] = position
        return vt

    def find_path(self, origin, destination):

        if not self.graph:
            logging.error("No Graph-Data available. Try importing some data first before searching in it")
            return

        # obtain origin vertex
        ovt = self.find_or_add(origin)

        # obtain destination vertex
        dvt = self.find_or_add(destination)

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
        vertex_list, edge_list = shortest_path(self.graph, ovt, dvt, weight)
        logging.info(f"search took {time.time() - starttime} seconds")
        return vertex_list, edge_list

    def closest_traders(self, origin, trader_type=None, maxdist=500):
        vt = self.find_or_add(origin)
        if trader_type:
            trader_view = GraphView(self.graph, vfilt=lambda v: self.graph.vp.trader_type[v] == trader_type)
        else:
            trader_view = GraphView(self.graph, vfilt=self.graph.vp.is_trader)
        self.link_vertex(vt, min(maxdist, config.link_dist_tl))
        self.link_vertex(vt, maxdist, trader_view)
        weights = self.graph.ep.weight
        dist_map = shortest_distance(self.graph, vt, weights=weights, max_dist=maxdist)
        closest = []
        for vt, dist in trader_view.iter_vertices([dist_map]):
            if dist < maxdist:
                trader_type = trader_enum[self.graph.vp.trader_type[vt]]
                trader_name = self.graph.vp.trader_name[vt]
                coord = tuple(self.graph.vp.coord[vt])
                closest.append((trader_type, trader_name, coord, dist))
        return sorted(closest, key=lambda x: x[-1])


    def do_import(self, filename, save=True):
        importer = get_importer(filename, self.graph)
        if not importer:
            return
        existing = importer.graph.num_vertices()
        try:
            importer.do_import()
        except IOError as e:
            logging.error(str(e))
            return
        importer.make_connections()
        new = importer.graph.num_vertices()
        logging.info(f"Added {new - existing} Nodes for a total of {new}.")
        if save:
            importer.graph.save(config.data_file)
        self.graph = importer.graph

    def parse_coord(self, coord_str):
        graph = self.graph
        try:
            x, y = re.split(',', coord_str)
            x = int(x)
            y = int(y)
            return (x, y)
        except ValueError:
            logging.debug("coordinate could not be parsed as x,y")

        view = graph_tool.GraphView(graph, vfilt=graph.vp.is_landmark)
        result = find_vertex(view, graph.vp.landmark_name, coord_str)
        if not result:
            logging.error(f'could not find a location for {coord_str}')
            return None
        if len(result) > 1:
            logging.warning(f'found {len(result)} possible locations for {coord_str} choosing the first one')
        return graph.vp.coord[result[0]]

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
