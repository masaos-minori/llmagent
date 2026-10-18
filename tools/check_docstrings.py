#!/usr/bin/env python3
"""Check module-level docstrings in scripts/*.py against the standard format.

Standard format: scripts/<relative-path> \u2014 <description>

Checks performed:
    - Module-level docstring exists
    - Em-dash (\u2014) separator is present
    - Path prefix matches the file's relative path under scripts/
    - Description after the separator is non-empty and > 3 characters

Baseline: violations that already existed are grandfathered through
`tools/check_docstrings_baseline.txt` (one `<relpath>\t<issue kind>` per line), so
only new violations fail. A baseline entry whose file no longer has that violation is
stale and also fails, which keeps the baseline shrinking.

Usage:
    python tools/check_docstrings.py [--scripts-dir PATH] [--baseline PATH]
    python tools/check_docstrings.py --no-baseline
    python tools/check_docstrings.py --update-baseline

Notes:
    - This script only validates existing docstrings; it does NOT add or modify them.
    - Docstring insertion/modification via regex causes line-number shifts and can
      corrupt Python source files. Use ast-based approaches for safe modification.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EM_DASH = "\u2014"  # —

# Patterns that must be skipped before looking for the module-level docstring
SHEBANG_RE = re.compile(r"^#!.*$")
FUTURE_IMPORT_RE = re.compile(r"^\s*from\s+__future__\s+import\s+.+\n")

# Regex to find the first triple-quote string (module-level docstring)
DOCSTRING_RE = re.compile(r"\s*\"\"\"(.*?)\"\"\"", re.DOTALL)
DOCSTRING_SINGLE_RE = re.compile(r"\s*\'\'\'(.*?)\'\'\'", re.DOTALL)

# Regex to split on em-dash
EM_DASH_SPLIT_RE = re.compile(r"\s*\u2014\s+")

# Minimum description length
MIN_DESC_LENGTH = 4

DEFAULT_BASELINE = Path(__file__).resolve().parent / "check_docstrings_baseline.txt"


def strip_header(content: str) -> str:
    """Remove shebang and __future__ imports before searching for docstring."""
    result = content
    if SHEBANG_RE.match(result):
        result = result[result.find("\n") + 1 :]
    while FUTURE_IMPORT_RE.match(result):
        result = FUTURE_IMPORT_RE.sub("", result, count=1)
    return result


def check_docstring(filepath: Path, relpath: str) -> list[str]:
    """Validate a single file's module-level docstring. Returns list of issue messages."""
    issues: list[str] = []
    expected_prefix = f"scripts/{relpath}"

    try:
        content = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        issues.append(f"read error: {e}")
        return issues

    if not content.strip():
        issues.append("empty file")
        return issues

    search_content = strip_header(content)

    # Find the module-level docstring
    match = DOCSTRING_RE.search(search_content)
    if not match:
        match = DOCSTRING_SINGLE_RE.search(search_content)
    if not match:
        issues.append("no docstring")
        return issues

    docstring = match.group(1).strip()

    # Check for em-dash separator
    if EM_DASH not in docstring:
        issues.append(f"missing separator: '{docstring[:80]}'")
        return issues

    # Check path prefix
    if not docstring.startswith(expected_prefix):
        issues.append(
            f"path mismatch: expected '{expected_prefix}', got '{docstring[:80]}'"
        )
        return issues

    # Split on em-dash and validate description
    parts = EM_DASH_SPLIT_RE.split(docstring)
    if len(parts) != 2:
        # Try simpler split (em-dash without surrounding spaces)
        parts = docstring.split(EM_DASH)
    if len(parts) != 2 or not parts[1].strip():
        issues.append(f"empty description: '{docstring[:80]}'")
        return issues

    desc = parts[1].strip()
    if len(desc) < MIN_DESC_LENGTH:
        issues.append(f"description too short: '{desc}'")
        return issues

    return []


def issue_kind(issue: str) -> str:
    """Return the stable category of an issue message (text before the first ':')."""
    return issue.split(":", 1)[0]


def collect_issues(scripts_dir: Path) -> list[tuple[str, str]]:
    """Return (relpath, issue message) for every violation under scripts_dir."""
    issues: list[tuple[str, str]] = []
    for py_file in sorted(scripts_dir.rglob("*.py")):
        relpath = py_file.relative_to(scripts_dir).as_posix()
        for issue in check_docstring(py_file, relpath):
            issues.append((relpath, issue))
    return issues


def load_baseline(path: Path) -> set[tuple[str, str]]:
    """Read `<relpath>\\t<issue kind>` lines; a missing file is an empty baseline."""
    if not path.is_file():
        return set()
    entries: set[tuple[str, str]] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        relpath, _, kind = line.partition("\t")
        entries.add((relpath, kind))
    return entries


def write_baseline(path: Path, entries: set[tuple[str, str]]) -> None:
    """Write the baseline sorted, one `<relpath>\\t<issue kind>` per line."""
    lines = [f"{relpath}\t{kind}" for relpath, kind in sorted(entries)]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check module-level docstrings in scripts/"
    )
    parser.add_argument(
        "--scripts-dir", default=None, help="Path to scripts/ directory"
    )
    parser.add_argument(
        "--baseline",
        default=str(DEFAULT_BASELINE),
        help="Baseline file of grandfathered violations",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--no-baseline", action="store_true", help="Report every violation"
    )
    group.add_argument(
        "--update-baseline",
        action="store_true",
        help="Rewrite the baseline from the current violations and exit 0",
    )
    args = parser.parse_args(argv)

    scripts_dir = (
        Path(args.scripts_dir)
        if args.scripts_dir
        else Path(__file__).resolve().parent.parent / "scripts"
    )
    # If scripts_dir doesn't exist, try one level up (for when script is in tools/)
    if not scripts_dir.is_dir():
        scripts_dir = Path(__file__).resolve().parent.parent.parent / "scripts"
    if not scripts_dir.is_dir():
        print(f"ERROR: scripts directory not found: {scripts_dir}", file=sys.stderr)
        return 1

    issues = collect_issues(scripts_dir)
    baseline_path = Path(args.baseline)

    if args.update_baseline:
        entries = {(relpath, issue_kind(issue)) for relpath, issue in issues}
        write_baseline(baseline_path, entries)
        print(f"Baseline written: {len(entries)} entries -> {baseline_path}")
        return 0

    baseline = set() if args.no_baseline else load_baseline(baseline_path)
    current = {(relpath, issue_kind(issue)) for relpath, issue in issues}
    new_issues = [
        (relpath, issue)
        for relpath, issue in issues
        if (relpath, issue_kind(issue)) not in baseline
    ]
    stale = sorted(baseline - current)
    grandfathered = len(issues) - len(new_issues)

    if new_issues:
        print(f"ISSUES FOUND ({len(new_issues)}):")
        for relpath, issue in new_issues:
            print(f"  {relpath}: {issue}")
    if stale:
        print(
            f"STALE BASELINE ENTRIES ({len(stale)}) - remove them (--update-baseline):"
        )
        for relpath, kind in stale:
            print(f"  {relpath}: {kind}")
    if new_issues or stale:
        if grandfathered:
            print(f"({grandfathered} baseline violation(s) not shown)")
        return 1

    if grandfathered:
        print(
            f"OK - no new violations ({grandfathered} grandfathered in the baseline)."
        )
    else:
        print("ALL OK - All docstrings follow the correct format.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
