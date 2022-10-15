
class Route():

    def __init__(self, dist, fdist, current, route=[]):
        self.dist = dist
        self.current = current
        self.route = route
        self.fdist = fdist


class Translocator():
    neighbors = []  # List of (distance_to, neighbor)
    origin = ()
    destination = ()

    def __init__(self, origin, destination):
        self.origin = origin
        self.destination = destination
        self.neighbors = []

    def __eq__(self, other):
        return self.origin == other.origin

    def __hash__(self):
        return self.origin.__hash__()
