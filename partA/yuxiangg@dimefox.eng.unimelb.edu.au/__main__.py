import sys
import json
import collections
import itertools
from collections import deque
import copy

from search.util import print_move, print_boom, print_board


def generate_all_squares_on_board():
    """ Return all squares on the board
    """
    return [(1, i, j) for i in range(8) for j in range(8)]


def generate_all_empty_squares(data):
    """ Return squares that white tokens can move to
    :param data: JSON input
    :type data: Dictionary
    """

    def helper(square, colors):
        for color in colors:
            if square[1] == color[1] and square[2] == color[2]:
                return False
        return True

    all_squares_on_board = generate_all_squares_on_board()
    whites = [tuple(white) for white in data["white"]]
    blacks = [tuple(black) for black in data["black"]]

    emptys = []
    colors = blacks + whites
    for square in all_squares_on_board:
        if helper(square, colors):
            emptys.append(square)

    return sorted(emptys)


def generate_adjacency_list(white, layout, adjacency_func):
    """Return a dictionary of adjacency list
    :param squares: list of square coordinates
    :type squares: list
    """

    non_black_squares = sorted(layout["emptys"] + layout["whites"])
    adjacency_list = {}
    for current_square in non_black_squares:
        adjacency_list[current_square] = []
        for other_square in non_black_squares:
            if other_square != current_square and other_square in adjacency_func(white[0], current_square,
                                                                                 layout):
                adjacency_list[current_square].append(other_square)

    return adjacency_list


def find_adjacent_squares(n, square, layout):
    """Return a list of adjacent square coordinates
    :param square: (x, y)
    :type: tuple
    """

    # List of other coordinates in adjacent squares
    #
    #    ├───┼───┼───┼
    #    │   │{:}│   │
    #    ├───┼───┼───┼
    #    │{:}│   │{:}│
    #    ├───┼───┼───┼
    #    │   │{:}│   │
    #    ├───┼───┼───┼

    x, y = square[1], square[2]
    adjacent_coordinates = [(i, j) for i in range(x - n, x + n + 1) for j in range(y - n, y + n + 1) if
                            i >= 0 and j >= 0 and (i, j) != (x, y) and (i == x or j == y)]

    non_black_squares = sorted(layout["emptys"] + layout["whites"])
    return [token for token in non_black_squares if tuple(token[1:]) in adjacent_coordinates]


def find_3x3_surrounding_squares(coordinate):
    """Return a list of surrounding square coordinates
    :param coordinate: (x, y)
    :type: tuple
    """

    # List of coordinates in surrounding 3x3 squares
    #
    #    ├───┼───┼───┼
    #    │{:}│{:}│{:}│
    #    ├───┼───┼───┼
    #    │{:}│   │{:}│
    #    ├───┼───┼───┼
    #    │{:}│{:}│{:}│
    #    ├───┼───┼───┼
    #

    x, y = coordinate[0], coordinate[1]
    return [(i, j) for i in [x - 1, x, x + 1] for j in [y - 1, y, y + 1] if i >= 0 and j >= 0 and (i, j) != (x, y)]


def find_5x5_surrounding_squares(coordinate):
    """Return a list of surrounding square coordinates
    :param coordinate: (x, y)
    :type: tuple
    """

    # # List of coordinates in surrounding 5x5 squares
    #
    #    ├───┼───┼───┼───┼───┼
    #    │{:}│{:}│{:}│{:}│{:}│
    #    ├───┼───┼───┼───┼───┼
    #    │{:}│   │   │   │{:}│
    #    ├───┼───┼───┼───┼───┼
    #    │{:}│   │   │   │{:}│
    #    ├───┼───┼───┼───┼───┼
    #    │{:}│   │   │   │{:}│
    #    ├───┼───┼───┼───┼───┼
    #    │{:}│{:}│{:}│{:}│{:}│
    #    ├───┼───┼───┼───┼───┼

    x, y = coordinate[0], coordinate[1]
    return [(i, j) for i in [x - 2, x - 1, x, x + 1, x + 2] for j in [y - 2, y - 1, y, y + 1, y + 2] if
            i >= 0 and j >= 0 and
            (i, j) != (x, y) and ((i, j) not in find_3x3_surrounding_squares((x, y)))]


