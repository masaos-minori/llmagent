#!/usr/bin/env python3
"""Replace the '§' (section sign) glyph with plain ASCII across docs/ and skills/.

'§' renders inconsistently (width/glyph drift) across terminals and viewers. This
script rewrites every occurrence into equivalent plain-English wording so no
markdown file under docs/ or skills/ depends on the glyph rendering correctly.

Substitution rules, applied in order:
  1. '**Label**: §X'        -> '**Label**: X'            (field-label context; the
                                                            label word already says
                                                            "section"/"symbol", so §
                                                            is simply dropped)
  2. '§N-§M'                -> 'sections N-M'             (hyphen range)
  3. '§N/§M'                -> 'sections N/M'             (slash range)
  4. '§<digit...>'          -> 'section <digit...>'       (single numeric/alnum ref,
                                                            e.g. '§15', '§9.4', '§8a')
  5. '<word-char>§' or '§'  -> '<word-char> ' or ''        (remaining word/phrase refs;
                                                            insert a space if the glyph
                                                            was glued directly onto a
                                                            preceding word character)

Usage:
    python tools/fix_docs_section_marks.py [--dir docs skills] [--apply]

Options:
    --dir <path> [<path> ...]   Directories to scan (default: docs skills)
    --apply                     Write changes to disk (default: dry-run, prints a diff-like summary)
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

_LABEL_RE = re.compile(r"(\*\*[^*\n]+\*\*:\s*)§")
_RANGE_HYPHEN_RE = re.compile(
    r"§([A-Za-z0-9][A-Za-z0-9.]*)-§([A-Za-z0-9][A-Za-z0-9.]*)"
)
_RANGE_SLASH_RE = re.compile(r"§([A-Za-z0-9][A-Za-z0-9.]*)/§([A-Za-z0-9][A-Za-z0-9.]*)")
_NUMERIC_RE = re.compile(r"§(\d[A-Za-z0-9.]*)")
_WORD_RE = re.compile(r"(\w?)§ ?")


def fix_section_marks(content: str) -> tuple[str, int]:
    """Rewrite every '§' in content into plain ASCII wording. Returns (new_content, count)."""
    count = 0

    def sub(pattern: re.Pattern[str], repl: str, text: str) -> str:
        nonlocal count
        new_text, n = pattern.subn(repl, text)
        count += n
        return new_text

    content = sub(_LABEL_RE, r"\1", content)
    content = sub(_RANGE_HYPHEN_RE, r"sections \1-\2", content)
    content = sub(_RANGE_SLASH_RE, r"sections \1/\2", content)
    content = sub(_NUMERIC_RE, r"section \1", content)

    def word_repl(m: re.Match[str]) -> str:
        prefix = m.group(1)
        return f"{prefix} " if prefix else ""

    content, n = _WORD_RE.subn(word_repl, content)
    count += n

    return content, count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dir",
        nargs="+",
        default=["docs", "skills"],
        help="Directories to scan, relative to repo root (default: docs skills)",
    )
    parser.add_argument(
        "--apply", action="store_true", help="Write changes to disk (default: dry-run)"
    )
    args = parser.parse_args()

    total_files = 0
    total_marks = 0

    for rel_dir in args.dir:
        base_dir = REPO_ROOT / rel_dir
        if not base_dir.is_dir():
            print(f"WARNING: {base_dir} is not a directory, skipping.")
            continue

        for md_file in sorted(base_dir.rglob("*.md")):
            try:
                original = md_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                print(f"WARNING: could not read {md_file}: {exc}")
                continue

            if "§" not in original:
                continue

            new_content, count = fix_section_marks(original)
            rel_path = md_file.relative_to(REPO_ROOT)

            if args.apply:
                md_file.write_text(new_content, encoding="utf-8")
                print(f"{rel_path}: {count} occurrence(s) replaced")
            else:
                print(f"[DRY-RUN] {rel_path}: {count} occurrence(s) would be replaced")

            total_files += 1
            total_marks += count

    mode = "Replaced" if args.apply else "Would replace"
    print(f"\n{mode} {total_marks} occurrence(s) across {total_files} file(s).")
    if not args.apply and total_marks:
        print("Re-run with --apply to write changes.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
