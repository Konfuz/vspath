#!/usr/bin/env python3
"""vspath find shortest route between two points."""
import argparse
import sys
import re
import logging
import pickle
import math
from importers import get_importer

logging.basicConfig(level=logging.ERROR)


class Route():

    def __init__(self, dist, current, route=[]):
        self.dist = dist
        self.current = current
        self.route = route


class PathSolver():
    tls = {}  # dict of Translocators {from: to}
    landmarks = {}
    traders = {}

    def __init__(self):
        try:
            with open('translocators.db', 'r+b') as db:
                self.tls = pickle.load(db)
        except FileNotFoundError:
            logging.info('No existing translocator-db found. Ignoring.')
        try:
            with open('landmarks.db', 'r+b') as db:
                self.landmarks = pickle.load(db)
        except FileNotFoundError:
            logging.info('No existing landmark-db found. Ignoring.')
            try:
                with open('traders.db', 'r+b') as db:
                    self.traders = pickle.load(db)
            except FileNotFoundError:
                logging.info('No existing trader-db found. Ignoring.')

    def describe_route(self, route):
        """Generate written description of a path."""
        hops = 0
        total_dist = 0
        old_wp = route.pop(0)
        print(f"You are starting at {old_wp}")
        next_wp = route.pop(0)
        while route:
            try:
                dist = math.dist(self.tls[old_wp], next_wp)
            except KeyError:
                dist = math.dist(old_wp, next_wp)
            total_dist += dist
            hops += 1
            print(f"Move {int(dist)}m to {next_wp} and Teleport")
            old_wp = next_wp
            next_wp = route.pop(0)
        try:
            dist = math.dist(self.tls[old_wp], next_wp)
        except KeyError:
            dist = math.dist(old_wp, next_wp)
        total_dist += dist
        print(f"Move {int(dist)}m to your destination {next_wp}.")
        print(f"The route is {(total_dist / 1000):.2f}km long and uses {hops} hops.")

    def generate_route(self, org, dst):
        """Return shortes route from a point to the other."""
        to_beat = math.dist(org, dst)
        best_route = [org, dst]
        routes = []

        for tl in self.tls:
            dist = math.dist(org, tl)
            if dist < to_beat:
                routes.append(Route(dist, tl, [org]))
        while routes:
            surviving_routes = []
            for route in routes:
                dist = math.dist(route.current, dst) + route.dist
                # Check if this path is the new best
                if dist < to_beat:
                    to_beat = dist
                    logging.info(f"new best is {to_beat}")
                    best_route = route.route + [dst]
                # Expand pathfinding
                for tl in self.tls:
                    if tl == route.current:
                        break
                    dist = math.dist(route.current, tl) + route.dist
                    if dist < to_beat:
                        surviving_routes.append(Route(dist, self.tls[tl], route.route + [tl]))
            routes = surviving_routes
            logging.debug(f"We got {len(routes)} to check")
        return best_route


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-i', '--import',
                        metavar='dbfile',
                        dest='dbfile',
                        help='file to import')

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

    solver = PathSolver()

    # import new data
    if args.dbfile:
        translocators = solver.tls
        landmarks = solver.landmarks
        traders = solver.traders
        importer = get_importer(args.dbfile, translocators, landmarks, traders)
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
            return solver.landmarks[coord_str]
        except KeyError:
            logging.error(f"Unknown coordinate: {coord_str}")
        return None

    origin = goal = None

    if args.origin:
        origin = parse_coord(args.origin)
    if args.goal:
        goal = parse_coord(args.goal)
    if origin and goal:
        route = solver.generate_route(origin, goal)
        solver.describe_route(route)
    sys.exit()
