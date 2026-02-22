#!/usr/bin/env python3
"""Import the index hierarchy content into the database."""

import json
import subprocess

# Read the JSON file
with open('elias-1848/data/raw/skvr/runoregi_pages_combined.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find the index hierarchy entry
for entry in data:
    if entry.get('view') == 'search_idx' and entry.get('position') == 'left' and entry.get('title') == 'Index hierarchy':
        content = ''.join(entry['content'])
        helptext = '\n'.join(entry.get('helptext', []))
        
        # Escape for SQL
        content_escaped = content.replace("'", "''")
        helptext_escaped = helptext.replace("'", "''")
        
        # Run mysql command to insert
        sql = f"INSERT INTO runoregi_pages (b_id, content, helptext) VALUES (3, '{content_escaped}', '{helptext_escaped}');"
        
        # Use mysql command
        cmd = f"mysql -h localhost -u jakob -p3a3mvo elias -e \"{sql}\""
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Successfully inserted index hierarchy: {len(content)} chars")
        else:
            print(f"Error: {result.stderr}")
        
        break
