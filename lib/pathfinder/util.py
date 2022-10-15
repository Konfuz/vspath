import math


def cardinal_dir(a, b):
    """Return Cardinal Direction String from coordinate origin to destination"""

    dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    dt_x = destination[0] - origin[0]
    dt_y = destination[1] - origin[1]
    ix = round(math.atan2(dt_x, -dt_y) / (2 * math.pi) * len(dirs))
    return dirs[ix]
