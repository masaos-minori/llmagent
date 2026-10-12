"""check_docs_japanese.py — List docs/*.md files that contain Japanese characters.

`skills/DESIGN.md` Output language requires every file under `docs/` to be written in
English. Exits 1 when any file contains Hiragana, Katakana, or CJK ideographs, so the
check can gate a hook or CI job; exits 0 when none is found.

Usage:
    python tools/check_docs_japanese.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"

# Hiragana, Katakana, and common Kanji ranges
_JAPANESE_RE = re.compile(r"[぀-ゟ゠-ヿ一-鿿]")


def contains_japanese(text: str) -> bool:
    return bool(_JAPANESE_RE.search(text))


def find_japanese_files(docs_dir: Path = DOCS_DIR) -> list[Path]:
    """Return the sorted `*.md` files under `docs_dir` containing Japanese text."""
    found: list[Path] = []
    for path in sorted(docs_dir.rglob("*.md")):
        try:
            if contains_japanese(path.read_text(encoding="utf-8")):
                found.append(path)
        except OSError as e:
            print(f"Error reading {path}: {e}", file=sys.stderr)
    return found


def main() -> int:
    if not DOCS_DIR.is_dir():
        print(f"Directory {DOCS_DIR} does not exist.", file=sys.stderr)
        return 1

    japanese_files = find_japanese_files()
    if not japanese_files:
        print("No Japanese files found.")
        return 0

    print("Files containing Japanese characters:")
    for path in japanese_files:
        print(path.relative_to(REPO_ROOT))
    return 1


if __name__ == "__main__":
    sys.exit(main())
