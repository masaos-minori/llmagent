#!/usr/bin/env python3
"""check_module_size.py — Verify scripts/ Python modules stay under the size gate.

Every `.py` file under `scripts/` is measured in bytes. A file larger than the
limit (default 20480 B) is a violation, because a module that large has outgrown
the point where one screen of logic can be reviewed, tested, and refactored as a
unit.

Baseline: violations that already existed are grandfathered through
`tools/check_module_size_baseline.txt` (one `<relpath>\t<byte size>` per line), so
only new violations fail. The baseline is a ceiling, not a license:

    - A baselined file that grows past its recorded size fails as a regression.
    - A baselined file that shrank is reported so the baseline can be tightened.
    - A baseline entry whose file is back under the limit, or is gone, is stale
      and fails, which keeps the baseline shrinking.

Usage:
    python tools/check_module_size.py [--scripts-dir PATH] [--limit BYTES]
    python tools/check_module_size.py --baseline PATH
    python tools/check_module_size.py --no-baseline
    python tools/check_module_size.py --update-baseline
    python tools/check_module_size.py --top N

Notes:
    - Only file size is measured. Splitting an over-limit module is a refactoring
      decision and is never performed by this script.
    - `--top N` prints the N largest modules as advisory output; it never changes
      the exit status.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

DEFAULT_LIMIT = 20480

DEFAULT_BASELINE = Path(__file__).resolve().parent / "check_module_size_baseline.txt"

SKIP_DIRS = frozenset({"__pycache__", ".venv", "node_modules"})


def collect_sizes(scripts_dir: Path) -> list[tuple[str, int]]:
    """Return `(relpath, size_bytes)` for every .py file under scripts_dir, sorted."""
    found: list[tuple[str, int]] = []
    for path in scripts_dir.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.relative_to(scripts_dir).parts):
            continue
        found.append((path.relative_to(scripts_dir).as_posix(), path.stat().st_size))
    return sorted(found)


def load_baseline(path: Path) -> dict[str, int]:
    """Read `<relpath>\\t<byte size>` entries; blank lines and `#` comments are ignored.

    Returns:
        Mapping of relpath to its recorded ceiling in bytes. A malformed line is
        reported on stderr and dropped, so a typo cannot silently grandfather a file.
    """
    if not path.is_file():
        return {}
    entries: dict[str, int] = {}
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        relpath, separator, size_text = line.partition("\t")
        if not separator or not relpath:
            print(f"malformed baseline line {line_no}: {raw}", file=sys.stderr)
            continue
        try:
            entries[relpath] = int(size_text)
        except ValueError:
            print(f"malformed baseline line {line_no}: {raw}", file=sys.stderr)
    return entries


def write_baseline(path: Path, entries: dict[str, int]) -> None:
    """Write the baseline file sorted by relpath."""
    lines = [f"{relpath}\t{size}" for relpath, size in sorted(entries.items())]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check that scripts/ modules stay under the size gate"
    )
    parser.add_argument(
        "--scripts-dir", default=None, help="Path to scripts/ directory"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Maximum module size in bytes (default: {DEFAULT_LIMIT})",
    )
    parser.add_argument(
        "--baseline",
        default=str(DEFAULT_BASELINE),
        help="Baseline file of grandfathered module sizes",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=0,
        metavar="N",
        help="Print the N largest modules as advisory output",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--no-baseline", action="store_true", help="Report every over-limit module"
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
    if not scripts_dir.is_dir():
        print(f"ERROR: scripts directory not found: {scripts_dir}", file=sys.stderr)
        return 1

    limit = args.limit
    sizes = collect_sizes(scripts_dir)
    over = [(relpath, size) for relpath, size in sizes if size > limit]
    baseline_path = Path(args.baseline)

    if args.top > 0:
        largest = sorted(sizes, key=lambda item: item[1], reverse=True)[: args.top]
        print(f"LARGEST MODULES (top {len(largest)}):")
        for relpath, size in largest:
            print(f"  {relpath}: {size} B")

    if args.update_baseline:
        entries = {relpath: size for relpath, size in over}
        write_baseline(baseline_path, entries)
        print(f"Baseline written: {len(entries)} entries -> {baseline_path}")
        return 0

    baseline = {} if args.no_baseline else load_baseline(baseline_path)

    new_issues: list[str] = []
    regressions: list[str] = []
    improved: list[str] = []
    grandfathered = 0
    for relpath, size in over:
        recorded = baseline.get(relpath)
        if recorded is None:
            new_issues.append(
                f"{relpath}: {size} B exceeds the {limit} B limit (not in the baseline)"
            )
        elif size > recorded:
            regressions.append(
                f"{relpath}: grew from {recorded} B to {size} B since it was baselined"
            )
        elif size < recorded:
            improved.append(f"{relpath}: {recorded} B -> {size} B")
            grandfathered += 1
        else:
            grandfathered += 1

    stale: list[str] = []
    size_by_relpath = dict(sizes)
    for relpath, recorded in sorted(baseline.items()):
        current = size_by_relpath.get(relpath)
        if current is None:
            stale.append(
                f"{relpath}: recorded {recorded} B but the file no longer exists"
            )
        elif current <= limit:
            stale.append(
                f"{relpath}: recorded {recorded} B but the file is now {current} B "
                f"(under the {limit} B limit)"
            )

    if new_issues:
        print(f"ISSUES FOUND ({len(new_issues)}):")
        for issue in new_issues:
            print(f"  {issue}")
    if regressions:
        print(f"BASELINE REGRESSIONS ({len(regressions)}) - split the module:")
        for issue in regressions:
            print(f"  {issue}")
    if stale:
        print(
            f"STALE BASELINE ENTRIES ({len(stale)}) - remove them (--update-baseline):"
        )
        for issue in stale:
            print(f"  {issue}")
    if new_issues or regressions or stale:
        if grandfathered:
            print(f"({grandfathered} baselined module(s) not shown)")
        return 1

    if improved:
        print(
            f"IMPROVED BASELINE ENTRIES ({len(improved)}) - tighten with --update-baseline:"
        )
        for issue in improved:
            print(f"  {issue}")
    if grandfathered:
        print(
            f"OK - no new violations ({grandfathered} baselined module(s) at or below "
            f"their recorded size)."
        )
    else:
        print(f"ALL OK - every scripts/ module is at most {limit} B.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
