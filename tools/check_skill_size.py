#!/usr/bin/env python3
"""tools/check_skill_size.py

Size budget for the instruction files that every pipeline cycle loads (skillsize001).

Every covered file (`skills/**/*.md`, `rules/*.md`, `prompts/*.md`, `templates/*.md`,
`routing.md`, `AGENTS.md`, `CLAUDE.md`) is measured in bytes. A file larger than the limit
(default 16384 B) is a violation unless it is recorded in the baseline. The model is
`tools/check_module_size.py`, with the same baseline semantics: the baseline is a ceiling,
not a license.

    - A baselined file that grows past its recorded size fails as a regression.
    - A baselined file that shrank is reported (advisory) so the baseline can be tightened.
    - A baseline entry whose file is gone, or is back at or under the limit, is stale and
      fails, which keeps the baseline shrinking.

Usage:
    python tools/check_skill_size.py [--root PATH] [--limit BYTES]
    python tools/check_skill_size.py --baseline PATH
    python tools/check_skill_size.py --no-baseline
    python tools/check_skill_size.py --update-baseline
    python tools/check_skill_size.py --top N

Exit codes: 0 clean, 1 a violation or a stale entry, 2 a usage error (missing root).

Notes:
    - Only file size is measured. Moving a rarely used branch to an edge-case file is an
      editing decision and is never performed by this script.
    - `--top N` prints the N largest covered files as advisory output.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.check_module_size import load_baseline, write_baseline

DEFAULT_LIMIT = 16384

DEFAULT_BASELINE = Path(__file__).resolve().parent / "check_skill_size_baseline.txt"

# Covered instruction files, as glob patterns relative to the repository root.
COVERED_PATTERNS = (
    "skills/**/*.md",
    "rules/*.md",
    "prompts/*.md",
    "templates/*.md",
    "routing.md",
    "AGENTS.md",
    "CLAUDE.md",
)


@dataclass(frozen=True)
class Evaluation:
    """Result of comparing sizes with the limit and the baseline."""

    violations: list[str] = field(default_factory=list)
    stale: list[str] = field(default_factory=list)
    shrunk: list[str] = field(default_factory=list)
    grandfathered: int = 0

    @property
    def failed(self) -> bool:
        """True when a violation or a stale baseline entry exists."""
        return bool(self.violations or self.stale)


def collect_covered(root: Path) -> list[tuple[str, int]]:
    """Return `(relpath, size_bytes)` for every covered file under root, sorted."""
    found: dict[str, int] = {}
    for pattern in COVERED_PATTERNS:
        for path in root.glob(pattern):
            if path.is_file():
                found[path.relative_to(root).as_posix()] = path.stat().st_size
    return sorted(found.items())


def evaluate(
    sizes: list[tuple[str, int]], baseline: dict[str, int], limit: int
) -> Evaluation:
    """Compare covered sizes with the limit and the baseline ceilings."""
    violations: list[str] = []
    shrunk: list[str] = []
    grandfathered = 0
    for relpath, size in sizes:
        if size <= limit:
            continue
        recorded = baseline.get(relpath)
        if recorded is None:
            violations.append(
                f"{relpath}: {size} B exceeds the {limit} B limit (not in the baseline)"
                " - move rarely used branches to an edge-case file"
            )
        elif size > recorded:
            violations.append(
                f"{relpath}: grew from {recorded} B to {size} B since it was baselined"
                " - reduce it or move a branch to an edge-case file"
            )
        else:
            grandfathered += 1
            if size < recorded:
                shrunk.append(f"{relpath}: {recorded} B -> {size} B")
    size_by_relpath = dict(sizes)
    stale: list[str] = []
    for relpath, recorded in sorted(baseline.items()):
        current = size_by_relpath.get(relpath)
        if current is None:
            stale.append(f"{relpath}: recorded {recorded} B but the file is gone")
        elif current <= limit:
            stale.append(
                f"{relpath}: recorded {recorded} B but the file is now {current} B"
                f" (at or under the {limit} B limit)"
            )
    return Evaluation(violations, stale, shrunk, grandfathered)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check that the pipeline instruction files stay within their size budget"
    )
    parser.add_argument("--root", default=None, help="Repository root")
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Maximum file size in bytes (default: {DEFAULT_LIMIT})",
    )
    parser.add_argument(
        "--baseline",
        default=str(DEFAULT_BASELINE),
        help="Baseline file of grandfathered file sizes",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=0,
        metavar="N",
        help="Print the N largest covered files as advisory output",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--no-baseline", action="store_true", help="Report every over-limit file"
    )
    group.add_argument(
        "--update-baseline",
        action="store_true",
        help="Rewrite the baseline from the current over-limit files and exit 0",
    )
    return parser


def _report(result: Evaluation) -> None:
    if result.violations:
        print(f"SIZE VIOLATIONS ({len(result.violations)}):", file=sys.stderr)
        for line in result.violations:
            print(f"  {line}", file=sys.stderr)
    if result.stale:
        print(
            f"STALE BASELINE ENTRIES ({len(result.stale)}) - remove them"
            " (--update-baseline):",
            file=sys.stderr,
        )
        for line in result.stale:
            print(f"  {line}", file=sys.stderr)
    if result.shrunk:
        print(
            f"SHRUNK ({len(result.shrunk)}) - tighten the baseline with"
            " --update-baseline:"
        )
        for line in result.shrunk:
            print(f"  {line}")


def _print_top(sizes: list[tuple[str, int]], count: int) -> None:
    largest = sorted(sizes, key=lambda item: item[1], reverse=True)[:count]
    print(f"LARGEST FILES (top {len(largest)}):")
    for relpath, size in largest:
        print(f"  {relpath}: {size} B")


def _write_baseline_from(path: Path, sizes: list[tuple[str, int]], limit: int) -> None:
    entries = {relpath: size for relpath, size in sizes if size > limit}
    write_baseline(path, entries)
    print(f"Baseline written: {len(entries)} entries -> {path}")


def main(argv: list[str] | None = None) -> int:
    """Run the check; return the process exit code."""
    args = _build_parser().parse_args(argv)
    root = Path(args.root) if args.root else Path(__file__).resolve().parent.parent
    if not root.is_dir():
        print(f"ERROR: root directory not found: {root}", file=sys.stderr)
        return 2
    sizes = collect_covered(root)
    if args.top > 0:
        _print_top(sizes, args.top)
    baseline_path = Path(args.baseline)
    if args.update_baseline:
        _write_baseline_from(baseline_path, sizes, args.limit)
        return 0
    baseline = {} if args.no_baseline else load_baseline(baseline_path)
    result = evaluate(sizes, baseline, args.limit)
    _report(result)
    if result.failed:
        if result.grandfathered:
            print(f"({result.grandfathered} baselined file(s) not shown)")
        return 1
    print(
        f"OK - no new violations ({result.grandfathered} baselined file(s) at or"
        " below their recorded size)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
