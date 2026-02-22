#!/usr/bin/env python3
"""Fix indentation in the runoregi_pages_combined.json file.

The issue is that level 2 categories (e.g., "1. Epiikka") have the same
indentation as level 1. This script changes the second-level indentation
from margin-left: 0px to margin-left: 19px.
"""

import json
import re

def fix_indentation(content):
    """Fix the indentation for level 2 categories in the HTML content."""
    
    # The pattern matches the second-level <summary> tags that have margin-left: 0px
    # Level 2 summaries are indented with 4 spaces (    <details>)
    # We need to change their margin-left from 0px to 19px
    
    # Pattern: 4 spaces + <details> + newline + 4 spaces + <summary...margin-left: 0px...>
    # This targets second-level details/summary elements
    pattern = r'(    <details>\n    <summary style="display: list-item; margin-left:) 0px(;">)'
    replacement = r'\g<1>19px\2'
    
    fixed_content = re.sub(pattern, replacement, content)
    
    return fixed_content

def main():
    input_file = 'elias-1848/data/raw/skvr/runoregi_pages_combined.json'
    output_file = 'elias-1848/data/raw/skvr/runoregi_pages_combined.json'
    
    # Read the JSON file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Process each entry
    for entry in data:
        if entry.get('view') == 'search_idx' and entry.get('position') == 'left':
            # The content is a list of strings, join them to process
            content = ''.join(entry['content'])
            
            # Fix the indentation
            fixed_content = fix_indentation(content)
            
            # Split back into list (the original format)
            entry['content'] = [fixed_content]
            
            print(f"Fixed indentation in entry: {entry.get('title', 'Unknown')}")
    
    # Write the modified JSON back
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Successfully updated {output_file}")

if __name__ == '__main__':
    main()
