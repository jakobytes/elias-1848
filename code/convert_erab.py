import argparse
from collections import OrderedDict
import csv
import lxml.etree as ET
import logging
import os.path as P
import re
import sys

from common_xml_functions import elem_content_to_str
# TODO restructure -- these are now also common functions
from convert_skvr import read_inputs, transform_rows, map_meta

# Names of input files.
FILENAMES = {
    'collectors'     : 'koguja.csv',
    'counties'       : 'maakond.csv',
    'genres'         : 'zanr.csv',
    'main'           : 'main.csv',
    'parishes'       : 'kihelkond.csv',
    'poem_collector' : 'laul_koguja.csv',
    'poem_place'     : 'laul_koht.csv',
    'poem_type'      : 'laul_hierarhia.csv',
    'poem_type_old'  : 'hierarhia_originaal.csv',
    'types'          : 'hierarhia.csv',
}

# FIXME replace with args.prefix
PREFIX = 'erab_'

# Prefix added to place IDs to avoid overlaps both between counties and
# parishes as well as between datasets.
PLACE_PREFIX = {
    'county' : 'erab_c',
    'parish' : 'erab_p'
}

def map_verses(item):

    def _node_to_dict(node, i, prefix=''):
        return { 'poem_id'    : item['poem_id'],
                 'pos'        : i,
                 'verse_type' : prefix + node.tag,
                 'text'       : elem_content_to_str(node).rstrip() }
    
    i = 1
    for node in item['textxml']:
        if node.tag == 'RREFR':
            for child in node:
                yield _node_to_dict(child, i, prefix='RREFR_')
                i += 1
        else:
            yield _node_to_dict(node, i)
            i += 1


def map_raw_meta(item):

    def _node_to_dict(node, prefix=''):
        return { 'poem_id' : item['poem_id'],
                 'field'   : prefix + node.tag,
                 'value'   : elem_content_to_str(node).rstrip() }

    for node in item['metaxml']:
        if node.tag in ('INF', 'YHT_ANDMED'):
            for child in node:
                yield _node_to_dict(child, prefix=node.tag+'_')
        else:
            yield _node_to_dict(node)


def map_refs(item):
    if item['refsxml'] is not None:
        for i, node in enumerate(item['refsxml'], 1):
            refnr = None
            text = elem_content_to_str(node).strip()
            m = re.match('^([0-9])+ ', text) 
            if m is not None:
                refnr = m.group(1)
                text = text[m.end():]
            yield { 'poem_id'    : item['poem_id'],
                    'ref_number' : refnr,
                    'ref_type'   : node.tag,
                    'ref'        : text }

def map_poem_year(item):
    yield { key: item[key] \
            for key in ('poem_id', 'year') }


mappers = {
    'verses.csv': (('poem_id', 'pos', 'verse_type', 'text'), map_verses),
    'poem_year.csv' : (('poem_id', 'year'), map_poem_year),
    'raw_meta.csv': (('poem_id', 'field', 'value'), map_raw_meta),
    'refs.csv': (('poem_id', 'ref_number', 'ref_type', 'ref'), map_refs)
}


def read_main(path):
    global FILENAMES

    def _clean_and_parse_xml(xml: str) -> ET.Element:
        return(ET.XML(re.sub(r'&(amp;)+(\w*);', r'&\2;', xml)))

    with open(P.join(path, FILENAMES['main'])) as fp:
        reader = csv.DictReader(fp)
        for item in reader:
            for key in ('metaxml', 'textxml', 'refsxml'):
                if item[key]:
                    item[key] = _clean_and_parse_xml(item[key])
            yield item


def right_join(reader, filename, by, prefix=''):
    # by is either a pair of strings or a string
    # by=x -> by=(x, x) (same field name in both tables)
    if isinstance(by, str):
        by = (by, by)
    right_dict = {}
    added_fields = []
    with open(filename) as fp:
        rdr = csv.DictReader(fp)
        added_fields = [f for f in rdr.fieldnames if f != by[1]]
        for row in rdr:
            right_dict[row[by[1]]] = { prefix+f: row[f] for f in added_fields }
    empty = OrderedDict((prefix+f, None) for f in added_fields)
    for row in reader:
        if row[by[0]] in right_dict:
            row.update(right_dict[row[by[0]]])
        else:
            row.update(empty)
        yield row


def read_places(path):
    global FILENAMES

    # read the counties
    with open(P.join(path, FILENAMES['counties'])) as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            if int(row['maakond_id']) > 0:
                yield {
                    'place_id': PLACE_PREFIX['county']+row['maakond_id'],
                    'place_name': row['nimi'],
                    'place_type': 'county',
                    'place_parent_id': None }

    # read the parishes
    with open(P.join(path, FILENAMES['parishes'])) as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            if int(row['kihelkond_id']) > 0:
                yield {
                    'place_id': PLACE_PREFIX['parish']+row['kihelkond_id'],
                    'place_name': row['nimi'],
                    'place_type': 'parish',
                    'place_parent_id': PLACE_PREFIX['county']+row['maakond_id'] }


def read_poem_place(path, check=True):

    def _check_row(row):
        if row['maakond_id'] and row['kk_maakond_id'] is not None \
                and row['maakond_id'] != row['kk_maakond_id']:
            logging.warning(\
                'Poem {0} is associated with parish {1} and county {2},'
                ' but our data says that the county of {1} is {3}.'\
                .format(row['laul_id'], row['kihelkond_id'],
                        row['maakond_id'], row['kk_maakond_id']))

    with open(P.join(path, FILENAMES['poem_place'])) as fp:
        reader = csv.DictReader(fp)
        if check:
            reader = right_join(reader, P.join(path, FILENAMES['parishes']),
                                by='kihelkond_id', prefix='kk_')
        for row in reader:
            place_id = None
            if check:
                _check_row(row)
            if row['kihelkond_id'] and int(row['kihelkond_id']) > 0:
                place_id = PLACE_PREFIX['parish']+row['kihelkond_id']
            elif row['maakond_id'] and int(row['maakond_id']) > 0:
                place_id = PLACE_PREFIX['county']+row['maakond_id']
            if place_id is not None:
                yield {'poem_id': row['laul_id'], 'place_id': place_id }


