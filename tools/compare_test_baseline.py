#!/usr/bin/env python3
"""tools/compare_test_baseline.py

Classify the failures of one pytest run against a baseline of known failing tests (wfeff002).

The input is the JUnit XML file of a run (`pytest --junitxml=<path>`, with or without
`-n`). Each failing or erroring testcase, including a collection error, is one id:
`classname::name`, or the bare dotted module name for a collection error. The tool reports
new failures, baseline entries that now pass, baseline entries that did not run, and the
count of unchanged known failures. It never runs pytest and never changes what runs.

Baseline file (`tools/known_test_failures_baseline.txt`): one entry per line as the test
id, a tab, and a reason that names an issue (`issues/...md`); `#` lines and blank lines are
ignored. A plain run writes nothing. `--update` removes the entries that ran and passed;
`--add ID --reason TEXT` appends one entry for a test that failed in this run.

Usage:
    python tools/compare_test_baseline.py <junit-xml> [--baseline PATH]
    python tools/compare_test_baseline.py <junit-xml> --update [--dry-run]
    python tools/compare_test_baseline.py <junit-xml> --add ID --reason TEXT [--dry-run]

Exit codes: 0 no new failure, 1 at least one new failure, 2 a usage or input error
(including an invalid baseline or an unusable XML file).
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET  # nosec B405 — reads the local XML file the caller's own pytest run wrote
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._atomic_write import add_dry_run_argument, atomic_write_text, print_dry_run

DEFAULT_BASELINE = Path(__file__).resolve().parent / "known_test_failures_baseline.txt"
ISSUE_PATH_RE = re.compile(r"issues/(?:done/)?[\w.-]+\.md")


class InputError(Exception):
    """The XML file or the baseline file is missing or unusable."""


class BaselineError(Exception):
    """A baseline line is invalid; carries its 1-based line number."""

    def __init__(self, line_no: int, message: str) -> None:
        super().__init__(f"baseline line {line_no}: {message}")
        self.line_no = line_no


@dataclass(frozen=True)
class RunResult:
    failing: frozenset[str]
    passed: frozenset[str]
    skipped: frozenset[str]
    total: int


@dataclass(frozen=True)
class Classification:
    new: list[str]
    known: list[str]
    fixed: list[str]
    not_run: list[str]


def read_junit(path: Path) -> RunResult:
    """Read one run; a missing, unparsable, or empty file is an InputError."""
    try:
        root = ET.parse(path).getroot()  # nosec B314 — same local, trusted file
    except (OSError, ET.ParseError) as exc:
        raise InputError(f"{path}: cannot read JUnit XML ({exc})") from exc
    failing: set[str] = set()
    passed: set[str] = set()
    skipped: set[str] = set()
    total = 0
    for case in root.iter("testcase"):
        total += 1
        classname = case.get("classname") or ""
        name = case.get("name") or ""
        test_id = f"{classname}::{name}" if classname else name
        tags = {child.tag for child in case}
        if tags & {"failure", "error"}:
            failing.add(test_id)
        elif "skipped" in tags:
            skipped.add(test_id)
        else:
            passed.add(test_id)
    if total == 0:
        raise InputError(f"{path}: no testcase found (an interrupted or empty run)")
    failing_ids = frozenset(failing)
    return RunResult(
        failing_ids,
        frozenset(passed) - failing_ids,
        frozenset(skipped) - failing_ids,
        total,
    )


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise InputError(f"{path}: cannot read baseline ({exc})") from exc


def load_baseline(path: Path) -> dict[str, str]:
    """Return {test id: reason}; an invalid line raises BaselineError."""
    entries: dict[str, str] = {}
    for line_no, line in enumerate(_read_text(path).splitlines(), start=1):
        if not line.strip() or line.startswith("#"):
            continue
        test_id, sep, reason = line.partition("\t")
        if not sep or not test_id.strip():
            raise BaselineError(line_no, "expected '<test id><TAB><reason>'")
        if not ISSUE_PATH_RE.search(reason):
            raise BaselineError(
                line_no, "the reason must name an issue path (issues/...md)"
            )
        if test_id in entries:
            raise BaselineError(line_no, f"duplicate entry {test_id}")
        entries[test_id] = reason.strip()
    return entries


def classify(run: RunResult, baseline: dict[str, str]) -> Classification:
    return Classification(
        new=sorted(run.failing - baseline.keys()),
        known=sorted(run.failing & baseline.keys()),
        fixed=sorted(baseline.keys() & run.passed),
        not_run=sorted(baseline.keys() - run.failing - run.passed),
    )


def render_report(result: Classification) -> str:
    sections = (
        ("new failures", result.new),
        ("fixed (remove from the baseline)", result.fixed),
        ("not run (kept in the baseline)", result.not_run),
    )
    lines: list[str] = []
    for title, ids in sections:
        if ids:
            lines.append(f"{title}:")
            lines.extend(f"  {test_id}" for test_id in ids)
    lines.append(f"known failures: {len(result.known)}")
    return "\n".join(lines) + "\n"


def update_baseline(text: str, fixed: list[str]) -> str:
    """Drop the lines of the fixed entries; every other line is kept byte for byte."""
    drop = set(fixed)
    kept = [
        line
        for line in text.splitlines(keepends=True)
        if line.partition("\t")[0] not in drop
    ]
    return "".join(kept)


def add_entry(text: str, test_id: str, reason: str) -> str:
    """Append one entry as the last line."""
    prefix = text if not text or text.endswith("\n") else text + "\n"
    return f"{prefix}{test_id}\t{reason}\n"


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Classify pytest failures against a known-failure baseline."
    )
    parser.add_argument(
        "junit_xml", type=Path, help="JUnit XML file written by `pytest --junitxml`"
    )
    parser.add_argument(
        "--baseline", type=Path, default=DEFAULT_BASELINE, help="baseline file"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--update", action="store_true", help="remove baseline entries that now pass"
    )
    mode.add_argument(
        "--add", metavar="ID", help="append an entry for a test that failed in this run"
    )
    parser.add_argument("--reason", help="reason for --add; must name an issue path")
    add_dry_run_argument(parser)
    return parser.parse_args(argv)


def _write(path: Path, old: str, new: str, *, dry_run: bool) -> None:
    if dry_run:
        print_dry_run(path, old, new)
    else:
        atomic_write_text(path, new)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        run = read_junit(args.junit_xml)
        baseline = load_baseline(args.baseline)
        result = classify(run, baseline)
        print(render_report(result), end="")
        if args.add is not None:
            reason = args.reason or ""
            if not ISSUE_PATH_RE.search(reason):
                raise InputError(
                    "--add needs --reason naming an issue path (issues/...md)"
                )
            if args.add in baseline:
                raise InputError(f"{args.add} is already in the baseline")
            if args.add not in run.failing:
                raise InputError(f"{args.add} did not fail in this run")
            old = _read_text(args.baseline)
            _write(
                args.baseline,
                old,
                add_entry(old, args.add, reason.strip()),
                dry_run=args.dry_run,
            )
        elif args.update and result.fixed:
            old = _read_text(args.baseline)
            _write(
                args.baseline,
                old,
                update_baseline(old, result.fixed),
                dry_run=args.dry_run,
            )
    except (InputError, BaselineError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 1 if result.new else 0


if __name__ == "__main__":
    raise SystemExit(main())
