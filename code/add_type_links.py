import argparse
import csv

def read_input(filename):
    results = None
    with open(filename) as fp:
        reader = csv.DictReader(fp)
        results = list(reader)
    return results


def write_output(filename, types):
    with open(filename, 'w+') as fp:
        writer = csv.DictWriter(fp, fieldnames=types[0].keys())
        writer.writeheader()
        writer.writerows(types)


def trie_insert(trie, key, value):
    if not isinstance(key, str):
        raise KeyError('Invalid key {}: must be a non-empty string!'.format(key))
    if len(key) == 0:
        trie[''] = value
    else:
        if not key[0] in trie:
            trie[key[0]] = {}
        trie_insert(trie[key[0]], key[1:], value)


def trie_bfs(trie, max_depth=1000):
    'Extract all values from the trie.'
    queue = [(0, trie)]
    results = []
    while queue:
        (depth, node) = queue.pop(0)
        if '' in node:
            results.append((depth, node['']))
        if depth < max_depth:
            queue.extend([(depth+1, child) for key, child in node.items() if key != ''])
    return results


def trie_match(trie, query, depth=0, min_depth=0, max_bfs_depth=1000):
    if not query:
        return depth, [(0, trie[''])] if '' in trie else []
    if query[0] not in trie:
        if depth >= min_depth:
            return depth, trie_bfs(trie, max_depth=max_bfs_depth)
        else:
            return depth, []
    else:
        return trie_match(trie[query[0]], query[1:], depth=depth+1)


def build_type_names_trie(types):
    trie = {}
    for t in types:
        trie_insert(trie, t['type_name'], t['type_id'])
    return trie


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Search type descriptions for references to other '
                    'types and convert them to links with IDs.')
    parser.add_argument(
        'filename', metavar='FILE',
        help='The CSV file containing the types table.')
    parser.add_argument(
        '-o', '--output-file', metavar='FILE',
        help='File to write output to (if different then input).')
    parser.add_argument(
        '-t', '--threshold', type=float, default=0.8,
        help='Minimum ratio of matched prefix length to the whole name.')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    types = read_input(args.filename)
    trie = build_type_names_trie(types)
    names = { t['type_id']: t['type_name'] for t in types }
    for t in types:
        i = t['type_description'].find('&gt;')
        while i > -1:
            query = t['type_description'][i+len('&gt;'):]
            j, matches = trie_match(trie, query, min_depth=7, max_bfs_depth=5)
            if matches and j/(j+matches[0][0]) > args.threshold:
                k = i+len('&gt;')+j
                while k < len(t['type_description']) and t['type_description'][k].isalpha():
                    k += 1
                linktext = t['type_description'][i+len('&gt;'):k]
                t['type_description'] = t['type_description'].replace(
                    '&gt;'+linktext,
                    '&gt;[{}|{}]'.format(matches[0][1], linktext))
            i = t['type_description'].find('&gt;', i+1)
    output_file = args.output_file if args.output_file is not None else args.filename
    write_output(output_file, types)

