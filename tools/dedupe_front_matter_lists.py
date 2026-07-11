#!/usr/bin/env python3
"""Remove duplicate entries from YAML Front Matter list fields (tags/related/source)
in docs/*.md, preserving first-occurrence order. Edits only the Front Matter block;
body content is untouched.
"""

from __future__ import annotations

import glob
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"
LIST_FIELDS = ("tags", "related", "source")


def dedupe_front_matter(content: str) -> tuple[str, bool]:
    if not content.startswith("---"):
        return content, False
    end = content.find("\n---", 3)
    if end == -1:
        return content, False
    fm_lines = content[3:end].split("\n")
    changed = False
    out_lines: list[str] = []
    current_field = None
    seen: set[str] = set()
    for line in fm_lines:
        field_match = re.match(r"^(\w+):\s*$", line)
        item_match = re.match(r"^(\s+)-\s+(.+)$", line)
        if field_match:
            current_field = field_match.group(1)
            seen = set()
            out_lines.append(line)
            continue
        if item_match and current_field in LIST_FIELDS:
            value = item_match.group(2).strip()
            if value in seen:
                changed = True
                continue
            seen.add(value)
            out_lines.append(line)
            continue
        current_field = None
        out_lines.append(line)
    new_fm = "\n".join(out_lines)
    return content[:3] + new_fm + content[end:], changed


def main() -> None:
    changed_files = 0
    for fp in sorted(glob.glob(str(DOCS_DIR / "*.md"))):
        path = Path(fp)
        content = path.read_text(encoding="utf-8")
        new_content, changed = dedupe_front_matter(content)
        if changed:
            path.write_text(new_content, encoding="utf-8")
            changed_files += 1
            print(f"deduped {path.name}")
    print(f"total files changed: {changed_files}")


if __name__ == "__main__":
    main()
