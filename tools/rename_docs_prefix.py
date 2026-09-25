#!/usr/bin/env python3
"""Rename docs/23_agent/ files from NN_agent_ prefix to agent_ prefix and update links."""

import os
import re
from pathlib import Path

DOCS_DIR = Path("/home/sugimoto/llmagent/docs")
AGENT_DIR = DOCS_DIR / "23_agent"

# Step 1: Rename files in docs/23_agent/
print("=== Step 1: Renaming files ===")
renamed_files = {}  # old_name -> new_name

for fpath in sorted(AGENT_DIR.iterdir()):
    if not fpath.is_file():
        continue
    name = fpath.name
    # Match pattern: NN_agent_<rest>.md
    m = re.match(r'^(\d{2})_(agent_.+)$', name)
    if m:
        nn_part = m.group(1)
        rest = m.group(2)
        new_name = f"{rest}"
        new_path = AGENT_DIR / new_name
        print(f"  {name} -> {new_name}")
        renamed_files[name] = new_name
        fpath.rename(new_path)

print(f"\nRenamed {len(renamed_files)} files\n")

# Step 2: Update all references across the project
print("=== Step 2: Updating references ===")

def find_all_md_files(root):
    """Find all .md files recursively, excluding .git."""
    result = []
    for dirpath, _, filenames in os.walk(root):
        if '.git' in dirpath:
            continue
        for fname in filenames:
            if fname.endswith('.md'):
                result.append(Path(dirpath) / fname)
    return result

# Collect all md files to check (project-wide, excluding .git)
all_md_files = find_all_md_files("/home/sugimoto/llmagent")

# Build a set of old filenames for quick lookup
old_names_set = set(renamed_files.keys())

# Also build mapping for link updates: old_filename -> new_filename
link_remap = {}
for old_name, new_name in renamed_files.items():
    # For links like [text](NN_agent_xxx.md) or [[NN_agent_xxx]] etc.
    link_remap[old_name] = new_name

# Process each file
updated_count = 0
files_with_changes = []

for fpath in all_md_files:
    try:
        content = fpath.read_text(encoding='utf-8')
    except Exception:
        continue
    
    original = content
    changed = False
    
    for old_name, new_name in renamed_files.items():
        # Replace in markdown links: [text](NN_agent_xxx.md)
        pattern1 = rf'\((\./)?{re.escape(old_name)}\)'
        replacement1 = rf'(\1){new_name}'
        if re.search(pattern1, content):
            content = re.sub(pattern1, replacement1, content)
            changed = True
        
        # Replace in wiki-style links: [[NN_agent_xxx]]
        pattern2 = rf'\[\[{re.escape(old_name)}\]\]'
        replacement2 = f'[[{new_name}]]'
        if re.search(pattern2, content):
            content = re.sub(pattern2, replacement2, content)
            changed = True
        
        # Replace in plain text references (e.g., "see NN_agent_xxx.md")
        pattern3 = rf'\b{re.escape(old_name)}\b'
        if re.search(pattern3, content):
            content = re.sub(pattern3, new_name, content)
            changed = True
    
    if changed:
        fpath.write_text(content, encoding='utf-8')
        updated_count += 1
        files_with_changes.append(str(fpath))

print(f"Updated {updated_count} files with link changes:")
for fp in files_with_changes:
    print(f"  {fp}")

print("\nDone!")
