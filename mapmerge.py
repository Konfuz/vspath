#!/usr/bin/env python3
"""convert webmap geojson to a campaign-cartographer importable json"""

import json
from datetime import datetime
from copy import deepcopy
import argparse
import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

known_features = {}  # (x,z) key -> feature_spec
doublets = 0

def foo():
    known_features['foo'] = 'baa'
    doublets += 1


COLOR_REF = {'Artisan': '#00f0f0',
          'Agricultural': '#c8c080',
    'Building materials': '#ff0000',
              'Clothing': '#008000',
           'Commodities': '#808080',
                 'Foods': '#c8c080',
             'Furniture': '#ff8000',
              'Luxuries': '#0000ff',
        'Survival goods': '#ffff00',
       'Treasure hunter': '#a000a0',
                 'Glass': '#ffc0c0',
               'Pottery': '#805c00',
               'Unknown': '#303030'
  }

JOB_REF = {'Artisan': 'Artisan',
            'Agricultural': 'Agricultural Trader',
    'Building materials': 'Building Materials Trader',
              'Clothing': 'Clothier',
           'Commodities': 'Commodities Trader',
                 'Foods': 'Food Trader',
             'Furniture': 'Furniture Trader',
              'Luxuries': 'Luxuries Trader',
        'Survival goods': 'Survival Goods Trader',
       'Treasure hunter': 'Treasure hunter',
                 'Glass': 'Glass Trader',
               'Pottery': 'Pottery Trader',
               'Unknown': 'Unknown Trader'
  }



def process_translocator(indata, waypoints, offset):
    global known_features
    global doublets
    tl1_spec = {
        "Title": "Translocator to ",
        "DetailText": None,
        "ServerIcon": "spiral",
        "DisplayedIcon": "spiral",
        "Colour": "#FFFF00FF",
        "Position": dict(X=0, Y=0, Z=0),
        "Pinned": False,
        "Selected": True
    }
    # TODO: Reduce Boilerplate
    tl2_spec = deepcopy(tl1_spec)
    d1, d2 = indata['properties']['depth1'], indata['properties']['depth2']
    tl1, tl2 = indata['geometry']['coordinates']
    tl1_spec['Title'] = f"Translocator to ({tl2[0]}, {d2}, {-tl2[1]})"
    tl2_spec['Title'] = f"Translocator to ({tl1[0]}, {d1}, {-tl1[1]})"
    x1 = tl1_spec['Position']['X'] = tl1[0] + offset[0]
    tl1_spec['Position']['Y'] = d1
    z1 = tl1_spec['Position']['Z'] = -tl1[1] + offset[1]  # Webmap has Z * -1 for "reasons"
    x2 = tl2_spec['Position']['X'] = tl2[0] + offset[0]
    tl2_spec['Position']['Y'] = d2
    z2 = tl2_spec['Position']['Z'] = -tl2[1] + offset[1]  # Webmap has Z * -1 for "reasons"
    if (x1, z1) not in known_features:
        waypoints.append(tl1_spec)
        known_features[(x1, z1)] = tl1_spec
    else:
        log.debug(f"Coordinate {(x1, z1)} already has a feature")
        doublets += 1
    if (x2, z2) not in known_features:
        waypoints.append(tl2_spec)
        known_features[(x2, z2)] = tl2_spec
    else:
        log.debug(f"Coordinate {(x2, z2)} already has a feature")
        doublets += 1
    return waypoints


def process_trader(indata, waypoints, offset):
    global known_features
    global doublets
    spec = {
        "Title": "Unknown Trader",
        "DetailText": None,
        "ServerIcon": "trader",
        "DisplayedIcon": "trader",
        "Colour": "#303030",
        "Position": dict(X=0, Y=0, Z=0),
        "Pinned": False,
        "Selected": True
    }
    name = indata['properties']['name']
    wares = indata['properties']['wares']
    try:
        spec['Title'] = f"{name} the {JOB_REF[wares]}"
    except KeyError:
        spec['Title'] = f"{name} trading {wares}"
    try:
        spec['Colour'] = COLOR_REF[wares]
    except KeyError:
        pass
    x = spec['Position']['X'] = indata['geometry']['coordinates'][0] + offset[0]
    spec['Position']['Y'] = indata['properties']['z']  # Webmap calls the vs-Y "z"
    z = spec['Position']['Z'] = -indata['geometry']['coordinates'][1] + offset[1]  # Webmap has Z * -1 for "reasons"
    if (x, z) not in known_features:
        waypoints.append(spec)
        known_features[(x, z)] = spec
    else:
        doublets += 1
        log.debug(f"Position {(x, z)} already has a feature")
    return waypoints

def process_landmark(indata, outdata, offset):
    raise NotImplementedError

def process_base(indata, outdata, offset):
    raise NotImplementedError

def process_geojson(filename, map_features=[]):
    """
    The webmap uses a geojson file for each type of feature.
    Figure out the type, convert coordinates to absolute and
    attach the features to the featurelist.

    :param filename: path to geojson
    :param map_features: List of Features
    :return: map_features
    """
    with open(filename) as f:
        data = json.load(f)

    if data['name'] == 'translocators':
        process = process_translocator
    elif data['name'] == 'traders':
        process = process_trader
    elif data['name'] == 'landmarks':
        process = process_landmark
    elif data['name'] == 'players_bases':
        process = process_base

    for item in data['features']:
        process(item, map_features, offset)

    return map_features

def process_cc_json(filename, map_features):
    global known_features
    global doublets
    with open(filename) as f:
        data = json.load(f)
        for item in data['Waypoints']:
            pos = (item['Position']['X'], item['Position']['Y'])
            if pos not in known_features:
                map_features.append(item)
                known_features[pos] = item
            else:
                log.debug(f"Position {pos} already has a feature")
                doublets += 1
    return map_features

if __name__ == '__main__':
    epilog = """Join Webmapdata (geojson) and CampaignCartographer export-files (json) into one json"""
    parser = argparse.ArgumentParser(description=__doc__,
                                     epilog=epilog)

    parser.add_argument('inputfiles', nargs='+', metavar='inputfile')
    parser.add_argument('-w', '--worldname', default='Unknown World')
    parser.add_argument('-o', '--output', default='export.json')
    parser.add_argument('--offset', metavar='x,z', help="absolute pos of the world spawn", default='500000,500000')

    args = parser.parse_args()
    x, z = args.offset.split(',')
    offset = (int(x), int(z))
    map_features = []
    for filename in args.inputfiles:
        if filename.endswith('.geojson'):
            process_geojson(filename, map_features)
        else:
            process_cc_json(filename, map_features)

    outdata = {
        "Name": f"Webmap Waypoints",
        "World": args.worldname,
        "Count": len(map_features),
        "DateCreated": datetime.utcnow().isoformat(),
        "Waypoints": map_features
    }
    log.info(f" Encountered {doublets} double landmarks")

    with open(args.output, 'w') as f:
        json.dump(outdata, f, indent=4)
