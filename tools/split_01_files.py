#!/usr/bin/env python3
"""Split 01_overview-files.md into 6 files at directory boundaries."""

import re

def add_frontmatter(content, title, category="overview"):
    """Add YAML Front Matter to content."""
    fm = f"""---
title: "{title}"
category: overview
tags:
  - overview
  - file-structure
related:
  - 01_overview.md
  - 01_overview-arch-process.md
source:
  - 01_overview-files.md
---

"""
    return fm + content

def add_tail(content):
    """Add Related Documents and Keywords sections."""
    tail = f"""
## Related Documents

- `01_overview.md`
- `01_overview-arch-process.md`

## Keywords

file-structure
directory
layout
configuration
scripts
shared
database
event-bus
"""
    return content.rstrip() + tail

# Read original file
with open("docs/01_overview-files.md", "r") as f:
    content = f.read()

lines = content.split('\n')

# Find all top-level directory entries by identifying lines that start with ├ or └ 
# followed by ─ or │ and then a directory name ending with /
# Top-level entries are those where the prefix doesn't contain │ immediately before ├ or └
top_level_entries = []
for i, line in enumerate(lines):
    # Match lines starting with ├ or └ (possibly preceded by spaces) followed by ─ or │ and then dirname/
    m = re.match(r'^\s*[├└][─│]\s+([\w.\-]+)/', line)
    if m:
        dirname = m.group(1)
        # Check if there's a │ immediately before ├ or └ (which would mean it's nested)
        pos = line.find(dirname)
        prefix = line[:pos]
        # If prefix contains │ right before ├ or └, it's nested
        if '│' in prefix and re.search(r'│\s*[├└]', prefix):
            continue  # Skip nested entries
        top_level_entries.append((i, dirname))
    
    # Also match /etc/conf.d/ which doesn't use box-drawing characters
    m2 = re.match(r'^/etc/conf\.d/', line)
    if m2:
        top_level_entries.append((i, 'etc-conf.d'))

print(f"Found {len(top_level_entries)} top-level directories:")
for idx, dirname in top_level_entries:
    print(f"  Line {idx}: {dirname}")

# Define sections based on top-level entries
sections = {}
current_section = None
current_start = None

for entry_idx, (line_num, dirname) in enumerate(top_level_entries):
    # Determine section for this directory
    if dirname == 'llama.cpp':
        section = 'misc'
    elif dirname == 'models':
        section = 'misc'
    elif dirname == 'rag-src':
        section = 'rag-src'
    elif dirname == 'db':
        section = 'db'
    elif dirname == 'sqlite-vec':
        section = 'misc'
    elif dirname == 'venv':
        section = 'misc'
    elif dirname == 'config':
        section = 'config'
    elif dirname == 'scripts':
        section = 'scripts'
    elif dirname == 'logs':
        section = 'misc'
    elif dirname == 'etc-conf.d':
        section = 'other'
    else:
        section = 'other'
    
    # Save previous section if exists
    if current_section and current_start is not None:
        # Get all lines from current_start to this entry
        if entry_idx + 1 < len(top_level_entries):
            end_line = top_level_entries[entry_idx + 1][0]
        else:
            end_line = len(lines)
        
        section_lines = lines[current_start:end_line]
        sections.setdefault(current_section, []).append('\n'.join(section_lines))
    
    # Start new section
    current_section = section
    current_start = line_num

# Save last section
if current_section and current_start is not None:
    section_lines = lines[current_start:]
    sections.setdefault(current_section, []).append('\n'.join(section_lines))

print(f"\nFound {len(sections)} sections:")
for sec_name, sec_lines_list in sections.items():
    total_lines = sum(len(lines.split('\n')) for lines in sec_lines_list)
    print(f"  - {sec_name}: {total_lines} lines")

# File 1: misc (llama.cpp, models, sqlite-vec, venv, logs)
file1_content = ""
for lines_str in sections.get('misc', []) + sections.get('other', []):
    file1_content += lines_str + "\n\n"

file1_title = "ファイル構成（ビルド・モデル・ランタイム）"
file1_content = add_frontmatter(file1_content, file1_title)
file1_content = add_tail(file1_content)

with open("docs/01_overview-files-misc.md", "w") as f:
    f.write(file1_content)

print(f"\nCreated docs/01_overview-files-misc.md ({len(file1_content)} bytes)")

# File 2: rag-src
file2_content = ""
for lines_str in sections.get('rag-src', []):
    file2_content += lines_str + "\n\n"

file2_title = "ファイル構成（RAG取込データ）"
file2_content = add_frontmatter(file2_content, file2_title)
file2_content = add_tail(file2_content)

with open("docs/01_overview-files-rag-src.md", "w") as f:
    f.write(file2_content)

print(f"Created docs/01_overview-files-rag-src.md ({len(file2_content)} bytes)")

