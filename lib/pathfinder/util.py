import math
import re

trader_enum = {
    0: 'unknown',
    1: 'artisan',
    2: 'agricultural',
    3: 'building',
    4: 'clothing',
    5: 'commodities',
    6: 'food',
    7: 'furniture',
    8: 'survival',
    9: 'treasure',
    10: 'glass',
    11: 'pottery',
    12: 'luxuries'
}
def cardinal_dir(origin, destination):
    """Return Cardinal Direction String from coordinate origin to destination"""

    dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    dt_x = destination[0] - origin[0]
    dt_y = destination[1] - origin[1]
    ix = round(math.atan2(dt_x, -dt_y) / (2 * math.pi) * len(dirs))
    return dirs[ix]

def manhattan(a, b):
    x = abs(a[0] - b[0])
    y = abs(a[1] - b[1])
    return x + y


# def manhattan(ox, oz, dx, dz):
#     x = abs(ox - dx)
#     y = abs(oz - dz)
#     return x + y

def get_trader_type(description):
    description = description.lower()
    if 'artisan' in description: return 1
    if 'agricultur' in description: return 2
    if 'building' in description: return 3
    if 'clothing' in description: return 4
    if 'commodit' in description: return 5
    if 'food' in description: return 6
    if 'furniture' in description: return 7
    if 'survival' in description: return 8
    if 'treasure' in description: return 9
    if 'glass' in description: return 10
    if 'pottery' in description: return 11
    if 'luxuries' in description: return 12
    return 0

def parse_coord(coord_str):
    try:
        x, y = re.split(',', coord_str)
        x = int(x)
        y = int(y)
        return (x, y)
    except ValueError:
        logging.debug("coordinate could not be parsed as x,y")
    try:
        return landmarks[coord_str]
    except KeyError:
        logging.error(f"Unknown coordinate: {coord_str}")
    return None

