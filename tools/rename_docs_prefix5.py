#!/usr/bin/env python3
"""Update all 24_eventbus_ -> eventbus_ references in markdown links across the project."""

import os
import re
from pathlib import Path

ROOT = Path("/home/sugimoto/llmagent")

def find_all_md_files(root):
    result = []
    for dirpath, _, filenames in os.walk(root):
        if '.git' in dirpath:
            continue
        for fname in filenames:
            if fname.endswith('.md'):
                result.append(Path(dirpath) / fname)
    return result

all_md_files = find_all_md_files(ROOT)

updated_count = 0
files_with_changes = []

for fpath in all_md_files:
    try:
        content = fpath.read_text(encoding='utf-8')
    except Exception:
        continue
    
    original = content
    changed = False
    
    # Pattern 1: Markdown links [text](24_eventbus_xxx.md)
    pattern1 = r'\[([^\]]+)\]\(([^)]*24_eventbus_[^)]*)\)'
    if re.search(pattern1, content):
        content = re.sub(pattern1, lambda m: f"[{m.group(1)}]({re.sub(r'\b24_eventbus_', 'eventbus_', m.group(2))})", content)
        changed = True
    
    # Pattern 2: Wiki-style links [[24_eventbus_xxx]]
    pattern2 = r'\[\[(24_eventbus_[^\]]+)\]\]'
    if re.search(pattern2, content):
        content = re.sub(pattern2, lambda m: f"[[{re.sub(r'\b24_eventbus_', 'eventbus_', m.group(1))}]]", content)
        changed = True
    
    # Pattern 3: Backtick references `24_eventbus_xxx`
    pattern3 = r'`(24_eventbus_[^`]+)`'
    if re.search(pattern3, content):
        content = re.sub(pattern3, lambda m: f"`{re.sub(r'\b24_eventbus_', 'eventbus_', m.group(1))}`", content)
        changed = True
    
    # Pattern 4: Plain text 24_eventbus_ not in any special context
    pattern4 = r'\b24_eventbus_(\d+_\w+\.md)'
    if re.search(pattern4, content):
        content = re.sub(pattern4, r'eventbus_\1', content)
        changed = True
    
    if changed:
        fpath.write_text(content, encoding='utf-8')
        updated_count += 1
        files_with_changes.append(str(fpath))

print(f"Updated {updated_count} files:")
for fp in files_with_changes:
    print(f"  {fp}")
