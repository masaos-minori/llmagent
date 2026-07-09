#!/usr/bin/env python3
"""Split 01_overview-arch.md into 3 files at H2/H3 boundaries."""

import re

def add_frontmatter(content, title, category="overview"):
    """Add YAML Front Matter to content."""
    fm = f"""---
title: "{title}"
category: {category}
tags:
  - overview
  - architecture
related:
  - 01_overview.md
  - 01_overview-files.md
source:
  - 01_overview-arch.md
---

"""
    return fm + content

def add_tail(content):
    """Add Related Documents and Keywords sections."""
    tail = f"""
## Related Documents

- `01_overview.md`
- `01_overview-files.md`

## Keywords

architecture
process
pipeline
feature
implementation
"""
    return content.rstrip() + tail

# Read original file
with open("docs/01_overview-arch.md", "r") as f:
    content = f.read()

# Split at H2 boundaries first
h2_pattern = r'^#{2} .+$'
sections = []
current_section = None
current_lines = []

for line in content.split('\n'):
    m = re.match(h2_pattern, line)
    if m:
        if current_section:
            sections.append((current_section, '\n'.join(current_lines)))
        current_section = m.group(0)
        current_lines = [line]
    else:
        current_lines.append(line)

if current_section:
    sections.append((current_section, '\n'.join(current_lines)))

print(f"Found {len(sections)} H2 sections:")
for sec_name, sec_content in sections:
    lines = sec_content.count('\n') + 1
    print(f"  - {sec_name}: {lines} lines")

# File 1: Section 1 + Section 2.1 (プロセス構成)
file1_content = ""
for sec_name, sec_content in sections:
    if "1. 概要" in sec_name:
        file1_content += sec_content + "\n\n"
    elif "2. アーキテクチャ" in sec_name:
        # Further split at H3 boundaries
        h3_pattern = r'^#{3} .+$'
        sub_sections = []
        current_sub = None
        current_sub_lines = []
        for line in sec_content.split('\n'):
            m = re.match(h3_pattern, line)
            if m:
                if current_sub:
                    sub_sections.append((current_sub, '\n'.join(current_sub_lines)))
                current_sub = m.group(0)
                current_sub_lines = [line]
            else:
                current_sub_lines.append(line)
        if current_sub:
            sub_sections.append((current_sub, '\n'.join(current_sub_lines)))
        
        for sub_name, sub_content in sub_sections:
            if "2.1" in sub_name:
                file1_content += sub_content + "\n\n"

file1_title = "概要・アーキテクチャ（プロセス構成）"
file1_content = add_frontmatter(file1_content, file1_title)
file1_content = add_tail(file1_content)

with open("docs/01_overview-arch-process.md", "w") as f:
    f.write(file1_content)

print(f"\nCreated docs/01_overview-arch-process.md ({len(file1_content)} bytes)")

# File 2: Section 2.2 + 2.3 (パイプライン)
file2_content = ""
for sec_name, sec_content in sections:
    if "2. アーキテクチャ" in sec_name:
        h3_pattern = r'^#{3} .+$'
        sub_sections = []
        current_sub = None
        current_sub_lines = []
        for line in sec_content.split('\n'):
            m = re.match(h3_pattern, line)
            if m:
                if current_sub:
                    sub_sections.append((current_sub, '\n'.join(current_sub_lines)))
                current_sub = m.group(0)
                current_sub_lines = [line]
            else:
                current_sub_lines.append(line)
        if current_sub:
            sub_sections.append((current_sub, '\n'.join(current_sub_lines)))
        
        for sub_name, sub_content in sub_sections:
            if "2.2" in sub_name or "2.3" in sub_name:
                file2_content += sub_content + "\n\n"

file2_title = "概要・アーキテクチャ（パイプライン）"
file2_content = add_frontmatter(file2_content, file2_title)
file2_content = add_tail(file2_content)

with open("docs/01_overview-arch-pipelines.md", "w") as f:
    f.write(file2_content)

print(f"Created docs/01_overview-arch-pipelines.md ({len(file2_content)} bytes)")

# File 3: Section 2.4 + 2.5 (機能・実装)
file3_content = ""
for sec_name, sec_content in sections:
    if "2. アーキテクチャ" in sec_name:
        h3_pattern = r'^#{3} .+$'
        sub_sections = []
        current_sub = None
        current_sub_lines = []
        for line in sec_content.split('\n'):
            m = re.match(h3_pattern, line)
            if m:
                if current_sub:
                    sub_sections.append((current_sub, '\n'.join(current_sub_lines)))
                current_sub = m.group(0)
                current_sub_lines = [line]
            else:
                current_sub_lines.append(line)
        if current_sub:
            sub_sections.append((current_sub, '\n'.join(current_sub_lines)))
        
        for sub_name, sub_content in sub_sections:
            if "2.4" in sub_name or "2.5" in sub_name:
                file3_content += sub_content + "\n\n"

file3_title = "概要・アーキテクチャ（機能・実装）"
file3_content = add_frontmatter(file3_content, file3_title)
file3_content = add_tail(file3_content)

with open("docs/01_overview-arch-features.md", "w") as f:
    f.write(file3_content)

print(f"Created docs/01_overview-arch-features.md ({len(file3_content)} bytes)")

# Update cross-references in all files
files_to_update = [
    "docs/01_overview.md",
    "docs/01_overview-files.md",
    "docs/01_overview-arch-process.md",
    "docs/01_overview-arch-pipelines.md",
    "docs/01_overview-arch-features.md",
]

old_ref = "[`01_overview-arch.md`](01_overview-arch.md)"
new_refs = {
    "docs/01_overview.md": "[`01_overview-arch-process.md`](01_overview-arch-process.md), [`01_overview-arch-pipelines.md`](01_overview-arch-pipelines.md), [`01_overview-arch-features.md`](01_overview-arch-features.md)",
    "docs/01_overview-files.md": "[`01_overview-arch-process.md`](01_overview-arch-process.md), [`01_overview-arch-pipelines.md`](01_overview-arch-pipelines.md), [`01_overview-arch-features.md`](01_overview-arch-features.md)",
    "docs/01_overview-arch-process.md": "[`01_overview-arch-pipelines.md`](01_overview-arch-pipelines.md), [`01_overview-arch-features.md`](01_overview-arch-features.md)",
    "docs/01_overview-arch-pipelines.md": "[`01_overview-arch-process.md`](01_overview-arch-process.md), [`01_overview-arch-features.md`](01_overview-arch-features.md)",
    "docs/01_overview-arch-features.md": "[`01_overview-arch-process.md`](01_overview-arch-process.md), [`01_overview-arch-pipelines.md`](01_overview-arch-pipelines.md)",
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