def read_types(path):
    global FILENAMES

    with open(P.join(path, FILENAMES['types'])) as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            if row['kood'] != '999999999':
                if row['markus'] is not None:
                    row['markus'] = row['markus'].replace('&', '&amp;')\
                                    .replace('<', '&lt;').replace('>', '&gt;')
                yield { 'type_id': PREFIX + row['kood'],
                        'type_name': row['nimi'],
                        'type_description': row['markus'],
                        'type_parent_id': PREFIX + row['kood'][:-3] \
                                          if len(row['kood']) > 3 else None,
                        'internal_id': row['id'] }

    # Read the old types and create IDs for them with prefix "orig".
    old_types, cur_id = set(), 1
    with open(P.join(path, FILENAMES['poem_type_old'])) as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            if row['sona'] not in old_types:
                yield { 'type_id': PREFIX + 'orig{}'.format(cur_id),
                        'type_name': row['sona'],
                        'type_description': None, 'type_parent_id': None,
                        'internal_id': row['sona'] }
                old_types.add(row['sona'])
                cur_id += 1


def read_csv(filename):
    with open(filename) as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            yield row


def write_csv(rows, filename, fieldnames):
    with open(filename, 'w+') as fp:
        writer = csv.DictWriter(fp, fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def transform_csv(infile, outfile, fieldnames, mapper):
    with open(infile) as infp:
        write_csv(map(mapper, csv.DictReader(infp)), outfile, fieldnames)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Convert ERAB to CSV files.')
    parser.add_argument(
        'xml_files', nargs='*', metavar='FILE', default=[],
        help='A list of input files in XML format.')
    parser.add_argument(
        '-i', '--csv-input-dir', metavar='PATH', default=[],
        help='The directory containing the CSV files from ERAB dump.')
    parser.add_argument(
        '-p', '--prefix', metavar='PREFIX', default='erab_',
        help='The prefix to prepend to collector, place and type IDs.')
    parser.add_argument(
        '-d', '--output-dir', metavar='PATH', default='.',
        help='The directory to write output files to.')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    if args.xml_files:
        inputs = read_inputs(args.xml_files, args.prefix)
        transform_rows(inputs, mappers, output_dir=args.output_dir)

    if args.csv_input_dir is not None:

        # transform places
        write_csv(read_places(args.csv_input_dir),
                  P.join(args.output_dir, 'places.csv'),
                  ('place_id', 'place_name', 'place_type', 'place_parent_id'))
        write_csv(read_poem_place(args.csv_input_dir, check=True),
                  P.join(args.output_dir, 'poem_place.csv'),
                  ('poem_id', 'place_id'))

        # transform collectors
        transform_csv(P.join(args.csv_input_dir, FILENAMES['collectors']),
                      P.join(args.output_dir, 'collectors.csv'),
                      ('collector_id', 'collector_name'),
                      lambda row: {'collector_id': PREFIX+row['koguja_id'],
                                   'collector_name': row['nimi']})
        transform_csv(P.join(args.csv_input_dir, FILENAMES['poem_collector']),
                      P.join(args.output_dir, 'poem_collector.csv'),
                      ('poem_id', 'collector_id'),
                      lambda row: {'poem_id': row['laul_id'],
                                   'collector_id': PREFIX+row['koguja_id']})

        # types -- merging the old and new type indices
        # `types_dict` contain the type IDs as referenced in the poem-type
        # tables. In the new index, this is an "internal ID" that is not going
        # to be used anywhere in the output data. In the old index, this is the
        # type name directly.
        types_dict = {}
        with open(P.join(args.output_dir, 'types.csv'), 'w+') as fp:
            fieldnames = ('type_id', 'type_name',
                          'type_description', 'type_parent_id')
            writer = csv.DictWriter(fp, fieldnames)
            writer.writeheader()
            for t in read_types(args.csv_input_dir):
                types_dict[t['internal_id']] = t['type_id']
                del t['internal_id']
                writer.writerow(t)

        with open(P.join(args.output_dir, 'poem_types.csv'), 'w+') as outfp:
            writer = csv.DictWriter(outfp, ('poem_id', 'type_id', 'type_is_minor'))
            writer.writeheader()
            for row in read_csv(P.join(args.csv_input_dir, FILENAMES['poem_type'])):
                if row['hierarhia_id'] != '1':
                    writer.writerow({ 'poem_id': row['laul_id'],
                                      'type_id': types_dict[row['hierarhia_id']],
                                      'type_is_minor': '0' })
            for row in read_csv(P.join(args.csv_input_dir, FILENAMES['poem_type_old'])):
                writer.writerow({ 'poem_id': row['laul_id'],
                                  'type_id': types_dict[row['sona']], 
                                  'type_is_minor': '0' })

        # genres
        transform_csv(P.join(args.csv_input_dir, FILENAMES['genres']),
                      P.join(args.output_dir, 'genres.csv'),
                      ('genre_id', 'genre_name', 'genre_comment'),
                      lambda row: {'genre_id': row['id'],
                                   'genre_name': row['nimi'],
                                   'genre_comment': row['markus']})

