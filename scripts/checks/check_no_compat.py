#!/usr/bin/env python3
"""scripts/checks/check_no_compat.py

CI check for backward compatibility leftovers in active source code and docs:
- Backward compatibility references
- Re-export stubs
- Stale import paths (rag.models, rag.llm)
- Module-level _cfg cache references

Usage:
    python -m scripts.checks.check_no_compat [--allowlist <path>]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Patterns that should not appear in active source code or docs
COMPAT_PATTERNS = {
    "backward compatibility layer": r"backward[ _]compatibility\s+(?:layer|stub|re-export)",
    "from rag.models import": r"from\s+rag\.models\s+import",
    "import rag.models": r"import\s+rag\.models\b",
    "rag.llm import": r"from\s+rag\.llm\s+import",
    "rag.llm module": r"import\s+rag\.llm\b",
    "module-level _cfg": r"module[ _]level[ _]_cfg",
    "_cfg cache": r"_cfg[ _]cache",
}

# Allowlist: files that are permitted to contain these patterns (archive/migration notes only)
DEFAULT_ALLOWLIST = {
    # Migration notes that document historical changes
    ROOT_DIR / "docs" / "05_agent_09_data-layer.md",
    ROOT_DIR / "docs" / "03_rag_00_document-guide.md",  # documents removed rag.llm stub
    # This checker's own docstring describing what it checks
    ROOT_DIR / "scripts" / "checks" / "check_no_compat.py",
    # Test file intentionally referencing the removed re-export stub
    ROOT_DIR / "tests" / "test_rag_get_cfg.py",
}


def is_allowlisted(filepath: Path, allowlist: set[Path]) -> bool:
    """Check if the file is in the allowlist."""
    return filepath in allowlist


def check_compat_patterns(content: str, filepath: Path, allowlist: set[Path]) -> list[str]:
    """Check for backward compatibility leftovers in content."""
    issues = []
    if is_allowlisted(filepath, allowlist):
        return issues

    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        for pattern_name, pattern in COMPAT_PATTERNS.items():
            if re.search(pattern, stripped):
                issues.append(
                    f"{filepath}:{i}: backward compatibility leftover — "
                    f"'{pattern_name}': {stripped}"
                )
    return issues


def check_all(content: str, filepath: Path, allowlist: set[Path]) -> list[str]:
    """Run all checks and return combined issues."""
    return check_compat_patterns(content, filepath, allowlist)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check for backward compatibility leftovers in source code and docs"
    )
    parser.add_argument(
        "--allowlist",
        type=Path,
        default=None,
        help="Override the default allowlist with a custom file (one path per line)",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Files to check (default: scripts/, docs/, tests/)",
    )
    args = parser.parse_args()

    # Load allowlist
    if args.allowlist and args.allowlist.exists():
        allowlist = {Path(p.strip()) for p in args.allowlist.read_text().splitlines() if p.strip()}
    else:
        allowlist = DEFAULT_ALLOWLIST.copy()

    # Determine files to check
    if not args.files:
        dirs_to_scan = [ROOT_DIR / "scripts", ROOT_DIR / "docs", ROOT_DIR / "tests"]
        files = []
        for d in dirs_to_scan:
            if d.exists():
                files.extend(d.glob("**/*.py"))
                files.extend(d.glob("**/*.md"))
        files = sorted(set(files))  # Deduplicate
    else:
        files = [Path(f) for f in args.files]

    total_issues = 0
    for filepath in files:
        if not filepath.exists():
            continue
        content = filepath.read_text(encoding="utf-8")
        issues = check_all(content, filepath, allowlist)
        if issues:
            total_issues += len(issues)
            print(f"\n--- {filepath.relative_to(ROOT_DIR)} ---", file=sys.stderr)
            for issue in issues:
                print(issue, file=sys.stderr)

    if total_issues > 0:
        print(f"\n{total_issues} issue(s) found", file=sys.stderr)
        return 1
    print("All checks passed", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
