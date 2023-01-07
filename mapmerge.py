#!/usr/bin/env python3
"""convert webmap geojson to a campaign-cartographer importable json"""

import json
from datetime import datetime
from copy import deepcopy
import argparse
import logging
from lib.pathfinder.util import get_trader_type, trader_enum, trader_colors, trader_descriptions, manhattan
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

known_features = {}  # (x,z) key -> feature_spec
doublets = 0
def is_doubled(pos, feature):
    server_icon = feature["ServerIcon"]
    trader_type = get_trader_type(feature['Title'])
    for key in known_features:
        if manhattan(key, pos) < 10:
            item = known_features[key]
            if item['ServerIcon'] == server_icon and trader_type == get_trader_type(item['Title']):
                log.debug(f"Considered doublet: {feature['Title']} {pos} =~ {key} {item['Title']}")
                doublets += 1
                return True
    return False

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
    trader_type = get_trader_type(wares)
    spec['Title'] = f"{name} the {trader_descriptions[trader_type]}"
    spec['Colour'] = trader_colors[trader_type]

    x = spec['Position']['X'] = indata['geometry']['coordinates'][0] + offset[0]
    spec['Position']['Y'] = indata['properties']['z']  # Webmap calls the vs-Y "z"
    z = spec['Position']['Z'] = -indata['geometry']['coordinates'][1] + offset[1]  # Webmap has Z * -1 for "reasons"

    if not is_doubled((x, z), spec):
        waypoints.append(spec)
        known_features[(x, z)] = spec

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
            pos = (int(item['Position']['X']), int(item['Position']['Y']))

            if not is_doubled(pos, item):
                map_features.append(item)
                known_features[pos] = item

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
