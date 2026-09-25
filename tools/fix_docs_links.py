#!/usr/bin/env python3
"""Fix broken backtick references in docs/ by adding proper subdir prefixes."""

import os
import re
from pathlib import Path

ROOT = Path("/home/sugimoto/llmagent/docs")

def build_doc_map(root):
    """Build a map from doc name (without .md) to relative path."""
    doc_map = {}
    for dirpath, _, filenames in os.walk(root):
        if '.git' in dirpath:
            continue
        for fname in filenames:
            if not fname.endswith('.md'):
                continue
            rel_path = Path(dirpath) / fname
            name_without_ext = fname[:-3]  # remove .md
            doc_map[name_without_ext] = str(rel_path)
    return doc_map

doc_map = build_doc_map(ROOT)

updated_count = 0
files_with_changes = []

for dirpath, _, filenames in os.walk(ROOT):
    if '.git' in dirpath:
        continue
    for fname in filenames:
        if not fname.endswith('.md'):
            continue
        fpath = Path(dirpath) / fname
        
        try:
            content = fpath.read_text(encoding='utf-8')
        except Exception:
            continue
        
        original = content
        changes = []
        
        # Fix backtick references: `xxx` -> `subdir/xxx.md` where xxx is a known doc name
        def fix_backtick(m):
            ref = m.group(1)
            # Skip empty or invalid refs
            if not ref or '.' in ref or '/' in ref:
                return m.group(0)
            # Check if this ref exists as a doc name
            if ref in doc_map:
                changes.append(f"backtick:{ref}->{doc_map[ref]}")
                return f"`{doc_map[ref]}`"
            return m.group(0)
        
        content = re.sub(r'`([a-z0-9_-]+)`', fix_backtick, content)
        
        # Also fix markdown links that point to wrong paths
        def fix_link(m):
            text = m.group(1)
            url = m.group(2)
            # Skip absolute URLs
            if url.startswith('http://') or url.startswith('https://'):
                return m.group(0)
            # Skip anchor-only links like #section-name
            if url.startswith('#'):
                return m.group(0)
            # Extract filename from URL (after last /)
            basename = url.split('/')[-1]
            name_without_ext = basename.replace('.md', '')
            # If it's a known doc name but missing subdir prefix
            if name_without_ext in doc_map and not url.startswith('/'):
                target_path = doc_map[name_without_ext]
                # Only fix if the current file doesn't have the right path
                if url != target_path:
                    changes.append(f"link:{url}->{target_path}")
                    return f"[{text}]({target_path})"
            return m.group(0)
        
        content = re.sub(r'\[([^\]]+)\]\(([^)]*)\)', fix_link, content)
        
        if changes:
            fpath.write_text(content, encoding='utf-8')
            updated_count += 1
            files_with_changes.append(str(fpath))

print(f"Updated {updated_count} files:")
for fp in files_with_changes:
    print(f"  {fp}")
