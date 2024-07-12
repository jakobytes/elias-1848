import argparse
import csv
from operator import itemgetter
import os.path
import sys


def load_mapping(filename, cols_from, cols_to):
    mapping = {}
    with open(filename) as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            key = tuple(row[c] for c in cols_from)
            val = tuple(row[c] for c in cols_to)
            mapping[key] = val
    return mapping


def map_fieldnames(fieldnames, cols_from, cols_to):
    result = []
    added = False
    for f in fieldnames:
        # insert cols_to at the index of the first column of cols_from
        if f in cols_from:
            if not added:
                result.extend(cols_to)
                added = True
        else:
            result.append(f)
    return result


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Map column combinations in the CSV.')
    parser.add_argument(
        '-f', '--cols-from', help='The columns of the input key.')
    parser.add_argument(
        '-t', '--cols-to', help='The columns of the output key.')
    parser.add_argument(
        '-u', '--unique', action='store_true',
        help='Do not output duplicate rows.')
    parser.add_argument('map_file', help='The file containing the mapping.')
    return parser.parse_args()


def main():
    args = parse_arguments()
    cols_from = args.cols_from.split(',')
    cols_to = args.cols_to.split(',')
    mapping = load_mapping(args.map_file, cols_from, cols_to)
    reader = csv.DictReader(sys.stdin)
    fieldnames = map_fieldnames(reader.fieldnames, cols_from, cols_to)
    writer = csv.DictWriter(sys.stdout, fieldnames, lineterminator='\n')
    writer.writeheader()
    seen = set()
    for row in reader:
        key = tuple(row[c] for c in cols_from)
        if key in mapping:
            for c in cols_from:
                del row[c]
            for i, c in enumerate(cols_to):
                row[c] = mapping[key][i]
            if not args.unique or tuple(row.values()) not in seen:
                writer.writerow(row)
            if args.unique:
                seen.add(tuple(row.values()))


if __name__ == '__main__':
    main()

