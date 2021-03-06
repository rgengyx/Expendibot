import copy
import itertools
import json
import sys

from search.graph import *
from search.square import *
from search.util import *


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

    def get_exploded_dict(coord, layout):

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

        exploded_tokens = {"blacks": [], "whites": []}
        get_exploded_tokens(coord, exploded_tokens)

        return exploded_tokens

    def pick_up(n, coordinate, layout):
        # A white token is picked up

        d = 0
        white = (n, coordinate[0], coordinate[1])
        for w in layout["whites"]:
            if w[1] == coordinate[0] and w[2] == coordinate[1]:
                d = w[0] - n
        if d == 0:
            layout["emptys"].append(white)
            layout["whites"].remove(white)
        else:
            for w in layout["whites"]:
                if w[1] == white[1] and w[2] == white[2]:
                    index = layout["whites"].index(w)
                    layout["whites"].remove(w)
                    d = w[0] - 1
                    layout["whites"].insert(index, (d, w[1], w[2]))

        return layout

    def place(n, coordinate, layout):

        target = (n, coordinate[0], coordinate[1])
        if target in layout["emptys"]:
            layout["emptys"].remove(target)
            layout["whites"].insert(0, target)
        else:
            for w in layout["whites"]:
                # if w == target:
                if w[1] == target[1] and w[2] == target[2]:
                    index = layout["whites"].index(w)
                    layout["whites"].remove(w)
                    d = w[0] + 1
                    layout["whites"].insert(index, (d, w[1], w[2]))

        return layout

    def initiate_boom(exploded_blacks_tmp, exploded_whites_tmp, layout):

        for exploded_black in exploded_blacks_tmp:
            layout["blacks"].remove(exploded_black)
        for exploded_white in exploded_whites_tmp:
            layout["whites"].remove(exploded_white)

        for e in exploded_blacks_tmp + exploded_whites_tmp:
            layout["emptys"].append((1, e[1], e[2]))

        return layout

    def restore(exploded_blacks_tmp, exploded_whites_tmp, layout):

        for exploded_black in exploded_blacks_tmp:
            layout["blacks"].append(exploded_black)
        for exploded_white in exploded_whites_tmp:
            layout["whites"].append(exploded_white)

        for e in exploded_blacks_tmp + exploded_whites_tmp:
            layout["emptys"].remove((1, e[1], e[2]))

        return layout

    # Recursively finding the destinations whites will move to
    def find_destinations(exploded_blacks, exploded_whites, destinations, n, destinations_list, layout_copy, perm,
                          perm_no):

        if destinations_list != []:
            return exploded_blacks
        if n >= 1:

            # Determine which white to move
            white = layout_copy["whites"][0]
            # Pick up a token and Reset layout
            print(layout_copy["whites"])
            if layout_copy["whites"] == [(1, 4, 3), (1, 3, 4)]:
                print(n)
            layout_copy = pick_up(1, white[1:], layout_copy)

            whites_adjacency_list = generate_adjacency_list(white, layout_copy, find_adjacent_squares)
            bfs_path = bfs(whites_adjacency_list, white)
            for target in bfs_path:

                exploded_blacks_tmp = exploded_blacks.copy()
                exploded_whites_tmp = exploded_whites.copy()

                # Place the token
                layout_copy = place(target[0], target[1:], layout_copy)

                token_dict = get_exploded_dict(target[1:], layout_copy)

                ebs = []
                ews = []
                for eb in token_dict['blacks']:
                    if eb not in exploded_blacks:
                        ebs.append(eb)
                exploded_blacks_tmp.append(ebs)
                for ew in token_dict['whites']:
                    if ew not in exploded_whites:
                        ews.append(ew)
                exploded_whites_tmp.append(ews)
                layout_copy_before = copy.deepcopy(layout_copy)
                layout_copy = initiate_boom(ebs, ews, layout_copy)

                # Recursively adding exploded blacks
                total_ews = 0
                for e in ews:
                    total_ews += e[0]
                nested = find_destinations(exploded_blacks_tmp, exploded_whites_tmp, destinations + [target],
                                           n - total_ews, destinations_list, layout_copy, perm, perm_no)

                if len(list(itertools.chain(*nested))) == len(blacks):
                    destinations_list.append(destinations + [target])
                    break
                # Pick up placed token
                layout_copy = copy.deepcopy(layout_copy_before)

                layout_copy = pick_up(1, target[1:], layout_copy)

            # Place the token back
            layout_copy = place(white[0], white[1:], layout_copy)

            if destinations_list == [] and n == len(whites):
                # Rotate
                perm_no += 1
                layout["whites"] = perm[perm_no]
                layout_copy = copy.deepcopy(layout)
                find_destinations([], [], destinations, len(whites), destinations_list, layout_copy, perm, perm_no)
            return exploded_blacks
        else:
            return exploded_blacks

    destinations = []
    destinations_list = []
    layout_copy = copy.deepcopy(layout)
    perm = [list(t) for t in list(itertools.permutations(layout["whites"]))]
    layout_copy["whites"] = perm[0]
    find_destinations([], [], destinations, len(whites), destinations_list, layout_copy, perm, 0)
    # for d in destinations_list:
    #     print("-------", d)
    destinations = destinations_list[0]

    # Level 1-3
    for i in range(len(destinations)):
        white = layout["whites"][0]
        start = white
        end = destinations[i]

        # Pick up
        layout = pick_up(start[0], start[1:], layout)

        whites_adjacency_list = generate_adjacency_list(start, layout, find_adjacent_squares)

        # Place the token
        layout = place(end[0], end[1:], layout)

        token_dict = get_exploded_dict(end[1:], layout)

        ebs = []
        ews = []
        for eb in token_dict['blacks']:
            ebs.append(eb)
        for ew in token_dict['whites']:
            ews.append(ew)

        # print(layout["whites"])

        # Check if end is accessible
        # if end in dfs(whites_adjacency_list, start):
        shortest_path = bfs_shortest_path(blacks, whites_adjacency_list, start, end)
        print_move_actions(white, shortest_path)
        layout = initiate_boom(ebs, ews, layout)
        if not ebs and ews == [white]:
            continue
        print_boom(end[1], end[2])

    return

    ###**************************************************************************************###
    ###                                     level 1-4                                          ###
    ###**************************************************************************************###
    # Determine if the whites are trapped

    def token_exist_in_component(token, white_components):
        for component in white_components:
            if whites[i] in component:
                return True
        return False

    white_components = []
    for i in range(len(whites)):
        if token_exist_in_component(whites[i], white_components):
            continue

        white_components.append([whites[i]])
        for j in range(i + 1, len(whites)):
            start = whites[i]
            end = whites[j]
            whites_adjacency_list = generate_adjacency_list(start, layout, find_adjacent_squares)
            # Check if end is accessible
            if end in dfs(whites_adjacency_list, start):
                for component in white_components:
                    if start in component:
                        component.append(end)
            else:
                white_components.append([end])

    # Level 1-3
    if len(white_components) == 1:
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
    # Stack up
    for i in range(len(white_components)):
        component = white_components[i]
        for j in range(len(component[:-1])):
            start = component[j]
            end = component[-1]
            whites_adjacency_list = generate_adjacency_list(start, layout, find_adjacent_squares)
            layout = pick_up(start[0], start[1:], layout)
            shortest_path = bfs_shortest_path(blacks, whites_adjacency_list, start, end)
            print_move_actions(start, shortest_path)
            layout = place(end[0], end[1:], layout)

    # Move
    trapped_whites = layout["whites"].copy()
    trapped_whites.sort(reverse=True)
    for i in range(len(destinations)):
        start = trapped_whites[i]
        end = destinations[i]

        whites_adjacency_list = generate_adjacency_list(start, layout, find_adjacent_squares)

        # Check if end is accessible
        if end in dfs(whites_adjacency_list, start):
            print("h", (start[0] - 1, start[1], start[2]))
            shortest_path = bfs_shortest_path(blacks, whites_adjacency_list, (start[0], start[1], start[2]),
                                              end)
            print("shortest_path", shortest_path)
            print_move_actions(start, shortest_path)
            print_boom(end[1], end[2])

            # De-stack
            layout = pick_up(start, layout)
            layout = place(end, layout)
            # trapped_whites.append(moved)

        else:
            trapped_whites.append(start)


def main():
    with open(sys.argv[1]) as file:
        data = json.load(file)

    #board(data)
    run_case(data)


if __name__ == '__main__':
    main()