def bfs_shortest_path(blacks, graph, start, end):
    """Return shortest path from start to end in form of a list of coordinates
    :param graph: dictionary of adjacency list
    :param start: coordinate (x, y)
    :param end: coordinate (x, y)
    """

    # https://stackoverflow.com/questions/8922060/how-to-trace-the-path-in-a-breadth-first-search
    # maintain a queue of paths
    queue = []
    # push the first path into the queue
    queue.append([start])

    visited = []

    while queue:
        # get the first path from the queue
        path = queue.pop(0)
        # get the last node from the path
        node = path[-1]
        if node not in visited:
            visited.append(node)
        # path found
        if node == end:
            return path
        # enumerate all adjacent nodes, construct a new path and push it into the queue

        for adjacent in graph.get(node, []):
            inbetween = []

            if adjacent[1] == node[1]:
                if adjacent[2] < node[2]:
                    for i in range(node[2] - adjacent[2] - 1):
                        inbetween.append((adjacent[1], adjacent[2] + i + 1))
                else:
                    for i in range(adjacent[2] - node[2] - 1):
                        inbetween.append((adjacent[1], node[2] + i + 1))

            else:
                if adjacent[1] < node[1]:
                    for i in range(node[1] - adjacent[1] - 1):
                        inbetween.append((adjacent[2], adjacent[1] + i + 1))
                else:
                    for i in range(adjacent[1] - node[1] - 1):
                        inbetween.append((adjacent[2], node[1] + i + 1))

            def helper():
                if inbetween == []:
                    return True

                for token in inbetween:
                    if token in [tuple(token[1:]) for token in blacks]:
                        return True
                return False

            if helper():
                new_path = list(path)
                if adjacent in new_path:
                    continue
                new_path.append(adjacent)
                if sorted(set(new_path), key=lambda k: (k[0], k[1])) == sorted(visited):
                    continue
                queue.append(new_path)


def dfs(graph, start):
    # https://github.com/TheAlgorithms/Python/blob/9eac17a4083ad08c4bb0520cb0b8e5ce385f9ce0/graphs/dfs.py
    explored, stack = set(), [start]
    while stack:
        v = (
            stack.pop()
        )  # one difference from BFS is to pop last element here instead of first one
        if v in explored:
            continue

        explored.add(v)

        for w in graph[v]:
            if w not in explored:
                stack.append(w)
    return explored


def connected_components(graph):
    """Return a list of connected black tokens. e.g. [[(0, 2), (1, 1), (2, 0)], [(4, 7)], [(7, 7)]]
    """

    # https://stackoverflow.com/questions/10301000/python-connected-components
    seen = set()

    for root in graph.keys():
        if root not in seen:
            seen.add(root)
            component = []
            queue = deque([root])
            while queue:
                node = queue.popleft()
                component.append(node)
                for neighbor in graph[node]:
                    if neighbor not in seen:
                        seen.add(neighbor)
                        queue.append(neighbor)
            yield component


def print_move_actions(white, path):
    """Print move actions from a given path to standard output
    :param path: list of (x, y)
    :type path: list
    """

    for i in range(len(path) - 1):
        n = 1
        if (abs(path[i][1] - path[i + 1][1]) + abs(path[i][2] - path[i + 1][2])) > 1:
            n = int(white[0][1:]) - 1
        print_move(n, path[i][1], path[i][2], path[i + 1][1], path[i + 1][2])


def board(data):
    whites, blacks = data['white'], data['black']

    board_dict = dict()

    for white in whites:
        if white[0] > 1:
            board_dict[tuple(white[1:])] = "W" + str(white[0])
        else:
            board_dict[tuple(white[1:])] = "W"

    for black in blacks:

        if black[0] > 1:
            board_dict[tuple(black[1:])] = "B" + str(black[0])
        else:
            board_dict[tuple(black[1:])] = "B"

    print_board(board_dict)


