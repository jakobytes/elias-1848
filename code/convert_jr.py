import argparse
import csv
import lxml.etree as ET
import logging
import os.path as P

from common_xml_functions import \
    elem_content_to_str, \
    insert_refnrs, \
    parse_skvr_refs


#########################################################################
# MAPPING FUNCTIONS
#########################################################################

def map_verses(item):
    for i, node in enumerate(item['textxml'], 1):
        # remove <O> tags together with content
        for cnode in node.iterchildren():
            if cnode.tag == 'O':
                if node.tail is None:
                    node.tail = cnode.tail
                elif cnode.tail is not None:
                    node.tail = node.tail.rstrip() + cnode.tail
                node.remove(cnode)
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
        # the tags <INF> and <LOC> have one more hierarchy level,
        # so their children are extracted
        if node.tag in ('INF', 'LOC'):
            for cnode in node.getchildren():
                yield { 'poem_id' : item['poem_id'],
                        'field'   : node.tag + '_' + cnode.tag,
                        'value'   : elem_content_to_str(cnode).rstrip() }
        # from other tags, we can extract the content directly
        else:
            yield { 'poem_id' : item['poem_id'],
                    'field'   : node.tag,
                    'value'   : elem_content_to_str(node).rstrip() }

def map_meta(item):
    yield { key: item[key] \
            for key in ('poem_id', 'year', 'place_id', 'collector_id') }

def map_poem_collector(item):
    if item['collector_id']:
        for col_id in item['collector_id'].split(';'):
            yield { 'poem_id': item['poem_id'], 'collector_id': col_id }

def map_poem_place(item):
    if item['place_id']:
        for place_id in item['place_id'].split(';'):
            yield { 'poem_id': item['poem_id'], 'place_id': place_id }

def map_poem_year(item):
    yield { key: item[key] for key in ('poem_id', 'year') }

# A dictionary: output_filename => (fieldnames, mapping_function)
# The mapping_function maps one row of the input CSV (i.e. one poem) to an
# iterator over output rows.
mappers = {
    'verses.csv': (('poem_id', 'pos', 'verse_type', 'text'), map_verses),

    'refs.csv' : (('poem_id', 'ref_number', 'ref_type', 'ref'),  map_refs),

    'poem_collector.csv' : (('poem_id', 'collector_id'), map_poem_collector),

    'poem_place.csv' : (('poem_id', 'place_id'), map_poem_place),

    'poem_year.csv' : (('poem_id', 'year'), map_poem_year),

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


def read_inputs(filenames, prefix):
    '''Transforms the XML files to an iterator over rows, each row
       corresponding to one ITEM.'''
    for filename in filenames:
        if not P.isfile(filename):
            logging.warning('Skipping "{}": file does not exist'.format(filename))
            continue
        for node in ET.parse(filename).getroot():
            meta = node.xpath('./META')
            text = node.xpath('./TEXT')
            refs = node.xpath('./REFS')
            try:
                assert len(meta) == 1 and len(text) == 1 and len(refs) <= 1
            except AssertionError:
                if len(meta) < 1:
                    logging.warning('{}: no metadata'.format(node.attrib['nro']))
                if len(text) < 1:
                    logging.warning('{}: no text'.format(node.attrib['nro']))
                logging.warning('{}: skipping'.format(node.attrib['nro']))
                continue
            item = {
                'poem_id'      : node.attrib['nro'],
                'collector_id' : prefix + node.attrib['k'] \
                                 if 'k' in node.attrib else None,
                'place_id'     : prefix + node.attrib['p'] \
                                 if 'p' in node.attrib else None,
                'year'         : node.attrib['y'] \
                                 if 'y' in node.attrib else None,
                'metaxml'      : meta[0],
                'textxml'      : text[0],
                'refsxml'      : refs[0] if refs else None
            }
            yield item


def parse_arguments():
    parser = argparse.ArgumentParser(description='Convert JR to CSV files.')
    parser.add_argument(
        'xml_files', nargs='*', metavar='FILE', default=[],
        help='A list of input files in XML format.')
    parser.add_argument(
        '-d', '--output-dir', metavar='PATH', default='.',
        help='The directory to write output files to.')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()

    if args.xml_files:
        inputs = read_inputs(args.xml_files, prefix='')
        transform_rows(inputs, mappers, output_dir=args.output_dir)

