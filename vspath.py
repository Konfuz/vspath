#!/usr/bin/env python3
"""vspath find shortest route between two points."""
import argparse
import sys
import re
import logging
import pickle
import math
import time
from importers import get_importer
from datastructures import Translocator, Route

logging.basicConfig(level=logging.DEBUG)
MAX_DIST = 8000  # Maximum allowed distance of the next TL in a chain
MAX_TIME = 600  # Maximum time allowed to find a route in seconds
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

        def tdist(a, b):
            origin = a
            if type(a) == Translocator:
                origin = a.destination
            destination = b
            if type(b) == Translocator:
                destination = b.origin
            return math.dist(origin, destination)
        while route:
            dist = tdist(old_wp, next_wp)
            total_dist += dist
            hops += 1
            print(f"Move {int(dist)}m to {next_wp.origin} and Teleport")
            old_wp = next_wp
            next_wp = route.pop(0)

        dist = tdist(old_wp, next_wp)
        total_dist += dist
        print(f"Move {int(dist)}m to your destination {next_wp}.")
        print(f"The route is {(total_dist / 1000):.2f}km long and uses {hops} hops.")

    def generate_route(self, org, dst, max_time):
        """Return shortest route from a point to the other."""
        to_beat = math.dist(org, dst)
        best_route = [org, dst]

        def investigate_route(route, dst):
            """Return shortest route to dst."""
            nonlocal to_beat, best_route
            # Discard early if a better route has been found while waiting for this to recurse
            if route.dist > to_beat:
                return
            runtime = time.thread_time()
            if runtime > max_time:
                return
            routes = []
            tl = route.current

            #logging.debug(f"checking {len(tl.neighbors)} neighbors")
            for dist, neighbor in tl.neighbors:
                dist += route.dist
                if dist >= to_beat:
                    continue
                fdist = dist + math.dist(neighbor.destination, dst)

                if fdist < to_beat:
                    to_beat = fdist
                    best_route = route.route + [neighbor, dst]
                    logging.debug(f"best distance {to_beat} with {len(best_route)} waypoints. Took {runtime:.2f}s")
                routes.append(Route(dist, fdist, neighbor, route.route + [neighbor]))
            # sort to check most promising routes first
            routes = sorted(routes, key=lambda route: route.fdist)
            for route in routes:
                investigate_route(route, dst)

        routes = []
        for tl in tls:
            dist = math.dist(org, tl.origin)
            if dist < MAX_DIST:
                fdist = math.dist(tl.destination, dst)
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
        return best_route

def _populate_neighbors():
    """Attach a list of neighbors to each TL."""
    for tl in tls:
        tl.neighbors = []
        for other_tl in tls:
            dist = math.dist(tl.destination, other_tl.origin)
            if dist <= 0:
                logging.debug(f"{tl.destination} to {other_tl.origin} is {dist}")
                continue
            if dist < MAX_DIST:
                tl.neighbors.append((dist, other_tl))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-i', '--import',
                        metavar='dbfile',
                        dest='dbfile',
                        help='file to import')
    parser.add_argument('-t', '--timelimit',
                        metavar='seconds',
                        type=int,
                        default=1,
                        help='seconds after which the search gets aborted with an approximate-result')
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

    # import new data
    if args.dbfile:
        importer = get_importer(args.dbfile, tls, landmarks, traders)
        importer.do_import()
        with open('translocators.db', 'w+b') as db:
            pickle.dump(importer.translocators, db)
        with open('landmarks.db', 'w+b') as db:
            pickle.dump(importer.landmarks, db)
        with open('traders.db', 'w+b') as db:
            pickle.dump(importer.traders, db)

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
        _populate_neighbors()
        route = solver.generate_route(origin, goal, args.timelimit)
        solver.describe_route(route)
    sys.exit()
