# Python Script: filter_items_by_year.py
import argparse
from lxml import etree
import os

def filter_items_by_year(input_file, output_file, max_year):
    
    output_dir = os.path.dirname(output_file)
    os.makedirs(output_dir, exist_ok=True)

    exceptions_log_path = os.path.join(output_dir, "filtering_exceptions.log")
    summary_log_path = os.path.join(output_dir, "filtering.log")

    total_items = 0
    included_items = 0

    with open(exceptions_log_path, "a", encoding="utf-8") as exceptions_log:
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.parse(input_file, parser)
        root = tree.getroot()

        # Iterate over <ITEM> elements
        for item in root.xpath(".//ITEM"):
            total_items += 1
            year = item.get("y")
            if year is not None:
                year = year.strip()  # Remove extra whitespace
                if year.isdigit():
                    year = int(year)
                    if year <= max_year:
                        included_items += 1
                        continue  # Keep this <ITEM>
                else:
                    exceptions_log.write(f"{input_file}: Invalid year format '{year}' in ITEM {item.get('nro')}\n")
            else:
                exceptions_log.write(f"{input_file}: Missing 'y' attribute in ITEM {item.get('nro')}\n")

            # Remove <ITEM> if invalid or exceeds the limit
            parent = item.getparent()
            parent.remove(item)

        # Handle case where all <ITEM>s are omitted
        if included_items == 0:
            exceptions_log.write(f"{input_file}: No valid <ITEM> elements remaining after filtering.\n")

        # Save the filtered XML if any items remain
        if included_items > 0:
            tree.write(output_file, pretty_print=True, encoding="utf-8", xml_declaration=True)

    # Write summary log
    inclusion_percentage = (included_items / total_items * 100) if total_items > 0 else 0
    with open(summary_log_path, "a", encoding="utf-8") as summary_log:
        summary_log.write(f"{input_file}: Processed {total_items} items, included {included_items} items, "
                          f"{inclusion_percentage:.2f}% included.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Filter XML items by year.")
    parser.add_argument("input_file", help="Path to the input XML file.")
    parser.add_argument("output_file", help="Path to the output XML file.")
    parser.add_argument("--max-year", type=int, required=True, help="Maximum year to retain in <ITEM> elements.")

    args = parser.parse_args()
    filter_items_by_year(args.input_file, args.output_file, args.max_year)
