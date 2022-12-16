#!/usr/bin/env python3
"""convert webmap geojson to a campaign-cartographer importable json"""

import json
from datetime import datetime
from copy import deepcopy
import argparse

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
    tl2_spec = deepcopy(tl1_spec)
    d1, d2 = indata['properties']['depth1'], indata['properties']['depth2']
    tl1, tl2 = indata['geometry']['coordinates']
    tl1_spec['Title'] = f"Translocator to ({tl2[0]}, {d2}, {-tl2[1]})"
    tl2_spec['Title'] = f"Translocator to ({tl1[0]}, {d1}, {-tl1[1]})"
    tl1_spec['Position']['X'] = tl1[0] + offset[0]
    tl1_spec['Position']['Y'] = d1
    tl1_spec['Position']['Z'] = -tl1[1] + offset[1]  # Webmap has Z * -1 for "reasons"
    tl2_spec['Position']['X'] = tl2[0] + offset[0]
    tl2_spec['Position']['Y'] = d2
    tl2_spec['Position']['Z'] = -tl2[1] + offset[1]  # Webmap has Z * -1 for "reasons"
    waypoints.append(tl1_spec)
    waypoints.append(tl2_spec)
    return waypoints


def process_trader(indata, waypoints, offset):
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
    spec['Position']['X'] = indata['geometry']['coordinates'][0] + offset[0]
    spec['Position']['Y'] = indata['properties']['z']  # Webmap calls the vs-Y "z"
    spec['Position']['Z'] = -indata['geometry']['coordinates'][1] + offset[1]  # Webmap has Z * -1 for "reasons"
    waypoints.append(spec)
    return waypoints

def process_landmark(indata, outdata, offset):
    raise NotImplementedError

def process_base(indata, outdata, offset):
    raise NotImplementedError

if __name__ == '__main__':
    epilog = """Imports points_of_interest.tsv from the Map folder and translocators_lines.geojson from the webmap"""
    parser = argparse.ArgumentParser(description=__doc__,
                                     epilog=epilog)

    parser.add_argument('inputfile')
    parser.add_argument('-w', '--worldname', default='Unknown Webmap Import')
    parser.add_argument('-o', '--output', default='export.json')
    parser.add_argument('--offset', metavar='x,z', help="absolute pos of the world spawn", default='500000,500000')

    args = parser.parse_args()
    x, z = args.offset.split(',')
    offset = (int(x), int(z))
    waypoints = []

    with open(args.inputfile) as f:
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
        process(item, waypoints, offset)

    outdata = {
        "Name": f"Webmap Waypoints - {data['name']}",
        "World": args.worldname,
        "Count": len(waypoints),
        "DateCreated": datetime.utcnow().isoformat(),
        "Waypoints": waypoints
    }

    with open(args.output, 'w') as f:
        json.dump(outdata, f, indent=4)
