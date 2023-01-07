"""
Generate runtime-config from various sources.
"""
import argparse
import yaml
import sys
import re

defaults = {
    'config': 'config/config.yaml',
    'import': None,
    'clean': False,
    'origin': None,
    'goal': None,
    'listlandmarks': False,
    'data': 'data/navgraph.gt',
    'drawgraph': False,
    'dbfile': None,  # Import File
    'link_dist_tl': 10000,
    'link_dist_trader': 1000,
    'link_dist_landmark': 1000,
    'tl_cost': 0,
    'global_offset': (500000, 50000),
    'debugmode': True
}




def _load_config_file(config_path):
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def _parse_args():
    description = """Various pathfinding options for vintagestory using translocators"""
    epilog = """Make backups. No Warranty. Do not sue me if your parrot dies!"""
    parser = argparse.ArgumentParser(description=__doc__,
                                     epilog=epilog)
    parser.add_argument('-i', '--import',
                        metavar='dbfile',
                        dest='dbfile',
                        help='file to import')
    parser.add_argument('-c', '--config', help='path to config file', default='config/config.yaml')
    parser.add_argument('--clean',
                        action='store_true',
                        help='clears the entire database')
    parser.add_argument('origin',
                        help='origin coordinate x,y or landmark',
                        nargs='?')
    parser.add_argument('goal',
                        help='target coordinate x,y or landmark',
                        nargs='?')
    parser.add_argument('--listlandmarks', action='store_true', help='output known landmarks')
    parser.add_argument('-d', '--data',
                        metavar='data_file',
                        dest='data_file',
                        help='database file in graphtool format *.gt')
    parser.add_argument('--drawgraph', action='store_true', help='save a visual representation of the search-graph')

    # Hack to prevent negative coordinates to be parsed as options by argparse
    args = sys.argv
    pat = '-?[0-9]+,-?[0-9]+'
    try:
        if re.match(pat, args[-2]) or re.match(pat, args[-1]):
            args.insert(-2, '--')
    except IndexError:
        pass  # Lack of parameters, not an issue

    return parser.parse_args()


class Config(dict):
    def __init__(self):
        args = vars(_parse_args())
        args = {k: v for k, v in args.items() if v is not None}  # remove unspecified option-keys
        super().__init__(defaults)
        self.update(_load_config_file(args['config']))  # merge config file, config taking preference
        self.update(args)  # merge args, with args taking preference
        self.__dict__ = self  # Allow keys to be accessed as attributes. WARNING: Keys may override class-members!


# Singleton Config that can be imported from this module
config = Config()
