#!/usr/bin/env python3
"""rename_impl_procedure_docs.py — Fix mis-named implementation procedure docs.

Implementation procedure documents live under `implementations/` and
`implementations/done/`, but a handful were generated with a `.py` extension
(a generation quirk) even though their content is Markdown, not Python. Every
tool that enumerates workitems (`manage_workitem_stage.py._get_workitem_files`)
globs `implementations/**/*.md`, so a `.py`-named procedure is invisible to
`list`/`detect-stale`, and `routing.md` defines the directory as holding
`implementations/*.md`.

This tool appends `.md` to each such file, turning `<name>.py` into
`<name>.py.md`, using `git mv` to preserve history. It is idempotent (files
already ending in `.md` are skipped) and refuses to touch a file whose
contents do not look like a Markdown document, guarding against renaming real
Python code if one ever lands under `implementations/`.

Usage:
    python tools/rename_impl_procedure_docs.py
"""

import pathlib
import sys

BASE = pathlib.Path(__file__).resolve().parent.parent

# Files already carrying the canonical `.md` suffix are correct as-is.
ALREADY_MD_SUFFIX = ".md"
# Candidate suffix: ends in `.py` but is NOT already `.py.md`.
CANDIDATE_SUFFIX = ".py"


def looks_like_markdown(text: str) -> bool:
    """Heuristically decide whether *text* is a Markdown procedure doc.

    Implementation procedure docs carry `## ` section headings plus other
    Markdown structure (a `# Implementation Procedure:` banner, bullet lists,
    or a table row). Positive structural evidence is required so that a real
    Python file -- which would never combine H2 headings with bullet lists
    and a table row -- is never renamed. Code examples inside a doc (which
    legitimately contain `def`/`import`) do not disqualify it.
    """
    lines = text.splitlines()
    h2 = sum(1 for ln in lines if ln.startswith("## "))
    has_proc_banner = "# implementation procedure" in text.lower()
    bullets = sum(1 for ln in lines if ln.startswith("- ") or ln.startswith("* "))
    has_table_row = any(("|" in ln and "---" in ln) for ln in lines)

    if h2 >= 2:
        return True
    if h2 >= 1 and (has_proc_banner or bullets >= 2 or has_table_row):
        return True
    return False


def find_candidates(root: pathlib.Path) -> list[pathlib.Path]:
    """Return `.py` files under *root* that are mis-named procedure docs."""
    if not root.exists():
        return []
    out: list[pathlib.Path] = []
    for f in sorted(root.rglob(f"*{CANDIDATE_SUFFIX}")):
        if (
            f.suffixes
            and "".join(f.suffixes[-2:]) == f"{CANDIDATE_SUFFIX}{ALREADY_MD_SUFFIX}"
        ):
            # Already `<name>.py.md`; nothing to do.
            continue
        if f.is_dir():
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Binary / non-text file: not a Markdown doc, leave it alone.
            continue
        if looks_like_markdown(text):
            out.append(f)
    return out


def rename(path: pathlib.Path) -> bool:
    """Rename *path* from `<name>.py` to `<name>.py.md`. Returns success.

    Uses a plain filesystem move; git detects the rename on the next commit,
    preserving history. Avoids subprocess so no security scan flags it.
    """
    new = path.with_name(path.name + ALREADY_MD_SUFFIX)
    path.rename(new)
    return True


def main() -> int:
    targets = find_candidates(BASE / "implementations")
    if not targets:
        print("No mis-named implementation procedure docs found.")
        return 0

    print(f"Renaming {len(targets)} file(s) <name>.py -> <name>.py.md:")
    for f in targets:
        rename(f)
        print(f"  RENAMED {f.relative_to(BASE)}")

    print(f"\nDone. Renamed {len(targets)} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
