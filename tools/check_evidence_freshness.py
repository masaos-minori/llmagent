#!/usr/bin/env python3
"""tools/check_evidence_freshness.py

Read-only freshness check for the evidence of a Plan (wfeff004).

A Plan records the revision at which its evidence was verified as one line in its
`## Traceability`: `- **Evidence revision**: <40 hex>`. The files that revision covers are
derived from the document: every backticked repository path (a trailing `:LINE` or
`:LINE-LINE` removed), plus any path given with `--also`. A later phase may cite a claim as
verified at that revision, without re-reading, only for the files this tool reports
unchanged (`rules/ai-execution.md` Adversarial Verification (Base)).

  check DOC   report the cited files that changed since the revision (a later commit),
              are uncommitted (working tree, index, or untracked), or are unrecorded (an
              `--also` path the document does not cite). DOC is a Plan, or a procedure,
              which uses the revision of its `Source plan`.
  record DOC  print the `Evidence revision` line for the current HEAD; refuse while a cited
              file is uncommitted, so the revision never covers unverified text.

Nothing is written. Usage:
    python tools/check_evidence_freshness.py check DOC [--also PATH ...] [--root DIR]
    python tools/check_evidence_freshness.py record DOC [--root DIR]

Exit codes: 0 every cited file unchanged (check) or the line printed (record); 1 at least
one file reported; 2 no revision, an unknown SHA, an unreadable document, or no git.
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 — fixed argv list built from "git" and document-derived paths after "--", no shell
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT_DIR = Path(__file__).resolve().parent.parent

_BACKTICKED_RE = re.compile(r"`([^`]+)`")
_LINE_SUFFIX_RE = re.compile(r":\d+(?:-\d+)?$")
_PATH_RE = re.compile(r"^[\w.][\w.-]*(?:/[\w.-]+)+$")
_REVISION_RE = re.compile(r"(?m)^- \*\*Evidence revision\*\*:\s*`?([0-9a-f]{40})`?\s*$")
_SOURCE_PLAN_RE = re.compile(r"(?m)^- \*\*Source plan\*\*:\s*`?([^`\s]+)`?\s*$")


class InputError(Exception):
    """No revision, an unknown SHA, an unreadable document, or git is unavailable."""


@dataclass(frozen=True)
class Freshness:
    changed: frozenset[str]
    uncommitted: frozenset[str]
    unrecorded: frozenset[str]
    total: int


def cited_paths(text: str, own_path: str | None = None) -> list[str]:
    """Repository paths cited in backticks, `:LINE` removed, unique, in first-seen order."""
    paths: list[str] = []
    for token in _BACKTICKED_RE.findall(text):
        path = _LINE_SUFFIX_RE.sub("", token.strip())
        if _PATH_RE.match(path) and path != own_path and path not in paths:
            paths.append(path)
    return paths


def read_revision(doc: Path, root: Path) -> str:
    """The `Evidence revision` of `doc`, or of its `Source plan` when `doc` has none."""
    text = _read(doc)
    match = _REVISION_RE.search(text)
    if match:
        return match.group(1)
    source = _SOURCE_PLAN_RE.search(text)
    if source:
        name = source.group(1)
        for candidate in (root / name, root / "plans" / "done" / Path(name).name):
            if candidate.is_file():
                match = _REVISION_RE.search(_read(candidate))
                if match:
                    return match.group(1)
    raise InputError(f"{doc}: no Evidence revision (verify in full)")


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise InputError(f"{path}: cannot read ({exc})") from exc


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(  # nosec B603 B607 — fixed argv: git (resolved through PATH), a subcommand, paths after "--"; no shell
            ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
        )
    except OSError as exc:
        raise InputError(f"git is not available ({exc})") from exc


def _status_paths(root: Path, paths: list[str]) -> set[str]:
    result = _git(
        root, "status", "--porcelain=v1", "--untracked-files=all", "--", *paths
    )
    found: set[str] = set()
    for line in result.stdout.splitlines():
        entry = line[3:]
        if " -> " in entry:
            entry = entry.split(" -> ", 1)[1]
        found.add(entry.strip('"'))
    return found


def classify(root: Path, sha: str, paths: list[str], also: list[str]) -> Freshness:
    """Classify each cited and `--also` path against revision `sha`."""
    if _git(root, "cat-file", "-e", f"{sha}^{{commit}}").returncode != 0:
        raise InputError(
            f"revision {sha} is not a commit of this repository (verify in full)"
        )
    unrecorded = frozenset(path for path in also if path not in paths)
    everything = list(dict.fromkeys([*paths, *also]))
    changed: set[str] = set()
    uncommitted: set[str] = set()
    if everything:
        diff = _git(root, "diff", "--name-only", sha, "HEAD", "--", *everything)
        changed = set(diff.stdout.splitlines())
        uncommitted = _status_paths(root, everything)
    return Freshness(
        frozenset(changed), frozenset(uncommitted), unrecorded, len(everything)
    )


def render(result: Freshness, sha: str) -> str:
    lines = [
        f"{status}: {path}"
        for status, group in (
            ("changed", result.changed),
            ("uncommitted", result.uncommitted),
            ("unrecorded", result.unrecorded),
        )
        for path in sorted(group)
    ]
    reported = result.changed | result.uncommitted | result.unrecorded
    lines.append(
        f"unchanged: {result.total - len(reported)}; changed: {len(result.changed)}; "
        f"uncommitted: {len(result.uncommitted)}; unrecorded: {len(result.unrecorded)} (revision {sha[:12]})"
    )
    return "\n".join(lines) + "\n"


def _own_path(doc: Path, root: Path) -> str | None:
    try:
        return doc.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report which cited files changed since a Plan's evidence revision."
    )
    parser.add_argument("command", choices=("check", "record"))
    parser.add_argument("doc", type=Path, help="a Plan or a procedure document")
    parser.add_argument(
        "--also",
        action="append",
        default=[],
        metavar="PATH",
        help="extra path the claims rely on",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT_DIR,
        help="repository root (default: this repository)",
    )
    args = parser.parse_args(argv)
    try:
        paths = cited_paths(_read(args.doc), _own_path(args.doc, args.root))
        if args.command == "record":
            dirty = sorted(_status_paths(args.root, paths)) if paths else []
            if dirty:
                print("".join(f"uncommitted: {path}\n" for path in dirty), end="")
                return 1
            head = _git(args.root, "rev-parse", "HEAD")
            if head.returncode != 0:
                raise InputError("cannot read HEAD")
            print(f"- **Evidence revision**: {head.stdout.strip()}")
            return 0
        sha = read_revision(args.doc, args.root)
        result = classify(args.root, sha, paths, args.also)
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(render(result, sha), end="")
    return 1 if (result.changed or result.uncommitted or result.unrecorded) else 0


if __name__ == "__main__":
    raise SystemExit(main())
