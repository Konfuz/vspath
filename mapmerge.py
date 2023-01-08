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
    """Add single translocator in webmap-format to waypoints

    :param indata:
    :param waypoints:
    :param tuple offset: Worldspawn in absolute coordinates
    :return: waypoints
    """
    global known_features
    global doublets

    def tl_spec(tl, depth):
        nonlocal offset
        spec = {
            "Title": f"Translocator to ({tl[0]}, {depth}, {-tl[1]})",
            "DetailText": None,
            "ServerIcon": "spiral",
            "DisplayedIcon": "spiral",
            "Colour": "#FFFF00FF",
            "Position": dict(X=tl[0]+offset[0], Y=depth, Z=-tl[1]+offset[1]),  # Webmap has Z * -1 for "reasons"
            "Pinned": False,
            "Selected": True
        }
        pos = (spec['Position']['X'], spec['Position']['Z'])
        if pos in known_features:
            log.debug(f"Coordinate {pos} already has a feature")
            doublets += 1
            return False
        known_features[pos] = spec
        return spec

    d1, d2 = indata['properties']['depth1'], indata['properties']['depth2']
    tl1, tl2 = indata['geometry']['coordinates']

    tl1_spec = tl_spec(tl1, d1)
    tl2_spec = tl_spec(tl2, d2)

    if tl1_spec:
        waypoints.append(tl1_spec)
    if tl2_spec:
        waypoints.append(tl2_spec)
    return waypoints


def process_trader(indata, waypoints, offset):
    """Add single Trader in webmap-format to waypoints

    :param indata:
    :param waypoints:
    :param tuple offset: Worldspawn in absolute coordinates
    :return: waypoints
    """
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


def process_geojson(filename, map_features=[], no_traders=False, no_tls=False):
    """
    The webmap uses a geojson file for each type of feature.
    Figure out the type, convert coordinates to absolute and
    attach the features to the featurelist.

    :param filename: path to geojson
    :param map_features: List of Features
    :param bool no_traders: Ignore Waypoints with Trader-Icon
    :param bool no_tls: Ignore Waypoints with Spiral-Icon
    :return: map_features
    """
    with open(filename) as f:
        data = json.load(f)

    if data['name'] == 'translocators':
        if no_tls:
            logging.warning(f"--notls was set but {filename} only contains TL's! (ignoring file)")
            return map_features
        process = process_translocator
    elif data['name'] == 'traders':
        if no_traders:
            logging.warning(f"--notraders was set but {filename} only contains Traders! (ignoring file)")
            return map_features
        process = process_trader
    elif data['name'] == 'landmarks':
        process = process_landmark
    elif data['name'] == 'players_bases':
        process = process_base

    for item in data['features']:
        process(item, map_features, offset)

    return map_features


def process_cc_json(filename, map_features, no_traders=False, no_tls=False):
    global known_features
    global doublets
    with open(filename) as f:
        data = json.load(f)
        for item in data['Waypoints']:
            pos = (int(item['Position']['X']), int(item['Position']['Y']))

            if no_traders and item['ServerIcon'] == 'trader':
                continue
            if no_tls and item['ServerIcon'] == 'Spiral':
                continue
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
    parser.add_argument('--notraders', action='store_true', help="Ignore all landmarks with Trader icon")
    parser.add_argument('--notls', action='store_true', help="Ignore all landmarks with Spiral icon")

    args = parser.parse_args()
    x, z = args.offset.split(',')
    offset = (int(x), int(z))
    map_features = []
    for filename in args.inputfiles:
        if filename.endswith('.geojson'):
            process_geojson(filename, map_features, args.notraders, args.notls)
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
