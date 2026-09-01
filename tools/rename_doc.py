#!/usr/bin/env python3
"""tools/rename_doc.py

Rename a `docs/*.md` file (including `docs/adr/*.md`) via `git mv` and rewrite
every Markdown-link path across `docs/` pointing at the old path, preserving
each referencing file's existing link style (bare filename vs. `../`-prefixed).

Scope is restricted to `docs/`: both the old/new path arguments and every
rewrite target must resolve under the repository's `docs/` directory, or the
run is rejected before any write (defends against a `..`-traversal argument).

An opt-in `--old-title`/`--new-title` pair also rewrites a matching link's
adjacent text. Non-link prose mentions of the old filename are reported, never
rewritten, in both modes.

Usage:
    python tools/rename_doc.py <old-path> <new-path>
    python tools/rename_doc.py <old-path> <new-path> --apply
    python tools/rename_doc.py <old-path> <new-path> \\
        --old-title "Old Title" --new-title "New Title" --apply
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# Inline `[text](path)` Markdown link form only -- reference-style
# `[text][ref]` / `[ref]: path` links are not in scope (see the implementation
# procedure's Assumptions: not observed in the inspected ADR files).
MD_LINK_RE = re.compile(r"\[([^\]\n]*)\]\(([^)\n]+)\)")

# A link path resolving to old-path is only rewritten when its shape is
# unambiguously one of the two conventions observed in this repository's own
# ADR cross-references: a bare filename (no `/` at all), or one-or-more
# `../` hops followed by a bare filename. Anything else fails closed (Details
# in the implementation procedure: "must fail closed ... report it rather
# than guess a rewrite").
_DOTDOT_STYLE_RE = re.compile(r"^(?:\.\./)+[^/]+$")

# A prose mention of the old filename outside a link span: word/hyphen
# boundaries on both sides avoid matching a basename that is merely a
# substring of a longer, unrelated filename.
_WORD_BOUNDARY_LEFT = r"(?<![\w./-])"
_WORD_BOUNDARY_RIGHT = r"(?![\w-])"


class RenameDocError(Exception):
    """Raised for any validation failure that must abort before a write."""


@dataclass(frozen=True)
class PlannedRewrite:
    """One `[text](path)` link span to rewrite in `file`."""

    file: Path
    line_no: int
    span: tuple[int, int]
    old_snippet: str
    new_snippet: str


@dataclass(frozen=True)
class ProseFinding:
    """A non-link occurrence of the old filename -- report only, never written."""

    file: Path
    line_no: int
    snippet: str


@dataclass(frozen=True)
class UnresolvedLink:
    """A link resolving to old-path whose style could not be classified."""

    file: Path
    line_no: int
    snippet: str
    reason: str


@dataclass(frozen=True)
class ScanPlan:
    rewrites_by_file: dict[Path, list[PlannedRewrite]]
    prose_findings: list[ProseFinding]
    unresolved_links: list[UnresolvedLink]


def find_repo_root(start: Path) -> Path:
    """Walk up from `start` to the nearest ancestor containing `.git`."""
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    raise RenameDocError(
        f"could not locate repository root (no .git found above {start})"
    )


def ensure_within_docs(path: Path, docs_root: Path, label: str) -> None:
    """Reject `path` unless it resolves strictly under `docs_root`."""
    try:
        path.relative_to(docs_root)
    except ValueError as exc:
        raise RenameDocError(f"{label} is outside docs/: {path}") from exc


def classify_style(path_part: str) -> str | None:
    """Return "bare", "dotdot", or None (unclassifiable -> fail closed)."""
    if "/" not in path_part:
        return "bare"
    if _DOTDOT_STYLE_RE.fullmatch(path_part):
        return "dotdot"
    return None


def compute_new_target(referencing_file: Path, new_path: Path) -> str:
    """Relative link path from `referencing_file`'s directory to `new_path`."""
    rel = Path(os.path.relpath(new_path, start=referencing_file.parent))
    return rel.as_posix()


def _line_number_at(content: str, pos: int) -> int:
    return content.count("\n", 0, pos) + 1


def _line_text_at(content: str, pos: int) -> str:
    start = content.rfind("\n", 0, pos) + 1
    end = content.find("\n", pos)
    if end == -1:
        end = len(content)
    return content[start:end]


