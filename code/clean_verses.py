#!/usr/bin/python3

import argparse
import csv
import logging
import re
import sys


def clean(string):
    string = re.sub('[0-9]', '', string)
    string = re.sub('<\/?([A-Z]+)>', '', string)
    string = string.lower().strip()
    string = re.sub(' \W+$', '', string)
    string = re.sub('^\W+ ', '', string)
    string = re.sub('\s+', '_', string)
    string = re.sub('\W', '', string)
    string = re.sub('_', ' ', string)
    return string


def parse_arguments():
    parser = argparse.ArgumentParser(description='Clean the verse texts.')
    parser.add_argument(
        '-c', '--column', default='text',
        help='The name of the column containing the text to clean.')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    reader = csv.DictReader(sys.stdin)
    writer = csv.DictWriter(sys.stdout, reader.fieldnames, lineterminator='\n')
    writer.writeheader()
    for i, row in enumerate(reader, 1):
        if args.column in row:
            row[args.column] = clean(row[args.column])
        else:
            logging.warn('Record {} contains no field \'{}\''\
                         .format(i, args.column))
        writer.writerow(row)

