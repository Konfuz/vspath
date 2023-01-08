
import logging
import re
import graph_tool as gt
from lib.pathfinder.util import manhattan, get_trader_type
from lib.pathfinder.config import config


from lib.pathfinder.datastructures import Node
TL_COST = config.tl_cost  # It *is* some effort to walk down a ladder and wait for the TL
TL_LINK_DIST = config.link_dist_tl
LANDMARK_LINK_DIST = config.link_dist_landmark
TRADER_LINK_DIST = config.link_dist_trader
GLOBAL_OFFSET = tuple(config.global_offset)


class AbstractImporter():
    translocators = set()
    landmarks = {}
    traders = {}
    filepath = ''

    def __init__(self, filepath, graph=None, *args):
        self.filepath = filepath
        self.graph = graph
        if not graph:
            self.graph = gt.Graph(directed=False)
            self.graph.vp['is_tl'] = self.graph.new_vertex_property('bool', val=False)
            self.graph.vp['coord'] = self.graph.new_vertex_property('vector<int>')
            self.graph.vp['elevation'] = self.graph.new_vertex_property('int', val=0)
            self.graph.ep['weight'] = self.graph.new_edge_property('int', val=0)
            self.graph.ep['is_tl'] = self.graph.new_edge_property('bool', val=False)
            self.graph.vp['is_trader'] = self.graph.new_vertex_property('bool', val=False)
            self.graph.vp['trader_name'] = self.graph.new_vertex_property('string')
            self.graph.vp['trader_type'] = self.graph.new_vertex_property('int', val=-1)
            self.graph.vp['is_landmark'] = self.graph.new_vertex_property('bool', val=False)
            self.graph.vp['landmark_name'] = self.graph.new_vertex_property('string')
            self.graph.vp['landmark_type'] = self.graph.new_vertex_property('int')

        print(self.graph)
    def do_import(self):
        raise NotImplementedError

    def add_tl(self, origin, destination):
        """Create vertices for a given translocator-pair"""
        if origin in self.graph.vp.coord:
            logging.debug(f"TL {origin} to {destination} already known")
            return
        org_vt = self.graph.add_vertex()
        dst_vt = self.graph.add_vertex()
        oe = self.graph.add_edge(org_vt, dst_vt)
        ie = self.graph.add_edge(dst_vt, org_vt)
        ox, oy, oz = origin
        dx, dy, dz = destination
        self.graph.vp.coord[org_vt] = (ox, oz)
        self.graph.vp.coord[dst_vt] = (dx, dz)
        self.graph.vp.elevation[org_vt] = oy
        self.graph.vp.elevation[dst_vt] = dy
        self.graph.ep.weight[oe] = TL_COST
        self.graph.ep.weight[ie] = TL_COST
        self.graph.vp.is_tl[org_vt] = True
        self.graph.vp.is_tl[dst_vt] = True
        self.graph.ep.is_tl[oe] = True
        self.graph.ep.is_tl[ie] = True

    def add_trader(self, pos, name, description):
        """Create Trader Vertex in the NavGraph"""
        if pos in self.graph.vp.coord.get_2d_array([0, 1])[:, 1:]:
            logging.debug(f"Adding Trader failed, already a node at {pos}")
            return
        vt = self.graph.add_vertex()
        self.graph.vp.is_trader[vt] = True
        self.graph.vp.coord[vt] = (pos[0], pos[2])
        self.graph.vp.elevation[vt] = pos[1]
        self.graph.vp.trader_name[vt] = name
        self.graph.vp.trader_type[vt] = get_trader_type(description)

    def add_landmark(self, pos, name, landmark_type=None):
        if pos in self.graph.vp.coord.get_2d_array([0, 1])[:, 1:]:
                logging.debug(f"Adding Landmark failed, a node already exists at {pos}")
                return
        vt = self.graph.add_vertex()
        self.graph.vp.is_landmark[vt] = True
        self.graph.vp.coord[vt] = (pos[0], pos[2])
        self.graph.vp.elevation[vt] = pos[1]
        self.graph.vp.landmark_name[vt] = name
        self.graph.vp.landmark_type[vt] = landmark_type

    def make_connections(self):
        """Create Edges in the NavGraph

        TL are Linked to all other TL closer than *link_dist_tl*
        Traders are Linked to all TL closer than *link_dist_trader*
        """

        trader_view = gt.GraphView(self.graph, vfilt=self.graph.vp.is_trader)
        tl_view = gt.GraphView(self.graph, vfilt=self.graph.vp.is_tl)
        landmark_view = gt.GraphView(self.graph, vfilt=self.graph.vp.is_landmark)
        num = 0

        def link(view1, view2, maxdist):
            nonlocal num
            for vt1, coord1 in view1.iter_vertices([self.graph.vp.coord]):
                for vt2, coord2 in view2.iter_vertices([self.graph.vp.coord]):
                    if self.graph.edge(vt1, vt2):
                        continue  # no need to link what is already there
                    dist = manhattan(coord1, coord2)
                    if 0 < dist < maxdist:
                        num += 1
                        e = self.graph.add_edge(vt1, vt2)
                        self.graph.ep.weight[e] = dist

        # Link Translocators to each other via walk
        link(tl_view, tl_view, TL_LINK_DIST)

        # Link Traders to Translocators
        link(trader_view, tl_view, TRADER_LINK_DIST)

        # Link Landmarks to Translocators
        link(landmark_view, tl_view, LANDMARK_LINK_DIST)

        logging.info(f"added {num} Edges")