def scan_file(
    md_file: Path,
    old_path: Path,
    new_path: Path,
    old_title: str | None,
    new_title: str | None,
) -> tuple[list[PlannedRewrite], list[ProseFinding], list[UnresolvedLink]]:
    """Scan one `docs/*.md` file for links/prose mentions of `old_path`."""
    content = md_file.read_text(encoding="utf-8")
    link_matches = list(MD_LINK_RE.finditer(content))
    handled_spans = [m.span() for m in link_matches]

    rewrites: list[PlannedRewrite] = []
    unresolved: list[UnresolvedLink] = []
    for m in link_matches:
        text, target = m.group(1), m.group(2)
        path_part, sep, anchor = target.partition("#")
        if not path_part:
            continue
        candidate = (md_file.parent / path_part).resolve()
        if candidate != old_path:
            continue

        line_no = _line_number_at(content, m.start())
        style = classify_style(path_part)
        if style is None:
            unresolved.append(
                UnresolvedLink(
                    file=md_file,
                    line_no=line_no,
                    snippet=m.group(0),
                    reason=(
                        "link path is neither a bare filename nor a "
                        "../-prefixed path; not rewritten"
                    ),
                )
            )
            continue

        new_target_path = compute_new_target(md_file, new_path)
        new_target = f"{new_target_path}#{anchor}" if sep else new_target_path
        new_text = (
            new_title if (old_title and new_title and text == old_title) else text
        )
        new_snippet = f"[{new_text}]({new_target})"
        rewrites.append(
            PlannedRewrite(
                file=md_file,
                line_no=line_no,
                span=m.span(),
                old_snippet=m.group(0),
                new_snippet=new_snippet,
            )
        )

    prose: list[ProseFinding] = []
    basename = old_path.name
    prose_re = re.compile(
        _WORD_BOUNDARY_LEFT + re.escape(basename) + _WORD_BOUNDARY_RIGHT
    )
    for pm in prose_re.finditer(content):
        if any(s <= pm.start() and pm.end() <= e for s, e in handled_spans):
            continue
        prose.append(
            ProseFinding(
                file=md_file,
                line_no=_line_number_at(content, pm.start()),
                snippet=_line_text_at(content, pm.start()).strip(),
            )
        )

    return rewrites, prose, unresolved


def build_plan(
    docs_root: Path,
    old_path: Path,
    new_path: Path,
    old_title: str | None,
    new_title: str | None,
) -> ScanPlan:
    """Scan every `docs/**/*.md` file and assemble the full rewrite plan."""
    rewrites_by_file: dict[Path, list[PlannedRewrite]] = {}
    prose_findings: list[ProseFinding] = []
    unresolved_links: list[UnresolvedLink] = []

    for md_file in sorted(docs_root.rglob("*.md")):
        rewrites, prose, unresolved = scan_file(
            md_file, old_path, new_path, old_title, new_title
        )
        if rewrites:
            rewrites_by_file[md_file] = rewrites
        prose_findings.extend(prose)
        unresolved_links.extend(unresolved)

    return ScanPlan(rewrites_by_file, prose_findings, unresolved_links)


def apply_rewrites_to_content(content: str, rewrites: list[PlannedRewrite]) -> str:
    """Apply `rewrites` to `content`, rightmost span first to keep offsets valid."""
    for rewrite in sorted(rewrites, key=lambda r: r.span[0], reverse=True):
        start, end = rewrite.span
        content = content[:start] + rewrite.new_snippet + content[end:]
    return content


