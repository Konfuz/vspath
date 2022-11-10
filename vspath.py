#!/usr/bin/env python3
"""vspath find shortest route between two points."""
import argparse
import sys
import re
import logging
import pickle
import math
import time
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

    def generate_route(self, org, dst, max_time):
        """Return shortest route from a point to the other."""
        to_beat = manhattan(org, dst)
        best_route = [org, dst]
        counter = 0

        def investigate_route(route, dst):
            """Return shortest route to dst."""
            nonlocal to_beat, best_route, counter
            # Discard early if a better route has been found while waiting for this to recurse
            if route.dist > to_beat:
                return
            runtime = time.thread_time()
            if runtime > max_time:
                return
            routes = []
            tl = route.current
            counter += 1

            #logging.debug(f"checking {len(tl.neighbors)} neighbors")
            for dist, neighbor in tl.neighbors:
                dist += route.dist
                if dist >= neighbor.current:
                    continue
                fdist = dist + manhattan(neighbor.destination, dst)

                if fdist < to_beat:
                    to_beat = fdist
                    neighbor.current = dist
                    best_route = route.route + [neighbor, dst]
                    logging.debug(f"best distance {to_beat} with {len(best_route)} waypoints. Took {runtime:.2f}s")
                routes.append(Route(dist, fdist, neighbor, route.route + [neighbor]))
            # sort to check most promising routes first
            routes = sorted(routes, key=lambda route: route.fdist)
            for route in routes:
                investigate_route(route, dst)

        routes = []
        for tl in tls:
            dist = manhattan(org, tl.origin)
            if dist < MAX_DIST and dist < manhattan(org, tl.destination):
                fdist = manhattan(tl.destination, dst)
                routes.append(Route(dist, fdist, tl, [org, tl]))
        # sort to check most promising routes first
        routes = sorted(routes, key=lambda route: route.fdist)
        progress = 100 / len(routes)
        i = 0
        for route in routes:
            logging.info(f"{progress * i}% Progress")
            investigate_route(route, dst)
            i += 1

        if time.thread_time() > max_time:
            print("Timelimit exceeded, Route may not be optimal!")
        else:
            print("Route is optimal!")
        print(f"Did {counter} Investigations")
        return best_route

def _populate_neighbors(dst):
    """Attach a list of neighbors to each TL."""
    for tl in tls:
        tl.neighbors = []
        for other_tl in tls:
            dist = manhattan(tl.destination, other_tl.origin)
            if dist <= 0:
                logging.debug(f"{tl.destination} to {other_tl.origin} is {dist}")
                continue
            if dist < manhattan(other_tl.destination, tl.origin):
                tl.neighbors.append((dist, other_tl))
        tl.neighbors = sorted(tl.neighbors, key=lambda neighbor: manhattan(neighbor[1].destination, dst))

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
    try:
        with open('translocators.db', 'r+b') as db:
            tls = pickle.load(db)
    except FileNotFoundError:
        logging.info('No existing translocator-db found. Ignoring.')
    try:
        with open('landmarks.db', 'r+b') as db:
            landmarks = pickle.load(db)
    except FileNotFoundError:
        logging.info('No existing landmark-db found. Ignoring.')
        try:
            with open('traders.db', 'r+b') as db:
                traders = pickle.load(db)
        except FileNotFoundError:
            logging.info('No existing trader-db found. Ignoring.')

    solver = PathSolver()

    def dbdump():
        with open('translocators.db', 'w+b') as db:
            pickle.dump(importer.translocators, db)
        with open('landmarks.db', 'w+b') as db:
            pickle.dump(importer.landmarks, db)
        with open('traders.db', 'w+b') as db:
            pickle.dump(importer.traders, db)

    # import new data
    if args.dbfile:
        importer = get_importer(args.dbfile, tls, landmarks, traders)
        importer.do_import()
        dbdump()

    if args.clean:
        tls = []
        landmarks = []
        traders = []
        dbdump()

    if args.listlandmarks:
        for landmark in sorted(landmarks):
            print(landmark)


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


    origin = goal = None

    if args.origin:
        origin = parse_coord(args.origin)
    if args.goal:
        goal = parse_coord(args.goal)
    if origin and goal:
        _populate_neighbors(goal)
        route = solver.generate_route(origin, goal, args.timelimit)
        solver.describe_route(route)
    sys.exit()
