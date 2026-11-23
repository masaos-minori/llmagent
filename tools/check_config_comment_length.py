#!/usr/bin/env python3
"""tools/check_config_comment_length.py

CI check for long TOML comment blocks under `config/` (agentcfg006 REQ-005): a run of
more than `THRESHOLD_LINES` consecutive comment lines is a finding. A finding whose block
is not recorded in `EXCEPTIONS` is error-level and the run exits 1; a recorded block is
reported as a non-blocking warning, so the eight blocks present at plan freeze keep the
live run clean while any new long block fails it. A recorded entry whose block no longer
exists is itself error-level: the exception list may not keep entries that no longer name
a live block.

A comment line is a line whose first non-whitespace character is `#`. Inline comments
after a value are not counted: they cannot form a block.

Usage:
    python tools/check_config_comment_length.py [--root PATH] [--threshold N] [files...]
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "config"

# Blocks longer than this many consecutive comment lines are findings. One constant,
# per design D2.
THRESHOLD_LINES = 5

CODE_LONG_BLOCK = "CFG-COMMENT-001"
CODE_ALLOWLISTED_BLOCK = "CFG-COMMENT-002"
CODE_STALE_EXCEPTION = "CFG-COMMENT-003"

SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"


@dataclass(frozen=True)
class ExceptionEntry:
    """One grandfathered block: the file, the block's first line, its length, its reason."""

    path: str
    line: int
    length: int
    reason: str


# The blocks that already exist in the live `config/` files, recorded at plan freeze
# (2026-11-22, implementation-cycle Step 3a). Entries follow the
# `tools/compat_exceptions.toml` shape (one entry per block, each with a reason): a block
# that changes length or position no longer matches its entry and the run fails, so an
# entry is removed when its block is shortened, never grown.
EXCEPTIONS: tuple[ExceptionEntry, ...] = (
    ExceptionEntry(
        path="config/adr_authority.toml",
        line=124,
        length=6,
        reason="Grandfathered at plan freeze; authority-model header block.",
    ),
    ExceptionEntry(
        path="config/chunk_splitter.toml",
        line=5,
        length=10,
        reason="Grandfathered at plan freeze; splitter parameter explanation block.",
    ),
    ExceptionEntry(
        path="config/cicd_mcp_server.toml",
        line=8,
        length=8,
        reason="Grandfathered at plan freeze; server permission-scope block.",
    ),
    ExceptionEntry(
        path="config/eventbus.toml",
        line=24,
        length=9,
        reason="Grandfathered at plan freeze; retention-rule explanation block.",
    ),
    ExceptionEntry(
        path="config/github_mcp_server.toml",
        line=3,
        length=7,
        reason="Grandfathered at plan freeze; server scope-restriction block.",
    ),
    ExceptionEntry(
        path="config/mcp_dedup.toml",
        line=1,
        length=12,
        reason="Grandfathered at plan freeze; dedup key model block.",
    ),
    ExceptionEntry(
        path="config/shell_mcp_server.toml",
        line=3,
        length=15,
        reason="Grandfathered at plan freeze; command allowlist explanation block.",
    ),
    ExceptionEntry(
        path="config/tool_catalog.toml",
        line=1,
        length=23,
        reason="Grandfathered at plan freeze; producer-declared field model block.",
    ),
)


def comment_blocks(text: str) -> list[tuple[int, int]]:
    """Return `(first_line, length)` for each run of consecutive comment lines."""
    blocks: list[tuple[int, int]] = []
    start = 0
    length = 0
    for line_no, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("#"):
            if length == 0:
                start = line_no
            length += 1
        elif length:
            blocks.append((start, length))
            length = 0
    if length:
        blocks.append((start, length))
    return blocks


def relative_path(path: Path) -> str:
    """Return *path* as a repository-relative path, or as given when it is outside."""
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def find_exception(
    exceptions: tuple[ExceptionEntry, ...], path: str, start: int, length: int
) -> ExceptionEntry | None:
    """Return the entry matching the block at *start* of *path*, or None."""
    for entry in exceptions:
        if entry.path == path and entry.line == start and entry.length == length:
            return entry
    return None


def check_file(
    path: Path,
    text: str,
    exceptions: tuple[ExceptionEntry, ...] | None = None,
    threshold: int = THRESHOLD_LINES,
) -> list[tuple[str, str, str]]:
    """Return `(code, severity, location)` per block longer than *threshold* and per stale entry."""
    if exceptions is None:
        exceptions = EXCEPTIONS
    rel = relative_path(path)
    findings: list[tuple[str, str, str]] = []
    blocks = comment_blocks(text)
    for start, length in blocks:
        if length <= threshold:
            continue
        location = f"{rel}:{start}"
        entry = find_exception(exceptions, rel, start, length)
        if entry is None:
            findings.append(
                (
                    CODE_LONG_BLOCK,
                    SEVERITY_ERROR,
                    f"{location}: comment block of {length} consecutive comment lines",
                )
            )
        else:
            findings.append(
                (
                    CODE_ALLOWLISTED_BLOCK,
                    SEVERITY_WARNING,
                    f"{location}: comment block of {length} consecutive comment lines "
                    f"grandfathered: {entry.reason}",
                )
            )
    live = {(start, length) for start, length in blocks}
    for entry in exceptions:
        if entry.path == rel and (entry.line, entry.length) not in live:
            findings.append(
                (
                    CODE_STALE_EXCEPTION,
                    SEVERITY_ERROR,
                    f"{entry.path}:{entry.line}: grandfathered block of "
                    f"{entry.length} lines no longer exists",
                )
            )
    return findings


def scan(files: list[Path]) -> list[tuple[str, str, str]]:
    """Run `check_file` over each existing file and return the combined findings."""
    findings: list[tuple[str, str, str]] = []
    for path in files:
        if not path.is_file():
            continue
        findings.extend(check_file(path, path.read_text(encoding="utf-8")))
    return findings


def target_files(root: Path, files: list[str]) -> list[Path]:
    """Return the files to check: the given ones, or every `*.toml` under *root*."""
    if files:
        return [Path(f) for f in files]
    return sorted(root.glob("**/*.toml"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check `config/` TOML files for comment blocks longer than the threshold "
            f"({THRESHOLD_LINES} consecutive comment lines)"
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=CONFIG_DIR,
        help="Directory to scan (default: config/)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=THRESHOLD_LINES,
        help=f"Block length that makes a finding error-level (default: {THRESHOLD_LINES})",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Files to check (default: every `config/*.toml`)",
    )
    args = parser.parse_args(argv)

    files = target_files(args.root, args.files)
    findings: list[tuple[str, str, str]] = []
    for path in files:
        if not path.is_file():
            continue
        findings.extend(
            check_file(path, path.read_text(encoding="utf-8"), threshold=args.threshold)
        )

    for code, severity, location in findings:
        print(f"{code} {severity} {location}", file=sys.stderr)
    errors = sum(1 for _, severity, _ in findings if severity == SEVERITY_ERROR)
    print(
        f"{errors} error(s), {len(findings) - errors} warning(s) in {len(files)} file(s)",
        file=sys.stderr,
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