def git_mv(old_path: Path, new_path: Path, repo_root: Path) -> None:
    """Move `old_path` to `new_path` via `git mv`, run from `repo_root`."""
    try:
        # bandit: B404/B603/B607 (Low) are expected here per
        # rules/coding.md Bandit priority findings ("B603 ... Preferred;
        # document if shell=True needed") -- shell=False with this fixed
        # argument list never interpolates caller input into a shell string,
        # and PATH-based `git` resolution (not a hardcoded absolute path) is
        # the portable, intended behavior across this repository's dev/CI
        # environments, matching the existing accepted pattern in
        # tools/check_workitem_traceability.py's `_git_or_mtime`.
        subprocess.run(
            ["git", "mv", str(old_path), str(new_path)],
            cwd=repo_root,
            shell=False,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RenameDocError(f"git mv failed: {exc.stderr.strip()}") from exc
    except OSError as exc:
        raise RenameDocError(f"git mv failed to start: {exc}") from exc


def print_report(
    old_path: Path,
    new_path: Path,
    repo_root: Path,
    plan: ScanPlan,
    apply_mode: bool,
) -> None:
    mode_label = "APPLY" if apply_mode else "DRY-RUN"
    print(
        f"[{mode_label}] git mv {old_path.relative_to(repo_root)} "
        f"{new_path.relative_to(repo_root)}"
    )

    if plan.rewrites_by_file:
        print("\nPlanned link/title rewrites:")
        for file, rewrites in sorted(plan.rewrites_by_file.items()):
            rel = file.relative_to(repo_root)
            for rewrite in sorted(rewrites, key=lambda r: r.line_no):
                print(f"  {rel}:{rewrite.line_no}")
                print(f"    - {rewrite.old_snippet}")
                print(f"    + {rewrite.new_snippet}")
    else:
        print("\nPlanned link/title rewrites: none")

    if plan.unresolved_links:
        print("\nUnresolved links (matched old path, style not rewritten):")
        for link in sorted(plan.unresolved_links, key=lambda u: (u.file, u.line_no)):
            rel = link.file.relative_to(repo_root)
            print(f"  {rel}:{link.line_no}: {link.snippet} -- {link.reason}")

    if plan.prose_findings:
        print("\nNon-link prose mentions (reported only, never rewritten):")
        for mention in sorted(plan.prose_findings, key=lambda p: (p.file, p.line_no)):
            rel = mention.file.relative_to(repo_root)
            print(f"  {rel}:{mention.line_no}: {mention.snippet}")
    else:
        print("\nNon-link prose mentions: none")


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("old_path", help="current docs/*.md path to rename")
    parser.add_argument("new_path", help="new docs/*.md path")
    parser.add_argument(
        "--old-title", default=None, help="link text to match for title rewrite"
    )
    parser.add_argument("--new-title", default=None, help="replacement link text")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run", action="store_true", help="report planned changes (default)"
    )
    mode.add_argument(
        "--apply", action="store_true", help="perform the move and write changes"
    )
    args = parser.parse_args(argv)

    if bool(args.old_title) != bool(args.new_title):
        parser.error("--old-title and --new-title must be supplied together")

    return args


def resolve_and_validate_paths(
    old_path_arg: str, new_path_arg: str
) -> tuple[Path, Path, Path, Path]:
    """Resolve CLI path arguments and confirm both lie under docs/."""
    repo_root = find_repo_root(Path.cwd())
    docs_root = (repo_root / "docs").resolve()
    if not docs_root.is_dir():
        raise RenameDocError(f"docs/ directory not found under {repo_root}")

    old_path = Path(old_path_arg).resolve()
    new_path = Path(new_path_arg).resolve()
    ensure_within_docs(old_path, docs_root, "old-path")
    ensure_within_docs(new_path, docs_root, "new-path")

    return old_path, new_path, docs_root, repo_root


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        old_path, new_path, docs_root, repo_root = resolve_and_validate_paths(
            args.old_path, args.new_path
        )
    except RenameDocError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if not old_path.is_file():
        print(
            f"ERROR: old-path does not exist or is not a file: {old_path}",
            file=sys.stderr,
        )
        return 1

    plan = build_plan(docs_root, old_path, new_path, args.old_title, args.new_title)

    # Defense in depth (Details): re-verify containment for every file the
    # scanner considers writing to, not only the git mv source/destination.
    for target_file in plan.rewrites_by_file:
        try:
            ensure_within_docs(target_file, docs_root, "rewrite target")
        except RenameDocError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

    apply_mode = args.apply
    print_report(old_path, new_path, repo_root, plan, apply_mode)

    if not apply_mode:
        return 0

    try:
        git_mv(old_path, new_path, repo_root)
    except RenameDocError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    for target_file, rewrites in plan.rewrites_by_file.items():
        # The old-path file itself, if it self-referenced, now lives at
        # new_path after the git mv above.
        actual_file = new_path if target_file == old_path else target_file
        content = actual_file.read_text(encoding="utf-8")
        new_content = apply_rewrites_to_content(content, rewrites)
        actual_file.write_text(new_content, encoding="utf-8")

    print(
        f"\nApplied: moved {old_path.relative_to(repo_root)} -> "
        f"{new_path.relative_to(repo_root)}; "
        f"updated {len(plan.rewrites_by_file)} referencing file(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
