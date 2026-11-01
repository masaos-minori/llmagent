"""tools/fix_procedure_new_markers.py

Add the ` (new)` marker recognized by `tools/stale_detector.py` after backticked
symbol names that an implementation procedure declares as constructs it creates.

`stale_detector.py` skips a backticked name followed by " (new)" (see its module
docstring and `_NEW_MARKER_RE`). When a procedure renames or introduces a symbol,
every backticked mention of the new name must carry the marker, or the procedure
reports false "symbol_missing" staleness before execution.

Usage:
    uv run python tools/fix_procedure_new_markers.py \
        --symbols task_nonce,test_example_new \
        implementations/20260101-000000_01_path.py.md [more .md ...]

Names already followed by the marker are left untouched. Only whole backticked
tokens (`name`) are matched; a name already marked is not marked twice.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def add_markers(text: str, symbols: list[str]) -> tuple[str, int]:
    """Return `text` with ` (new)` appended after each unmarked `` `symbol` ``.

    Longer names are matched first so a shorter name that is a substring of a
    longer one cannot split it (the surrounding backticks make collisions
    unlikely, but ordering keeps the behavior obvious).
    """
    order = sorted(set(symbols), key=len, reverse=True)
    pattern = re.compile(
        "`(" + "|".join(re.escape(name) for name in order) + r")`(?! ?\(new\))"
    )
    count = 0

    def _replace(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return f"`{match.group(1)}` (new)"

    return pattern.sub(_replace, text), count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Add stale_detector (new) markers to procedure documents."
    )
    parser.add_argument(
        "--symbols",
        required=True,
        help="Comma-separated symbol names the procedures create.",
    )
    parser.add_argument("files", nargs="+", help="Procedure Markdown files to edit.")
    args = parser.parse_args(argv)

    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    total = 0
    for path in args.files:
        file_path = Path(path)
        if not file_path.is_file():
            print(f"ERROR: not a file: {file_path}", file=sys.stderr)
            return 1
        text = file_path.read_text(encoding="utf-8")
        new_text, count = add_markers(text, symbols)
        if count:
            file_path.write_text(new_text, encoding="utf-8")
        print(f"{file_path}: {count} marker(s) added")
        total += count
    print(f"total: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