def get_3x3_surrounding_tokens(tokens, squares):
    _3x3_surrounding_tokens = []
    for square in squares:
        for token in tokens:
            if token[1] == square[0] and token[2] == square[1]:
                _3x3_surrounding_tokens.append(token)
                continue
    return _3x3_surrounding_tokens


def run_case(data):
    """ Run simulation
    :param data: JSON input
    :type data: Dictionary
    """

    emptys = generate_all_empty_squares(data)
    whites = [tuple(white) for white in data["white"]]
    blacks = [tuple(black) for black in data["black"]]

    layout = {
        "emptys": emptys,
        "whites": whites,
        "blacks": blacks
    }

    def get_exploded_dict(layout):

        def get_exploded_tokens(coordinate, exploded_tokens):

            _3x3_surrounding_white_tokens = get_3x3_surrounding_tokens(layout["whites"],
                                                                       find_3x3_surrounding_squares(coordinate))
            _3x3_surrounding_black_tokens = get_3x3_surrounding_tokens(layout["blacks"],
                                                                       find_3x3_surrounding_squares(coordinate))

            for token in _3x3_surrounding_black_tokens:
                if token not in exploded_tokens['blacks']:
                    exploded_tokens['blacks'].append(token)
                    coordinate = tuple(token[1:])
                    get_exploded_tokens(coordinate, exploded_tokens)
            for token in _3x3_surrounding_white_tokens:
                if token not in exploded_tokens['whites']:
                    exploded_tokens['whites'].append(token)
                    coordinate = tuple(token[1:])
                    get_exploded_tokens(coordinate, exploded_tokens)

        exploded_dict = {}
        non_black_squares = sorted(layout["emptys"] + layout["whites"])
        for non_black_square in non_black_squares:
            exploded_tokens = {"blacks": [], "whites": []}
            get_exploded_tokens(non_black_square[1:], exploded_tokens)
            exploded_dict[non_black_square] = exploded_tokens
        return exploded_dict

    def pick_up(white, layout):
        # A white token is picked up
        if white not in layout["emptys"]:
            layout["emptys"].append(white)

        if white in layout["whites"]:
            layout["whites"].remove(white)
        return layout

    def place(empty, layout):

        # A white token is placed
        if empty in layout["emptys"]:
            layout["emptys"].remove(empty)
        layout["whites"].append(empty)
        return layout

    # Recursively finding the destinations whites will move to
    def find_destinations(exploded_blacks, exploded_whites, destinations, n, destinations_list, layout):
        if n >= 1:

            # Determine which white to move
            white = layout["whites"][0]

            # Pick up a token and Reset layout
            layout = pick_up(white, layout)
            # print(n, white, layout["whites"])
            # Obtain exploded dictionary
            exploded_dict = get_exploded_dict(layout)
            non_blacks = sorted(layout["emptys"] + layout["whites"])
            for empty in non_blacks:
                exploded_blacks_tmp = exploded_blacks.copy()
                exploded_whites_tmp = exploded_whites.copy()

                # Obtain list of exploded tokens
                token_dict = exploded_dict[empty]
                for black in token_dict['blacks']:
                    if black not in exploded_blacks:
                        exploded_blacks_tmp.append(black)
                for exploded_white in token_dict['whites']:
                    if exploded_white not in exploded_whites:
                        exploded_whites_tmp.append(exploded_white)

                # Place the token
                layout = place(empty, layout)

                # Recursively adding exploded blacks
                if len(find_destinations(exploded_blacks_tmp, exploded_whites_tmp, destinations + [empty],
                                         n - 1 - len(exploded_whites_tmp), destinations_list, layout)) == len(
                    blacks):
                    destinations_list.append(destinations + [empty])

                # Pick up placed token
                layout = pick_up(empty, layout)

            # Place the token back
            layout = place(white, layout)
            return exploded_blacks
        else:
            return exploded_blacks

    destinations = []
    destinations_list = []
    layout_copy = copy.deepcopy(layout)
    find_destinations([], [], destinations, len(whites), destinations_list, layout_copy)
    destinations = destinations_list[0]
    # print("destinations", destinations)

    # Level 1-3
    for i in range(len(destinations)):
        white = layout["whites"][i]
        start = tuple(white)
        end = destinations[i]
        whites_adjacency_list = generate_adjacency_list(white, layout, find_adjacent_squares)
        # Check if end is accessible
        if end in dfs(whites_adjacency_list, start):
            shortest_path = bfs_shortest_path(blacks, whites_adjacency_list, start, end)
            print_move_actions(white, shortest_path)
            print_boom(end[1], end[2])
    return

    ###**************************************************************************************###
    ###                                     level 4                                          ###
    ###**************************************************************************************###
    # Determine if the whites are trapped
    reachable = {}
    for i in range(len(destinations)):
        for white in whites:
            start = tuple(white)
            end = destinations[i]
            whites_adjacency_list = generate_adjacency_list(white, layout, find_adjacent_squares)
            # Check if end is accessible
            if end in dfs(whites_adjacency_list, start):
                if white not in reachable.keys():
                    reachable[white] = [end]
                else:
                    reachable[white].append(end)
            else:
                reachable[white] = []

    reachable_copy = reachable.copy()
    for i in range(len(destinations)):
        for k, v in reachable_copy.items():
            if destinations[i] in v:
                reachable_copy.pop(k)
                break

    # Level 1-3
    if reachable_copy == {}:
        for i in range(len(destinations)):
            white = layout["whites"][i]
            start = tuple(white)
            end = destinations[i]
            whites_adjacency_list = generate_adjacency_list(white, layout, find_adjacent_squares)
            # Check if end is accessible
            if end in dfs(whites_adjacency_list, start):
                shortest_path = bfs_shortest_path(blacks, whites_adjacency_list, start, end)
                print_move_actions(white, shortest_path)
                print_boom(end[1], end[2])
        return

    # Level 4
    # Stacking
    trapped_whites = whites.copy()
    trapped_whites_copy = whites.copy()
    layout_copy = layout.copy()
    for i in range(len(trapped_whites)):
        for j in range(i + 1, len(trapped_whites)):
            start = trapped_whites[i]
            end = trapped_whites[j]
            whites_adjacency_list = generate_adjacency_list(start, layout_copy, find_adjacent_squares)
            if end in dfs(whites_adjacency_list, start):
                shortest_path = bfs_shortest_path(blacks, whites_adjacency_list, start, end)
                print_move_actions(start, shortest_path)

                # Stack
                moved = (str("W" + str(int(trapped_whites[j][0][1:]) + int(trapped_whites[i][0][1:]))),) + tuple(
                    trapped_whites[j][1:])
                layout.remove(trapped_whites[i])
                layout.append(("E", trapped_whites[i][1], trapped_whites[i][2]))
                layout.remove(trapped_whites[j])
                layout.append(moved)
                # trapped_whites[j] = moved
                trapped_whites_copy[j] = moved
                trapped_whites_copy.remove(trapped_whites[i])
                break

    trapped_whites = trapped_whites_copy.copy()
    trapped_whites.sort(key=lambda x: int(x[0][1:]), reverse=True)
    for i in range(len(destinations)):
        white = trapped_whites[i]
        start = tuple(white)
        end = destinations[i]

        whites_adjacency_list = generate_adjacency_list(white, layout, find_adjacent_squares)

        # break
        # Check if end is accessible
        if end in dfs(whites_adjacency_list, start):
            shortest_path = bfs_shortest_path(blacks, whites_adjacency_list, start, end)
            print_move_actions(white, shortest_path)
            print_boom(end[1], end[2])

            # De-stack
            moved = ("W1",) + tuple(trapped_whites[i][1:])
            layout.append(moved)
            trapped_whites.append(moved)

        else:
            trapped_whites.append(white)


def main():
    with open(sys.argv[1]) as file:
        data = json.load(file)

    # TODO: find and print winning action sequence
    board(data)
    run_case(data)


if __name__ == '__main__':
    main()
