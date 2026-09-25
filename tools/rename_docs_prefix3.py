#!/usr/bin/env python3
"""Fix remaining 05_agent_ -> agent_ references in docs/."""

import os
import re
from pathlib import Path

DOCS_DIR = Path("/home/sugimoto/llmagent/docs")

def find_all_md_files(root):
    result = []
    for dirpath, _, filenames in os.walk(root):
        if '.git' in dirpath:
            continue
        for fname in filenames:
            if fname.endswith('.md'):
                result.append(Path(dirpath) / fname)
    return result

all_md_files = find_all_md_files(DOCS_DIR)

updated_count = 0
files_with_changes = []

for fpath in all_md_files:
    try:
        content = fpath.read_text(encoding='utf-8')
    except Exception:
        continue
    
    original = content
    changed = False
    
    # Replace all occurrences of 05_agent_ with agent_ in file path contexts
    # But skip historical/deleted file references (TODO comments about deleted files)
    
    # Skip lines that reference deleted files
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        # Check if this line references a deleted file
        if 'was deleted' in line.lower() or 'deleted' in line.lower():
            # Keep as-is for deleted file references
            new_lines.append(line)
            continue
        
        # Replace 05_agent_ with agent_ in this line
        new_line = line.replace('05_agent_', 'agent_')
        if new_line != line:
            changed = True
        new_lines.append(new_line)
    
    if changed:
        content = '\n'.join(new_lines)
        fpath.write_text(content, encoding='utf-8')
        updated_count += 1
        files_with_changes.append(str(fpath))

print(f"Updated {updated_count} files:")
for fp in files_with_changes:
    print(f"  {fp}")
