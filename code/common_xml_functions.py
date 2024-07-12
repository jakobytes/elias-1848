
# %%
import xml.etree.ElementTree as ET
import logging
from operator import itemgetter
from typing import Any
import _csv
import re

# %%


def elem_content_to_str(elem: ET.Element) -> str:
    '''Get the node's content as string, but without surrounding tags.'''
    text = ET.tostring(elem, encoding='unicode')
    pattern = '<{}>(.*)</{}>'.format(elem.tag, elem.tag)
    m = re.match(pattern, text, flags=re.DOTALL)
    if m is not None:
        return m.group(1)
    elif re.match('<{} />'.format(elem.tag), text):
        return ''
    else:
        logging.warning('Pattern \'{}\' does not match string \'{}\'.'\
                        .format(pattern, text))
        return elem.text


def insert_refnrs(text: str) -> str:
    '''Convert the references like #1 or #1† to XML: <REFNR>1</REFNR>.'''
    result = ''
    m = re.search('(^|[^&])(#([0-9]+)(\u2020|&#8224;)?,?)+', text)
    while m is not None:
        refnrs = re.findall('(#([0-9]+)(\u2020|&#8224;)?)', m.group(0))
        result += text[:m.start()] + m.group(1) + \
                  '<REFNR>' + ','.join(map(itemgetter(1), refnrs)) + '</REFNR>'
        text = text[m.end():]
        m = re.search('(^|[^&])(#([0-9]+)(\u2020|&#8224;)?,?)+', text)
    result += text
    return result


def parse_skvr_refs(elem: ET.Element) -> ET.Element:
    '''
    Parse the contents of the <REFS> tag if it is provided
    as one text node. E.g. the following:
 
      <REFS>
        #1 first footnote
        #2 second footnote
      </REFS>

    is converted to:

      <REFS>
        <REF nr="1">first footnote</REF>
        <REF nr="2">second footnote</REF>
      </REFS>
    '''
    pat = re.compile('^\s*#([0-9]+) ?')
    cur_refnr, cur_reftext = None, ''
    for line in elem_content_to_str(elem).split('\n'):
        m = pat.match(line)
        if m is not None:
            if cur_reftext.strip():
                yield cur_refnr, cur_reftext.strip()
            cur_refnr, cur_reftext = m.group(1), line[m.end():].rstrip()
        else:
            cur_reftext += '\n' + line.rstrip()
    if cur_reftext.strip():
        yield cur_refnr, cur_reftext.strip()


# FIXME deprecated -- should be removed if unused
def parse_elem_content_to_string(poem_id: str, elem: ET.Element) -> str:
    """Parse the contents of an XML element that should not have structural children into a string. 

    The element can have markup XML within it though.

    Args:
        poem_id (str): the poem id for the poem this element is a part of (used here only for logging)
        elem (xml.etree.ElementTree.Element): the XML element to parse
    Returns:
        string: the content of the element parsed as a string
    """
    content = ""
    if elem.text is not None:
        content += elem.text
    for ce in elem:
        content += parse_markup_elem_to_string(poem_id, ce, elem,content)
    if elem.tail is not None:
        content += elem.tail
    return content


# FIXME deprecated -- should be removed if unused
def parse_markup_elem_to_string(poem_id: str, elem: ET.Element, parent_elem: ET.Element, preceding_content: str) -> str:
    """Parse a markup XML element that should not have structural children into a string. 

    The element can have other markup XML within it though.

    Args:
        poem_id (str): the poem id for the poem this element is a part of (used here only for logging)
        elem (xml.etree.ElementTree.Element): the XML element to parse
        parent_elem (xml.etree.ElementTree.Element): the parent element of what we're parsing (used here only for logging)
        preceding_content (str): preceding content. Used to intelligently squash double spacing in the presence of dropped PAG elements
    Returns:
        string: the element parsed as a string
    """

    marker = ""
    if elem.tag == "REFNR":  # note reference number
        marker = "#"
    elif elem.tag == "REFR":  # within-verse refrain
        marker = "$"
    elif elem.tag == "MRKSNR":  # later note reference number already has * in the content, so not added
        marker = ""
    elif elem.tag == "U":  # underline
        marker = "_"
    elif elem.tag == "PAG": # within-verse PAGE information is currently skipped. Line-level PAGE information is retained though.
        logging.debug("Skipping inline "+ET.tostring(elem, encoding="unicode")+" in "+ET.tostring(parent_elem, encoding="unicode"))
        if elem.tail is not None:
            if len(preceding_content)>0 and preceding_content[-1]==" " and elem.tail[0]==" ": # Eat possible double spacing resulting from PAG elements
                if elem.tail==" ":
                    return ""
                else:
                    return elem.tail[1:]
            else:
                return elem.tail
        else:
            return ""
    elif elem.tag == "I":
        marker = "@"
    elif elem.tag == "H":
        marker = "$"
    elif elem.tag == "SUP":
        marker = '^'
    elif elem.tag == "KA":
        marker = '°'
    elif elem.tag == "SMALLCAPS":
        marker = '¨'
    elif elem.tag == "SUB":
        marker = 'ˇ'
    elif elem.tag == "FR":
        marker = '€'
    else:
        logging.error(
            "Element "+elem.tag+" unexpectedly has children when parsing poem "+poem_id+": "+ET.tostring(parent_elem, encoding="unicode"))
    content = marker
    if elem.text is not None:
        content += elem.text
    elif len(elem) == 0:
        logging.warning(
            "Element "+elem.tag+" unexpectedly empty when parsing poem "+poem_id+": "+ET.tostring(parent_elem, encoding="unicode"))
    for ce in elem:
        content += parse_markup_elem_to_string(poem_id, ce, elem,content)
    if elem.tail is not None:
        content += elem.tail
    content += marker
    return content

