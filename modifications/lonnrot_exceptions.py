import os
from lxml import etree

# Assign the path to the XML file
xml_file = "kr01-53.xml"
output_file = "lonnrot_exceptions.xml"

# Define the <TEOS> values to keep
keepers = {
    "Elias Lönnrot : Suomen Kansan arwoituksia ynnä 189 Wiron arwoituksen kanssa",
    "Suomen Kansan Muinaisia Loitsurunoja toimittanut Elias Lönnrot"
}

try:
    # Parse the XML file
    tree = etree.parse(xml_file)
    root = tree.getroot()

    # Filter <ITEM> elements
    filtered_items = []
    for item in root.findall(".//ITEM"):
        teos_element = item.find(".//TEOS")
        if teos_element is not None and teos_element.text and teos_element.text.strip() in keepers:
            filtered_items.append(item)

    # Create a new XML tree with the filtered items
    new_root = etree.Element(root.tag)
    for item in filtered_items:
        new_root.append(item)

    # Write the filtered XML to a new file
    new_tree = etree.ElementTree(new_root)
    new_tree.write(output_file, pretty_print=True, encoding="utf-8", xml_declaration=True)

    print(f"Filtered XML file has been saved to: {output_file}")

except Exception as e:
    print(f"Error processing file {xml_file}: {e}")
