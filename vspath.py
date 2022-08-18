#!/usr/bin/env python3
"""vspath find shortest route between two points."""
import argparse
import csv
import sys
import re
import logging
import pickle
import math
logging.basicConfig(level=logging.ERROR)


class Route():

    def __init__(self, dist, current, route=[]):
        self.dist = dist
        self.current = current
        self.route = route


class PathSolver():

    def __init__(self, translocators=None):
        self.tls = translocators

    def describe_route(self, route):
        #route = reversed(route)
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
        """Generate routing instruction from a point to the other."""
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

def import_translocators(filename):
    """Import new Translocators and save them."""
    translocators = {}
    with open(filename, newline='') as dbfile:
        reader = csv.DictReader(dbfile, dialect='excel-tab')
        for row in reader:
            if row['\ufeffName'] == 'Translocator':

                org = re.split('X|, Y|, Z', row['Location'])
                org = (int(org[1]), int(org[3]))
                if not row['Destination'] or row['Destination'] == '---':
                    logging.info(
                        f"TL at {org} " +
                        f"Missing Destination. {row['Description']}")
                    continue
                dst = re.split('X|, Y|, Z', row['Destination'])
                dst = (int(dst[1]), int(dst[3]))
                translocators[org] = dst
    return translocators

def import_landmarks(filename):
    """Import new Locations and save them."""
    landmarks = {}
    with open(filename, newline='') as dbfile:
        reader = csv.DictReader(dbfile, dialect='excel-tab')
        for row in reader:
            if row['\ufeffName'] == 'Sign':
                try:
                    landmark = re.split('<AM:\w+>', row['Description'])[1][1:]
                except IndexError:
                    logging.warning(f"Malformed <AM:XXX>: {row['Description']}")
                    continue
                dst = re.split('X|, Y|, Z', row['Location'])
                dst = (int(dst[1]), int(dst[3]))
                landmarks[landmark] = dst
    return landmarks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-d', '--dbfile',
                        help='csv with translocator locations or landmarks')

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

    translocators = {}
    try:
        with open('translocators.db', 'r+b') as db:
            translocators = pickle.load(db)
    except FileNotFoundError:
        logging.debug('No existing translocator-db found. Ignoring.')
    landmarks = {}
    try:
        with open('landmarks.db', 'r+b') as db:
            landmarks = pickle.load(db)
    except FileNotFoundError:
        logging.debug('No existing landmark-db found. Ignoring.')

    # import new data
    if args.dbfile:
        new_translocators = import_translocators(args.dbfile)
        for key in new_translocators:
            translocators[key] = new_translocators[key]
        with open('translocators.db', 'w+b') as db:
            pickle.dump(translocators, db)
        new_landmarks = import_landmarks(args.dbfile)
        for key in new_landmarks:
            landmarks[key] = new_landmarks[key]
        with open('landmarks.db', 'w+b') as db:
            pickle.dump(landmarks, db)

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
        solver = PathSolver(translocators)
        route = solver.generate_route(origin, goal)
        solver.describe_route(route)
    sys.exit()
