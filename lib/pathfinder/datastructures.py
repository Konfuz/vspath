from lib.pathfinder.util import manhattan
from math import inf
class Route():

    def __init__(self, dist, fdist, current, route=[]):
        self.dist = dist
        self.current = current
        self.route = route
        self.fdist = fdist


class Node():
    neighbors = []  # List of (distance_to, neighbor)
    origin = ()
    destination = ()
    nodetype = "None"
    dist = 0
    current = inf  # Storing current known best dist to this node during a search

    def __init__(self, origin, destination):
        self.origin = origin
        self.destination = destination
        self.neighbors = []
        self.dist = manhattan(origin, destination)

    def __eq__(self, other):
        return self.origin == other.origin

    def __hash__(self):
        return self.origin.__hash__()
