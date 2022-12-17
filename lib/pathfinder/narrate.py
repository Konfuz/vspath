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
    print(f"you start at {vert}")
    while vertex_list:
        msg = ""
        edg = edge_list.pop(0)
        oldvert = vert
        vert = tuple(coord[vertex_list.pop(0)])
        if e_is_tl[edg]:
            print(f"Translocate to {vert}")
        else:
            dist += weight[edg]
            direction = cardinal_dir(oldvert, vert)
            print(f"Move {weight[edg]}m {direction} to {vert}")
    print(f"You arrive at your destination after {(dist / 1000):.2f}km of travel!")
