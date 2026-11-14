#!/usr/bin/env python3
"""tools/_compat_leftover_phrases.py

Path-scoped leftover-phrase patterns for ``tools/check_compat_shims.py``.

Owns the eleven ``LEFTOVER_PHRASES`` entries and ``check_leftover_phrases``,
which returns issue strings in the same shape as
``check_compat_patterns`` in ``tools/check_compat_shims.py``. Called from
``check_all`` by plan 20261112-122408 (rmcompat008).

Each entry maps a human-readable phrase name to a compiled regex, the path
prefixes (relative to the repository root) it applies to, and a multi-line
flag. The regexes use character classes instead of plain spaces (for example
``Extracted[ ]from``) so ordinary words do not match and the checker does not
flag this module's own source. The module also skips its own file, mirroring
the ``[checker_self_reference]`` allowance in
``tools/compat_exceptions.toml`` without adding an entry there.
"""

from __future__ import annotations

import re
from pathlib import Path

# Skip the helper's own source: its pattern-name labels are the leftover
# phrases themselves and would match their own regexes. This mirrors the
# checker's ``[checker_self_reference]`` allowance without widening
# compat_exceptions.toml (plan 20261112-122408 REQ-007 keeps that file
# unchanged).
_SELF_PATH = Path(__file__).resolve()

# name -- compiled regex -- path prefixes (relative to repo root) -- multiline
LEFTOVER_PHRASES: dict[str, tuple[re.Pattern[str], tuple[str, ...], bool]] = {
    "Extracted from": (re.compile(r"Extracted[ ]from"), ("scripts/",), False),
    "Refactored:": (re.compile(r"Refactored:"), ("scripts/",), False),
    "Precedent:": (re.compile(r"Precedent:"), ("scripts/",), False),
    "signature stability": (
        re.compile(r"signature stability"),
        ("scripts/",),
        False,
    ),
    "re-exported for": (re.compile(r"re-exported for"), ("scripts/",), False),
    "predates": (re.compile(r"predates"), ("scripts/",), False),
    "user-approved": (
        re.compile(r"user-approved"),
        ("scripts/", "docs/"),
        False,
    ),
    "pre-migration gate|database": (
        re.compile(r"pre-migration (?:gate|database)"),
        ("scripts/",),
        False,
    ),
    "additive (wire) field": (
        re.compile(r"additive (wire )?field"),
        ("scripts/",),
        False,
    ),
    "bypass(es) build_db_config": (
        re.compile(r"bypass(?:es|ed)?\s+build_db_config"),
        ("scripts/rag/",),
        False,
    ),
    "mirror... exactly": (
        re.compile(r"mirror.{1,50}exactly"),
        ("scripts/", "docs/"),
        True,
    ),
}


def _in_scope(file_posix: str, prefix: str) -> bool:
    """True when *file_posix* is under directory *prefix* (segment-aware).

    Matches both repository-relative paths (``scripts/x.py`` starts with the
    prefix) and arbitrary absolute paths (``/tmp/.../scripts/x.py`` contains
    ``/scripts/``), while rejecting look-alikes such as ``/x/myscripts/x.py``.
    """
    return file_posix.startswith(prefix) or f"/{prefix}" in file_posix


def check_leftover_phrases(
    content: str, filepath: Path, allowlist: set[Path]
) -> list[str]:
    """Check for path-scoped leftover phrases.

    Returns issue strings in the same format as
    ``check_compat_patterns`` in ``tools/check_compat_shims.py``. Skips
    allowlisted files and files outside every pattern's path prefixes; for a
    multi-line pattern tests each stripped line joined with its successor
    (REQ-002).
    """
    issues: list[str] = []
    resolved = filepath.resolve()
    if resolved in {p.resolve() for p in allowlist}:
        return issues
    if resolved == _SELF_PATH:
        return issues

    posix = resolved.as_posix()
    lines = content.split("\n")
    for idx, raw_line in enumerate(lines):
        lineno = idx + 1
        stripped = raw_line.strip()
        for name, (pattern, pat_prefixes, multiline) in LEFTOVER_PHRASES.items():
            if not any(_in_scope(posix, p) for p in pat_prefixes):
                continue
            if multiline:
                candidate = stripped
                if idx + 1 < len(lines):
                    candidate = f"{stripped} {lines[idx + 1].strip()}"
                if pattern.search(candidate):
                    issues.append(
                        f"{filepath}:{lineno}: backward compatibility leftover "
                        f"— '{name}': {stripped}"
                    )
            elif pattern.search(stripped):
                issues.append(
                    f"{filepath}:{lineno}: backward compatibility leftover "
                    f"— '{name}': {stripped}"
                )
    return issues


if __name__ == "__main__":
    # Standalone smoke use; the checker owns the real scan loop.
    import sys

    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path()
    print(check_leftover_phrases(target.read_text(encoding="utf-8"), target, set()))
