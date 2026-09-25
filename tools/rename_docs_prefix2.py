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

# Build mapping of old filenames to new filenames
renamed_files = {}
AGENT_DIR = DOCS_DIR / "23_agent"
for fpath in AGENT_DIR.iterdir():
    if not fpath.is_file():
        continue
    name = fpath.name
    m = re.match(r'^(\d{2})_(agent_.+)$', name)
    if m:
        renamed_files[name] = m.group(2)

print(f"Renamed files ({len(renamed_files)}):")
for k, v in sorted(renamed_files.items()):
    print(f"  {k} -> {v}")

updated_count = 0
files_with_changes = []

for fpath in all_md_files:
    try:
        content = fpath.read_text(encoding='utf-8')
    except Exception:
        continue
    
    original = content
    changed = False
    
    # Replace file path references: 05_agent_xxx.md -> agent_xxx.md
    for old_name, new_name in renamed_files.items():
        # In backticks: `05_agent_xxx.md`
        pattern1 = rf'(`){re.escape(old_name)}(.*)(`)'
        replacement1 = rf'\1{new_name}\2\3'
        if re.search(pattern1, content):
            content = re.sub(pattern1, replacement1, content)
            changed = True
        
        # In links: [text](05_agent_xxx.md) or [[05_agent_xxx]]
        pattern2 = rf'\((\./)?{re.escape(old_name)}\)'
        replacement2 = rf'(\1){new_name}'
        if re.search(pattern2, content):
            content = re.sub(pattern2, replacement2, content)
            changed = True
        
        pattern3 = rf'\[\[{re.escape(old_name)}\]\]'
        replacement3 = f'[[{new_name}]]'
        if re.search(pattern3, content):
            content = re.sub(pattern3, replacement3, content)
            changed = True
        
        # Plain text reference: 05_agent_xxx (without .md extension)
        pattern4 = rf'\b{re.escape(old_name)}\b'
        if re.search(pattern4, content):
            content = re.sub(pattern4, new_name, content)
            changed = True
    
    if changed:
        fpath.write_text(content, encoding='utf-8')
        updated_count += 1
        files_with_changes.append(str(fpath))

print(f"\nUpdated {updated_count} files:")
for fp in files_with_changes:
    print(f"  {fp}")