# %%


# FIXME deprecated -- should be removed if unused
def parse_meta(poem_id: str, meta_xml: ET.Element, out: _csv.writer) -> None:
    """Parse META XML into CSV.

    Args:
        poem_id (str): the poem id for the poem this META XML is associated with
        meta_xml (xml.etree.ElementTree.Element): the META XML element to parse
        out (csv.writer): A csv writer to output parsed rows to
    """

    for elem in meta_xml:
        # informant information has structured subelements in Regilaul
        if elem.tag == "INF" or elem.tag == "YHT_ANDMED":
            content = ""
            if elem.text is not None:
                content += elem.text
            for ce in elem:
                if ce.tag == "ELUL" or ce.tag == "NIMI" or ce.tag == "LOC" or ce.tag == "TMP" or ce.tag == "REF" or ce.tag == "COL":
                    cecontent = parse_elem_content_to_string(poem_id, ce)
                    out.writerow(
                        [poem_id, elem.tag+"_"+ce.tag, cecontent.strip()])
                    content += cecontent
                else:
                    content += parse_markup_elem_to_string(poem_id, ce, elem,content)
            if elem.tail is not None:
                content += elem.tail
            out.writerow([poem_id, elem.tag, content.strip()])
        else:
            out.writerow([poem_id, elem.tag, parse_elem_content_to_string(
                poem_id, elem).strip()])

# %%


# FIXME deprecated -- should be removed if unused
def parse_ref(poem_id: str, row: int, ref_xml: ET.Element, out) -> None:
    """Parse a single REF XML into CSV.

    Args:
        poem_id (str): the poem id for the poem this REF XML is associated with
        row (int): row number
        ref_xml (xml.etree.ElementTree.Element): the REF XML element to parse
        out (csv.writer): A csv writer to output parsed row to
    """
    out.writerow([poem_id, row, ref_xml.tag,
                  parse_elem_content_to_string(poem_id, ref_xml).strip()])


# FIXME deprecated -- should be removed if unused
def parse_refs(poem_id: str, refs_xml: ET.Element, out) -> None:
    """Parse REFS XML into CSV.

    Args:
        poem_id (str): the poem id for the poem this REFS XML is associated with
        refs_xml (xml.etree.ElementTree.Element): the REFS XML element to parse
        out (csv.writer): A csv writer to output parsed rows to
    """
    row = 1
    for elem in refs_xml:
        parse_ref(poem_id, row, elem, out)
        row = row + 1

# %%


# FIXME deprecated -- should be removed if unused
def parse_text_element(poem_id: str, row: int, elem: ET.Element, out, parent: str = None):
    """Parse an XML element in TEXT that can have multiple structural children. 

    If an element has children, the parent affects the naming of child verse types, 
    which have the parent element type prepended to them.

    Args:
        poem_id (str): the poem id for the poem this REFS XML is associated with
        row (int)): current row number
        elem (xml.etree.ElementTree.Element): the XML element to parse
        out (csv.writer): A csv writer to output parsed rows to
        parent (str, optional): The name of the current parent element if there is one. Defaults to None.

    Returns:
        int: current row number after any additional rows have been emitted
    """
    content = ""
    if elem.text is not None:
        content += elem.text
    for ce in elem:
        if ce.tag == "RREFR" or ce.tag == "V" or ce.tag == "CPT":
            row = parse_text_element(poem_id, row, ce, out, elem.tag)
        else:
            content += parse_markup_elem_to_string(poem_id, ce, elem,content)
    if content != "" or elem.tag == "TYHI":
        tag = elem.tag
        if parent is not None:
            tag = parent + "_" + tag
        out.writerow([poem_id, row, tag, content.rstrip()])
        return row + 1
    elif len(elem) == 0:
        logging.warning("Element parsed as empty for poem "+poem_id+": " +
                        ET.tostring(elem, encoding="unicode"))
    return row


# FIXME deprecated -- should be removed if unused
def parse_text(poem_id: str, text_xml: ET.Element, out: _csv.writer) -> None:
    """Parse TEXT XML into CSV.

    Args:
        poem_id (str): the poem id for the poem this TEXT XML is associated with
        text_xml (xml.etree.ElementTree.Element): the TEXT XML element to parse
        out (csv.writer): A csv writer to output parsed rows to
    """
    row = 1
    for elem in text_xml:
        if elem.tag!="PAG":
            row = parse_text_element(poem_id, row, elem, out)

# %%