class CampaignCartographerImporter(AbstractImporter):
    """Manage Import from an Campaign-Cartographer export .json"""
    def do_import(self):
        import json
        with open(self.filepath) as dbfile:
            db = json.load(dbfile)
            for item in db['Waypoints']:
                position = (
                    int(item["Position"]['X']) - GLOBAL_OFFSET[0],
                    int(item['Position']['Y']),
                    int(item['Position']['Z']) - GLOBAL_OFFSET[1])
                if item['ServerIcon'] == 'trader':
                    title = item['Title'].strip('Local Goods - ')
                    match = re.match("(\w+) the (\w+)", title)
                    if match:
                        name, description = match.groups()
                        self.add_trader(position, name, description)
                elif item['ServerIcon'] == 'spiral':
                    match = re.match('Translocator to \((-*\d+), (-*\d+), (-*\d+)\)', item["Title"])
                    if match:
                        dest = [int(_) for _ in match.groups()]
                        self.add_tl(position, dest)
                elif item['ServerIcon'] == 'home':
                    self.add_landmark(position, item['Title'].lower(), landmark_type=1)
                elif item['ServerIcon'] == 'star1':
                    self.add_landmark(position, item['Title'].lower(), landmark_type=2)

class ProspectorImporter(AbstractImporter):
    def do_impport(self):
        import json
        with open(self.filepath) as dbfile:
            db = json.load(dbfile)
        for item in db:
            position = (item['X'], item['Z'])
            _, _, ores = item['Message'].partition("Relative densities:")
            ores = ores.split('\n')


class GeojsonImporter(AbstractImporter):
    """Manage Import from an webmap geojson db"""
    # TODO: Reimplement for use by graphtool
    def do_import(self):
        import json
        with open(self.filepath) as dbfile:
            db = json.load(dbfile)
            for item in db['features']:
                try:
                    origin, dest = item['geometry']['coordinates']
                except KeyError:
                    continue
                origin = (int(origin[0]), -int(origin[1]))
                dest = (int(dest[0]), -int(dest[1]))
                self.add_tl(origin, dest)
                logging.debug(f"adding {origin}, {dest}")


class TSVImporter(AbstractImporter):

    def do_import(self):

        raise DeprecationWarning  # This is no longer supported
        import csv

        def to_2d_coord(field):
            dst = re.split('X|, Y|, Z', field)
            dst = (int(dst[1]), int(dst[3]))
            return dst

        with open(self.filepath, newline='') as dbfile:
            reader = csv.DictReader(dbfile, dialect='excel-tab')
            for row in reader:
                if row['\ufeffName'] == 'Translocator':

                    org = to_2d_coord(row['Location'])

                    if not row['Destination'] or row['Destination'] == '---':
                        logging.info(
                            f"TL at {org} " +
                            f"Missing Destination. {row['Description']}")
                        continue
                    self.translocators.add(Node(org, to_2d_coord(row['Destination'])))
                elif row['\ufeffName'] == 'Sign':
                    try:
                        landmark = re.split('<AM:\w+>', row['Description'])[1][1:]
                    except IndexError:
                        logging.warning(f"Malformed <AM:XXX>: {row['Description']}")
                        continue
                    self.landmarks[landmark] = to_2d_coord(row['Location'])
                elif row['\ufeffName'] == 'Trader':
                    try:
                        name, kind = re.split(' the ', row['Description'])
                    except ValueError:
                        logging.warning(f"Trader could not be parsed: {row['Description']}")
                        continue
                    coord = to_2d_coord(row['Location'])
                    try:
                        self.traders[kind].append(coord)
                    except KeyError:
                        self.traders[kind] = [coord]
        return


def get_importer(filepath, graph):
    if filepath.endswith('.tsv'):
        return TSVImporter(filepath, graph)
    elif filepath.endswith('.geojson'):
        return GeojsonImporter(filepath, graph)
    elif filepath.endswith('.json'):
        return CampaignCartographerImporter(filepath, graph)
    logging.error(f'Could not find a valid importer for {filepath}')

