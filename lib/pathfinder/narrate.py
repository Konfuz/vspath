from lib.pathfinder.util import cardinal_dir


def narrate_path(graph, vertex_list, edge_list):
    """Give textual description of a path

    :param graph: the navgraph
    :param vertex_list: ordered list of vertices to visit
    :param edge_list: ordered list of edges to traverse
    """
    coord = graph.vp.coord
    weight = graph.ep.weight
    e_is_tl = graph.ep.is_tl
    vert = tuple(coord[vertex_list.pop(0)])
    dist = 0
    step = 0
    num_tl = 0
    route = f"\n{step}. You start at {vert}.\n"
    while vertex_list:
        step += 1
        edg = edge_list.pop(0)
        oldvert = vert
        vert = tuple(coord[vertex_list.pop(0)])
        if e_is_tl[edg]:
            route += f"    translocate\n"
            num_tl += 1
        else:
            dist += weight[edg]
            direction = cardinal_dir(oldvert, vert)
            route += f"{step}. Move {direction} {weight[edg]}m from {oldvert} to {vert}.\n"
    route += f"\nYou arrive at your destination after {(dist / 1000):.2f}km of travel using {num_tl} TL!"
    print(route)
