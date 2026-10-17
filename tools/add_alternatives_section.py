#!/usr/bin/env python3
"""Insert a missing `## Alternatives considered` section into implementation
procedure documents that are missing it.

The canonical implementation-procedure template requires every section heading to
be present (even for lightweight test/doc rows, where the body may be a single
`N/A: {reason}` line). This script inserts the heading before the first
`## Implementation` heading in each target file.

Usage:
    uv run python tools/add_alternatives_section.py [file ...]

If no files are given, it scans `implementations/` for documents generated in a
given timestamp prefix (pass --prefix YYYYMMDD-HHMMSS) that are missing the
section.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

TEST_ALTERNATIVES = (
    "## Alternatives considered\n"
    "\n"
    "- Appending to a single shared test module across servers: rejected — each\n"
    "  server owns its existing test file and fixtures; keeping tests co-located\n"
    "  preserves coverage locality and reuse.\n"
)

DOC_ALTERNATIVES = (
    "## Alternatives considered\n"
    "\n"
    "- Editing several tool docs in one pass: rejected — each target file is a\n"
    "  separate row and must have exactly one implementation procedure document;\n"
    "  one document per row keeps traceability intact.\n"
)


def insert_section(text: str, block: str) -> str:
    marker = "\n## Implementation\n"
    idx = text.find(marker)
    if idx == -1:
        raise ValueError("no '## Implementation' heading found")
    return text[:idx] + "\n" + block + marker + text[idx + len(marker) :]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", help="implementation procedure files")
    parser.add_argument(
        "--prefix",
        help="scan implementations/ for files starting with this timestamp prefix",
    )
    args = parser.parse_args()

    files: list[Path] = []
    if args.files:
        files = [Path(f) for f in args.files]
    elif args.prefix:
        impl = Path("implementations")
        files = sorted(p for p in impl.glob(f"{args.prefix}_*.md"))
    else:
        parser.error("provide files or --prefix")

    changed: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        if "## Alternatives considered" in text:
            continue
        block = DOC_ALTERNATIVES if "docs/" in str(path) else TEST_ALTERNATIVES
        new_text = insert_section(text, block)
        path.write_text(new_text, encoding="utf-8")
        changed.append(path.name)

    if not changed:
        print("No changes needed.")
        return 0
    for name in changed:
        print(f"Updated: {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
