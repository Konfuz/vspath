
import logging
import re
import graph_tool as gt
import graph_tool.util
from lib.pathfinder.util import manhattan


from lib.pathfinder.datastructures import Node
TL_COST = 100  # It *is* some effort to walk down a ladder and wait for the TL
LINK_DIST = 10000


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
            self.graph.vp['is_tl'] = self.graph.new_vertex_property('bool')
            self.graph.vp['coord'] = self.graph.new_vertex_property('vector<int>')
            self.graph.vp['x_coord'] = self.graph.new_vertex_property('int')
            self.graph.vp['z_coord'] = self.graph.new_vertex_property('int')
            self.graph.ep['weight'] = self.graph.new_edge_property('int')

        print(self.graph)
    def do_import(self, filepath):
        raise NotImplementedError

    def add_tl(self, origin, destination):
        if origin in self.graph.vp.coord:
            logging.debug(f"TL {origin} to {destination} already known")
            return
        org_vt = self.graph.add_vertex()
        dst_vt = self.graph.add_vertex()
        oe = self.graph.add_edge(org_vt, dst_vt)
        ie = self.graph.add_edge(dst_vt, org_vt)
        self.graph.vp.coord[org_vt] = origin
        self.graph.vp.coord[dst_vt] = destination
        self.graph.ep.weight[oe] = TL_COST
        self.graph.ep.weight[ie] = TL_COST
        self.graph.vp.is_tl[org_vt] = True
        self.graph.vp.is_tl[dst_vt] = True

    def make_connections(self):
        #self.graph.set_vertex_filter(self.graph.vp.is_tl)
        # FIXME: Two TL on the same horizontinal coordinate will cause issues
        num = 0
        for ovt, o_coord in self.graph.iter_vertices([self.graph.vp.coord]):
            for dvt, d_coord in self.graph.iter_vertices([self.graph.vp.coord]):
                if self.graph.edge(ovt, dvt):
                    continue  # no need to link what is already there
                dist = manhattan(o_coord, d_coord)
                if 0 < dist < LINK_DIST:
                    num += 1
                    e = self.graph.add_edge(ovt, dvt)
                    assert(e)
                    self.graph.ep.weight[e] = dist
        logging.info(f"added {num} Edges")
        #self.graph.set_vertex_filter(None)

class CampaignCartographerImporter(AbstractImporter):
    def do_import(self):
        import json
        with open(self.filepath) as dbfile:
            db = json.load(dbfile)
            for item in db['Waypoints']:
                try:
                    dest = re.match('Translocator to \((-*\d+), -*\d+, (-*\d+)\)', item["Title"]).group(1,2)
                except AttributeError:
                    continue
                position = item["Position"]
                origin = (int(position["X"]) - 500000, int(position["Z"] - 500000))
                dest = (int(dest[0]), int(dest[1]))
                self.translocators.add(Node(origin, dest))

class GeojsonImporter(AbstractImporter):
    def do_import(self):
        import json
        with open(self.filepath) as dbfile:
            db = json.load(dbfile)
            for item in db['features']:
                try:
                    origin, dest = item['geometry']['coordinates']
                except KeyError:
                    logging.warning(f"missing coordinate in {geometry}")
                    continue
                origin = (int(origin[0]), -int(origin[1]))
                dest = (int(dest[0]), -int(dest[1]))
                self.add_tl(origin, dest)
                logging.debug(f"adding {origin}, {dest}")


class TSVImporter(AbstractImporter):

    def do_import(self):

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
                        self.traders[kind]
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