# File 3: db
file3_content = ""
for lines_str in sections.get('db', []):
    file3_content += lines_str + "\n\n"

file3_title = "ファイル構成（データベース層）"
file3_content = add_frontmatter(file3_content, file3_title)
file3_content = add_tail(file3_content)

with open("docs/01_overview-files-db.md", "w") as f:
    f.write(file3_content)

print(f"Created docs/01_overview-files-db.md ({len(file3_content)} bytes)")

# File 4: config
file4_content = ""
for lines_str in sections.get('config', []):
    file4_content += lines_str + "\n\n"

file4_title = "ファイル構成（設定ファイル）"
file4_content = add_frontmatter(file4_content, file4_title)
file4_content = add_tail(file4_content)

with open("docs/01_overview-files-config.md", "w") as f:
    f.write(file4_content)

print(f"Created docs/01_overview-files-config.md ({len(file4_content)} bytes)")

# File 5: scripts
file5_content = ""
for lines_str in sections.get('scripts', []):
    file5_content += lines_str + "\n\n"

file5_title = "ファイル構成（スクリプト・パッケージ）"
file5_content = add_frontmatter(file5_content, file5_title)
file5_content = add_tail(file5_content)

with open("docs/01_overview-files-scripts.md", "w") as f:
    f.write(file5_content)

print(f"Created docs/01_overview-files-scripts.md ({len(file5_content)} bytes)")

# File 6: other (/etc/conf.d/)
file6_content = ""
for lines_str in sections.get('other', []):
    file6_content += lines_str + "\n\n"

if file6_content:
    file6_title = "ファイル構成（その他）"
    file6_content = add_frontmatter(file6_content, file6_title)
    file6_content = add_tail(file6_content)
    
    with open("docs/01_overview-files-other.md", "w") as f:
        f.write(file6_content)
    print(f"Created docs/01_overview-files-other.md ({len(file6_content)} bytes)")
else:
    # No other section, create empty file
    file6_title = "ファイル構成（共有・イベントバス）"
    file6_content = add_frontmatter("", file6_title)
    file6_content = add_tail(file6_content)
    
    with open("docs/01_overview-files-shared.md", "w") as f:
        f.write(file6_content)
    print(f"Created docs/01_overview-files-shared.md (empty - no top-level shared/eventbus)")

# Update cross-references
files_to_update = [
    "docs/01_overview.md",
    "docs/01_overview-arch-process.md",
    "docs/01_overview-arch-pipelines.md",
    "docs/01_overview-arch-features.md",
]

old_ref = "[`01_overview-files.md`](01_overview-files.md)"
new_refs = {
    "docs/01_overview.md": "[`01_overview-files-misc.md`](01_overview-files-misc.md), [`01_overview-files-rag-src.md`](01_overview-files-rag-src.md), [`01_overview-files-db.md`](01_overview-files-db.md), [`01_overview-files-config.md`](01_overview-files-config.md), [`01_overview-files-scripts.md`](01_overview-files-scripts.md), [`01_overview-files-other.md`](01_overview-files-other.md)",
    "docs/01_overview-arch-process.md": "[`01_overview-files-misc.md`](01_overview-files-misc.md), [`01_overview-files-rag-src.md`](01_overview-files-rag-src.md), [`01_overview-files-db.md`](01_overview-files-db.md), [`01_overview-files-config.md`](01_overview-files-config.md), [`01_overview-files-scripts.md`](01_overview-files-scripts.md), [`01_overview-files-other.md`](01_overview-files-other.md)",
    "docs/01_overview-arch-pipelines.md": "[`01_overview-files-misc.md`](01_overview-files-misc.md), [`01_overview-files-rag-src.md`](01_overview-files-rag-src.md), [`01_overview-files-db.md`](01_overview-files-db.md), [`01_overview-files-config.md`](01_overview-files-config.md), [`01_overview-files-scripts.md`](01_overview-files-scripts.md), [`01_overview-files-other.md`](01_overview-files-other.md)",
    "docs/01_overview-arch-features.md": "[`01_overview-files-misc.md`](01_overview-files-misc.md), [`01_overview-files-rag-src.md`](01_overview-files-rag-src.md), [`01_overview-files-db.md`](01_overview-files-db.md), [`01_overview-files-config.md`](01_overview-files-config.md), [`01_overview-files-scripts.md`](01_overview-files-scripts.md), [`01_overview-files-other.md`](01_overview-files-other.md)",
}

for filepath in files_to_update:
    try:
        with open(filepath, "r") as f:
            content = f.read()
        new_content = content.replace(old_ref, new_refs.get(filepath, old_ref))
        if new_content != content:
            with open(filepath, "w") as f:
                f.write(new_content)
            print(f"Updated references in {filepath}")
    except FileNotFoundError:
        pass
