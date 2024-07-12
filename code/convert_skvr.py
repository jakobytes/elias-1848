import argparse
import csv
import json
import lxml.etree as ET
import logging
import os.path as P
import re

from common_xml_functions import \
    elem_content_to_str, \
    insert_refnrs, \
    parse_skvr_refs


PREFIX = 'skvr_'


def is_county_id(place_id):
    return int(place_id.replace(PREFIX, '')) >= 9000


#########################################################################
# MAPPING FUNCTIONS
#########################################################################

def map_verses(item):
    for i, node in enumerate(item['textxml'], 1):
        yield { 'poem_id'    : item['poem_id'],
                'pos'        : i,
                'verse_type' : node.tag,
                'text'       : insert_refnrs(elem_content_to_str(node)).rstrip() }

def map_refs(item):
    if item['refsxml'] is not None:
        for refnr, reftext in parse_skvr_refs(item['refsxml']):
            yield { 'poem_id'    : item['poem_id'],
                    'ref_number' : refnr,
                    'ref_type'   : 'REF',
                    'ref'        : reftext.strip() }


def map_raw_meta(item):
    for node in item['metaxml']:
        yield { 'poem_id' : item['poem_id'],
                'field'   : node.tag,
                'value'   : insert_refnrs(elem_content_to_str(node)).rstrip() }

def map_meta(item):
    yield { key: item[key] \
            for key in ('poem_id', 'year', 'place_id', 'collector_id') }

# A dictionary: output_filename => (fieldnames, mapping_function)
# The mapping_function maps one row of the input CSV (i.e. one poem) to an
# iterator over output rows.
mappers = {
    'verses.csv': (('poem_id', 'pos', 'verse_type', 'text'), map_verses),

    'refs.csv' : (('poem_id', 'ref_number', 'ref_type', 'ref'),  map_refs),

    'meta.csv' : (('poem_id', 'year', 'place_id', 'collector_id'), map_meta),

    'raw_meta.csv' : (('poem_id', 'field', 'value'),  map_raw_meta),
}


def transform_rows(input_rows, mappers, output_dir='.'):
    '''Applies the mappers to an iterator over input rows.'''

    outfiles = { m_file: open(P.join(output_dir, m_file), 'w+') \
                         for m_file in mappers }
    writers = { m_file: csv.DictWriter(outfiles[m_file], m_header)
                for m_file, (m_header, m_func) in mappers.items() }
    for writer in writers.values():
        writer.writeheader()
    for row in input_rows:
        for m_file, (m_header, m_func) in mappers.items():
            writers[m_file].writerows(m_func(row))
    for fp in outfiles.values():
        fp.close()


def read_csv(filename, encoding='utf-8'):
    with open(filename) as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            yield row


def map_county_codes(items, prefix):
    for item in items:
        if is_county_id(item['id']):
            yield {
                'place_id' : prefix + str(item['id']),
                'county_code' : item['area']
            }


def map_places(items, prefix):
    counties = {}           # county_name -> id
    places = []
    replacements = {
        'Etelä-Karjala (Karjalan kannas)': 'Etelä-Karjala',
        'Länsi-Pohja': 'Länsipohja',
        'Peräpohjola, Lappi': 'Peräpohjola',
        'Tverin alue': 'Tveri',
        'Ei': 'Ei aluetietoa'
    }
    # first pass: figure out the parent IDs for parishes
    for item in items:
        # remove the trailing letter from the county name
        # (e.g. "Varsinais-Suomi a" -> "Varsinais-Suomi")
        county_name = re.sub(' ([a-zäöå]|oN|oR)$', '', item['county'])
        if county_name in replacements:
            county_name = replacements[county_name]
        is_county = is_county_id(item['id'])
        places.append((item['id'], item['parish'], county_name, is_county))
        if is_county:
            counties[county_name] = item['id']
    # second pass: output the results
    for place_id, place_name, county_name, is_county in places:
        if place_id == prefix + '9999':
            logging.debug('Skipping unknown place')
        elif county_name not in counties:
            logging.error('County not found: ' + county_name)
        else:
            yield {
                'place_id': place_id,
                'place_name': place_name,
                'place_type': 'county' if is_county else 'parish',
                'place_parent_id': str(counties[county_name]) \
                                   if not is_county else None
            }


def read_skvr_xml_types(filename):
    doc = ET.parse(filename).getroot()
    for n_file in doc:
        main_title = n_file.find('main_title').text
        parent_type_id, type_name = None, None
        if main_title.startswith('t0'):
            i = main_title.index(' ')
            parent_type_id, type_name = main_title[:i], main_title[i+1:]
        else:
            parent_type_id, type_name = '?', main_title
        yield { 'type_id': parent_type_id, 'type_name': type_name,
                'type_description': None, 'type_parent_id': None,
                'type_comparison': None, 'type_old_names': None,
                'type_ref': None }
        for n_type in n_file.iter('type'):
            yield {
                'type_id': n_type.find('code').text.strip(),
                'type_name': n_type.find('title_1').text,
                'type_description': n_type.find('notes').text,
                'type_parent_id': parent_type_id,
                'type_old_names': n_type.find('title_2').text,
                'type_comparison': n_type.find('title_3').text,
                'type_ref': n_type.find('ref').text }


