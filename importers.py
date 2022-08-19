
import logging
import re
from datastructures import Translocator

class AbstractImporter():
    translocators = set()
    landmarks = {}
    traders = {}
    filepath = ''

    def __init__(self, filepath, translocators=set(), landmarks={}, traders={}):
        self.translocators = translocators
        self.landmarks = landmarks
        self.traders = traders
        self.filepath = filepath

    def do_import(self, filepath):
        raise NotImplementedError


class GeojsonImporter(AbstractImporter):
    def do_import(self):
        import json
        with open(self.filepath) as dbfile:
            db = json.load(dbfile)
            for item in db['features']:
                try:
                    origin, goal = item['geometry']['coordinates']
                except KeyError:
                    logging.warning(f"missing coordinate in {geometry}")
                    continue
                origin = (int(origin[0]), int(origin[1]))
                goal = (int(goal[0]), int(goal[1]))
                self.translocators.add(Translocator(origin, goal))


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
                    self.translocators.add(Translocator(org, to_2d_coord(row['Destination'])))
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


def get_importer(filepath, translocators={}, landmarks={}, traders={}):
    if filepath.endswith('.tsv'):
        return TSVImporter(filepath, translocators, landmarks, traders)
    elif filepath.endswith('.geojson'):
        return GeojsonImporter(filepath, translocators, landmarks, traders)
    logging.error(f'Could not find a valid importer for {filepath}')
