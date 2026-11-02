"""tools/classify_changes.py
Read-only classifier for splitting one working tree into per-group commits.

Reads `git status --porcelain=v1 -z` output and prints the changed paths grouped
into `artifacts` (issues/, plans/, implementations/, including done/), `code`
(scripts/, config/, deploy/), `tests`, `tools`, `docs` (docs/, skills/, rules/,
templates/, prompts/, routing.md, AGENTS.md, CLAUDE.md) and `other`. Each group
prints a ready-to-use `pathspec:` line for `git commit -- <paths>`. A rename is one
record, so both of its names always sit side by side in the same pathspec (new name
first, then old name): committing only one name would record an addition and leave
the old name's deletion staged. Paths with a working-tree-only change are printed on
an `unstaged:` line and untracked paths on an `untracked:` line; neither is part of
a pathspec. A path that is both staged and changed in the working tree is flagged
`partly-staged`, because a pathspec commit records working-tree content.

Never stages, unstages, or commits anything; the only subprocess is the status read.

Usage:
    python tools/classify_changes.py [--status-file <path>]
    python tools/classify_changes.py --group <name>
    python tools/classify_changes.py --verify-pathspec <path> [<path> ...]

`--status-file <path>` reads the porcelain bytes from a file (`-` means stdin)
instead of running git.

Exit code: 0 normal; 1 when a `partly-staged` or `unmerged` warning exists (or, with
`--verify-pathspec`, when a candidate names only one name of a staged rename);
2 for a usage error or a failed git call.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess  # nosec B404 — static git status call only, see _read_status
import sys
from dataclasses import dataclass
from pathlib import Path

GROUP_ORDER: tuple[str, ...] = (
    "artifacts",
    "code",
    "tests",
    "tools",
    "docs",
    "other",
)

# (group, directory prefixes, exact file names); first match wins, `other` is the fallback.
_GROUP_RULES: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    ("artifacts", ("issues/", "plans/", "implementations/"), ()),
    ("code", ("scripts/", "config/", "deploy/"), ()),
    ("tests", ("tests/",), ()),
    ("tools", ("tools/",), ()),
    (
        "docs",
        ("docs/", "skills/", "rules/", "templates/", "prompts/"),
        ("routing.md", "AGENTS.md", "CLAUDE.md"),
    ),
)

_UNMERGED = frozenset({"DD", "AU", "UD", "UA", "DU", "AA", "UU"})
_STAGED_LETTERS = "MADRC"
_WORKTREE_LETTERS = "MD"


@dataclass(frozen=True)
class Change:
    """One porcelain entry; a rename or copy holds both names."""

    index: str
    worktree: str
    path: str
    orig_path: str | None = None

    @property
    def is_untracked(self) -> bool:
        return self.index == "?"

    @property
    def is_unmerged(self) -> bool:
        return (self.index + self.worktree) in _UNMERGED

    @property
    def is_staged(self) -> bool:
        return (
            not self.is_unmerged
            and not self.is_untracked
            and self.index in _STAGED_LETTERS
        )

    @property
    def is_partly_staged(self) -> bool:
        return (
            self.is_staged
            and self.index in _STAGED_LETTERS
            and self.worktree in _WORKTREE_LETTERS
        )

    @property
    def is_worktree_only(self) -> bool:
        return self.index == " " and self.worktree != " "


@dataclass
class Classification:
    """Per-group path lists plus the warnings of one status snapshot."""

    pathspec: dict[str, list[str]]
    unstaged: dict[str, list[str]]
    untracked: dict[str, list[str]]
    warnings: list[str]

    @property
    def blocking(self) -> bool:
        return any(
            w.startswith(("WARN partly-staged", "WARN unmerged")) for w in self.warnings
        )


def parse_porcelain_z(raw: bytes) -> list[Change]:
    """Parse `git status --porcelain=v1 -z` bytes; raise ValueError on a malformed entry."""
    tokens = raw.decode("utf-8", errors="surrogateescape").split("\0")
    if tokens and tokens[-1] == "":
        tokens.pop()
    changes: list[Change] = []
    i = 0
    while i < len(tokens):
        entry = tokens[i]
        i += 1
        if len(entry) < 4 or entry[2] != " ":
            raise ValueError(f"malformed status entry: {entry!r}")
        index, worktree, path = entry[0], entry[1], entry[3:]
        if index + worktree == "!!":
            continue
        orig_path: str | None = None
        if index in "RC" or worktree in "RC":
            if i >= len(tokens) or not tokens[i]:
                raise ValueError(f"rename entry without original path: {entry!r}")
            orig_path = tokens[i]
            i += 1
        changes.append(Change(index, worktree, path, orig_path))
    return changes


def group_of(path: str) -> str:
    """Return the group name of a repository-relative path."""
    for group, prefixes, names in _GROUP_RULES:
        if path in names or path.startswith(prefixes):
            return group
    return "other"


def classify(changes: list[Change]) -> Classification:
    """Group the changes; a rename is grouped under its new name."""
    result = Classification(
        pathspec={g: [] for g in GROUP_ORDER},
        unstaged={g: [] for g in GROUP_ORDER},
        untracked={g: [] for g in GROUP_ORDER},
        warnings=[],
    )
    for change in changes:
        group = group_of(change.path)
        if change.is_untracked:
            result.untracked[group].append(change.path)
        elif change.is_unmerged:
            result.warnings.append(f"WARN unmerged: {change.path}")
        elif change.is_staged:
            result.pathspec[group].append(change.path)
            if change.orig_path is not None:
                result.pathspec[group].append(change.orig_path)
                if group_of(change.orig_path) != group:
                    result.warnings.append(
                        f"NOTE cross-group-rename: {change.orig_path} -> {change.path} "
                        f"(grouped under {change.path})"
                    )
            if change.is_partly_staged:
                result.warnings.append(f"WARN partly-staged: {change.path}")
        elif change.is_worktree_only:
            result.unstaged[group].append(change.path)
    return result


def _quote(paths: list[str]) -> str:
    return " ".join(shlex.quote(p) for p in paths)


def render(classification: Classification) -> str:
    """Render the default output: one block per non-empty group, then warnings."""
    lines: list[str] = []
    for group in GROUP_ORDER:
        spec = classification.pathspec[group]
        unstaged = classification.unstaged[group]
        untracked = classification.untracked[group]
        if not (spec or unstaged or untracked):
            continue
        lines.append(f"[{group}]")
        if spec:
            lines.append(f"pathspec: {_quote(spec)}")
        if unstaged:
            lines.append(f"unstaged: {_quote(unstaged)}")
        if untracked:
            lines.append(f"untracked: {_quote(untracked)}")
    if classification.warnings:
        lines.append("warnings:")
        lines.extend(classification.warnings)
    return "\n".join(lines)


def verify_pathspec(changes: list[Change], paths: list[str]) -> list[str]:
    """Return one message per staged rename or copy of which only one name is in `paths`."""
    named = set(paths)
    messages: list[str] = []
    for change in changes:
        if not change.is_staged or change.orig_path is None:
            continue
        has_new, has_old = change.path in named, change.orig_path in named
        if has_new and not has_old:
            messages.append(f"split-rename: {change.path} needs {change.orig_path}")
        elif has_old and not has_new:
            messages.append(f"split-rename: {change.orig_path} needs {change.path}")
    return messages


def _read_status(status_file: str | None) -> bytes:
    """Read porcelain bytes from stdin, a file, or `git status --porcelain=v1 -z`."""
    if status_file == "-":
        return sys.stdin.buffer.read()
    if status_file is not None:
        return Path(status_file).read_bytes()
    proc = subprocess.run(  # nosec B603 B607 — static argument list, no user input
        ["git", "status", "--porcelain=v1", "-z"],
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"git status failed (exit {proc.returncode}): "
            f"{proc.stderr.decode('utf-8', errors='replace').strip()}"
        )
    return proc.stdout


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only classifier of changed paths into per-group pathspec lists."
    )
    parser.add_argument(
        "--status-file",
        help="read `git status --porcelain=v1 -z` bytes from this file ('-' for stdin)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--group",
        choices=GROUP_ORDER,
        help="print only this group's pathspec value",
    )
    mode.add_argument(
        "--verify-pathspec",
        nargs="+",
        metavar="PATH",
        help="report staged renames of which only one name is among the given paths",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = _build_parser().parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    try:
        changes = parse_porcelain_z(_read_status(args.status_file))
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.verify_pathspec is not None:
        messages = verify_pathspec(changes, args.verify_pathspec)
        for message in messages:
            print(message)
        return 1 if messages else 0

    classification = classify(changes)
    if args.group is not None:
        value = _quote(classification.pathspec[args.group])
        if value:
            print(value)
        for warning in classification.warnings:
            print(warning, file=sys.stderr)
    else:
        output = render(classification)
        if output:
            print(output)
    return 1 if classification.blocking else 0


if __name__ == "__main__":
    sys.exit(main())