def process_skvr_typetree(tree, prefix):
    queue = [(t, None) for t in tree]          # [(t, type_parent_id), ...]
    while queue:
        t, type_parent_id = queue.pop(0)
        if t['description'] is not None:
            t['description'] = t['description'].replace('&', '&amp;')\
                               .replace('<', '&lt;').replace('>', '&gt;')
        yield { 'type_id': prefix + t['id'], 'type_name': t['name'],
                'type_description': t['description'],
                'type_parent_id': prefix + type_parent_id \
                                  if type_parent_id is not None else None,
                'type_comparison': t['comparison'] }
        if 'branch' in t:
            queue.extend((child, t['id']) for child in t['branch'])


def read_skvr_poem_types(filename, prefix):
    with open(filename) as fp:
        reader = csv.reader(fp, delimiter='\t')
        for row in reader:
            if len(row) == 5:
                yield { 'poem_id': row[3], 'type_id': prefix + row[0],
                        'type_is_minor': '1' if row[4] == '*' else '0' }


def transform_hash(inputs, outfile, fieldnames, mapper):
    with open(outfile, 'w+') as fp:
        writer = csv.DictWriter(fp, fieldnames)
        writer.writeheader()
        writer.writerows(mapper(inputs))


def read_inputs(filenames, prefix):
    '''Transforms the XML files to an iterator over rows, each row
       corresponding to one ITEM.'''
    for filename in filenames:
        for node in ET.parse(filename).getroot():
            meta = node.xpath('./META')
            text = node.xpath('./TEXT')
            refs = node.xpath('./REFS')
            assert len(meta) == 1 and len(text) == 1 and len(refs) <= 1
            item = {
                'poem_id'      : node.attrib['nro'],
                'collector_id' : node.attrib['k'] \
                                 if 'k' in node.attrib else None,
                'place_id'     : node.attrib['p'] \
                                 if 'p' in node.attrib else None,
                'year'         : node.attrib['y'] \
                                 if 'y' in node.attrib else None,
                'metaxml'      : meta[0],
                'textxml'      : text[0],
                'refsxml'      : refs[0] if refs else None
            }
            yield item


def parse_arguments():
    parser = argparse.ArgumentParser(description='Convert SKVR to CSV files.')
    parser.add_argument(
        'xml_files', nargs='*', metavar='FILE', default=[],
        help='A list of input files in XML format.')
    parser.add_argument(
        '-d', '--output-dir', metavar='PATH', default='.',
        help='The directory to write output files to.')
    parser.add_argument(
        '-p', '--prefix', metavar='PREFIX', default='skvr_',
        help='The prefix to prepend to collector, place and type IDs.')
    parser.add_argument(
        '--places-file', metavar='FILE',
        help='The file containing a list of places in "hash map" format.')
    parser.add_argument(
        '--xml-types-file', metavar='FILE',
        help='The type index in XML format.')
    parser.add_argument(
        '--json-types-file', metavar='FILE',
        help='The type index in JSON format (with hierarchy).')
    parser.add_argument(
        '--poem-types-file', metavar='FILE',
        help='The file with mappings between poem IDs and type IDs.')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()

    if args.xml_files:
        inputs = read_inputs(args.xml_files, args.prefix)
        transform_rows(inputs, mappers, output_dir=args.output_dir)

    if args.places_file is not None:
        inputs = list(read_csv(args.places_file))
        transform_hash(
            inputs,
            P.join(args.output_dir, 'county_codes.csv'),
            ('place_id', 'county_code'),
            lambda items: map_county_codes(items, args.prefix))
        transform_hash(
            inputs,
            P.join(args.output_dir, 'places.csv'),
            ('place_id', 'place_name', 'place_type', 'place_parent_id'),
            lambda items: map_places(items, args.prefix))

    if args.xml_types_file is not None:
        types = read_skvr_xml_types(args.xml_types_file)
        with open(P.join(args.output_dir, 'xmltypes.csv'), 'w+') as fp:
            fieldnames = ('type_id', 'type_name', 'type_description',
                          'type_parent_id', 'type_old_names',
                          'type_comparison', 'type_ref')
            writer = csv.DictWriter(fp, fieldnames)
            writer.writeheader()
            writer.writerows(types)

    if args.json_types_file is not None:
        tree = None
        with open(args.json_types_file) as fp:
            tree = json.load(fp)
        types = process_skvr_typetree(tree, args.prefix)
        with open(P.join(args.output_dir, 'types.csv'), 'w+') as fp:
            fieldnames = ('type_id', 'type_name', 'type_description',
                          'type_parent_id', 'type_comparison')
            writer = csv.DictWriter(fp, fieldnames)
            writer.writeheader()
            writer.writerows(types)

    if args.poem_types_file is not None:
        poem_types = read_skvr_poem_types(args.poem_types_file, args.prefix)
        with open(P.join(args.output_dir, 'poem_types.csv'), 'w+') as fp:
            fieldnames = ('poem_id', 'type_id', 'type_is_minor')
            writer = csv.DictWriter(fp, fieldnames)
            writer.writeheader()
            writer.writerows(poem_types)

