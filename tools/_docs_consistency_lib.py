#!/usr/bin/env python3
"""_docs_consistency_lib.py — Shared scaffolding for per-domain docs consistency checkers.

Extracted from tools/check_agent_docs_consistency.py so that
tools/check_mcp_docs_consistency.py (and any future per-domain checker) can
reuse the same DocFile/Issue shapes, file discovery, and CLI reporting
instead of re-implementing them.

Not a check script itself — has no __main__ entry point.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DocFile:
    """A single documentation file with its contents."""

    path: Path
    rel_path: str  # relative to docs/
    lines: list[str] = field(default_factory=list)

    @property
    def line_count(self) -> int:
        return len(self.lines)


@dataclass(frozen=True)
class Issue:
    """A single consistency issue found."""

    file: str  # relative path within docs/
    line_no: int
    severity: str  # "ERROR" or "WARNING"
    message: str


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------


def discover_md_files(docs_dir: Path, *, prefix: str) -> list[DocFile]:
    """Return all *prefix*-matching .md files under *docs_dir*, sorted for determinism."""
    result: list[DocFile] = []
    for p in sorted(docs_dir.glob(f"{prefix}*.md")):
        rel = str(p.relative_to(docs_dir))
        content = p.read_text(encoding="utf-8")
        lines = content.splitlines()
        result.append(DocFile(path=p, rel_path=rel, lines=lines))
    return result


# ---------------------------------------------------------------------------
# Generic checks shared across domains: broken internal links and
# removed-legacy-doc-file references. Both operate over the full docs/
# directory listing (not just the caller's prefix-filtered files) so a link
# from an agent doc to a removed RAG doc is still caught.
# ---------------------------------------------------------------------------

_MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_BARE_MD_FILENAME_RE = re.compile(r"`([0-9]{2}_[a-z0-9_-]+\.md)`")
_HISTORICAL_MARKERS: frozenset[str] = frozenset(
    {
        "legacy",
        "historical",
        "archive only",
        "resolved",
        "was:",
        "removed",
        "削除済み",
        "旧",
    }
)


def _split_link_target(target: str) -> tuple[str, str | None]:
    """Split a link target into (file_part, anchor_part_or_None)."""
    if "#" in target:
        file_part, _, anchor = target.partition("#")
        return file_part, anchor
    return target, None


def is_historical_line(line: str) -> bool:
    """True if *line* explicitly marks its content as historical/removed context."""
    lowered = line.lower()
    return any(marker.lower() in lowered for marker in _HISTORICAL_MARKERS)


def check_broken_internal_links(docs_dir: Path, files: list[DocFile]) -> list[Issue]:
    """Flag [text](path.md) / [text](path.md#anchor) links that don't resolve."""
    issues: list[Issue] = []
    existing_files = {f.name for f in docs_dir.glob("*.md")}

    for doc in files:
        for line_no, line in enumerate(doc.lines, start=1):
            for match in _MD_LINK_RE.finditer(line):
                target = match.group(1).strip()
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                file_part, _anchor = _split_link_target(target)
                if not file_part:
                    continue  # pure "#anchor" link within the same page
                if "/" in file_part:
                    continue  # relative paths outside docs/ are out of scope
                if file_part not in existing_files:
                    issues.append(
                        Issue(
                            file=doc.rel_path,
                            line_no=line_no,
                            severity="ERROR",
                            message=(
                                f"broken internal link target {file_part!r} "
                                f"(referenced doc file does not exist under docs/)"
                            ),
                        )
                    )
    return issues


def check_removed_file_references(docs_dir: Path, files: list[DocFile]) -> list[Issue]:
    """Flag inline-code-quoted `NN_doc_name.md` mentions of files that don't exist.

    Skips lines explicitly marked as historical -- this doc set's established
    convention for intentionally naming a removed file as migration context.
    """
    issues: list[Issue] = []
    existing_files = {f.name for f in docs_dir.glob("*.md")}

    for doc in files:
        for line_no, line in enumerate(doc.lines, start=1):
            if is_historical_line(line):
                continue
            for match in _BARE_MD_FILENAME_RE.finditer(line):
                filename = match.group(1)
                if filename not in existing_files:
                    issues.append(
                        Issue(
                            file=doc.rel_path,
                            line_no=line_no,
                            severity="ERROR",
                            message=(
                                f"reference to removed/nonexistent doc file `{filename}`"
                            ),
                        )
                    )
    return issues


# ---------------------------------------------------------------------------
# Directory-listing completeness — a doc that hand-enumerates a directory's
# entries (a file tree, an ownership table, ...) drifts whenever an entry is
# added on disk without updating the doc. Callers do their own doc-specific
# extraction (table rows, ASCII tree branches, ...) and pass the resulting
# name set here; this only does the "compare against disk" half so the
# comparison logic isn't reimplemented per caller.
# ---------------------------------------------------------------------------


def check_directory_listing_completeness(
    rel_doc_path: str,
    line_no: int,
    listed_names: frozenset[str],
    actual_dir: Path,
    *,
    label: str | None = None,
) -> list[Issue]:
    """Flag directory entries that exist on disk but are absent from *listed_names*.

    Best-effort: returns [] if *actual_dir* does not exist rather than raising,
    since a doc describing a since-removed directory is a different kind of
    drift (covered by check_removed_file_references-style checks).
    """
    if not actual_dir.is_dir():
        return []
    actual_names = {p.name for p in actual_dir.iterdir()}
    missing = sorted(actual_names - listed_names)
    if not missing:
        return []
    where = label or str(actual_dir)
    return [
        Issue(
            file=rel_doc_path,
            line_no=line_no,
            severity="WARNING",
            message=(
                f"directory listing for {where} omits entries present on "
                f"disk: {missing}"
            ),
        )
    ]


# ---------------------------------------------------------------------------
# Slash-command drift vs command_defs_list.py's _COMMANDS — shared because
# both Agent and MCP docs cite REPL slash commands.
# ---------------------------------------------------------------------------

_COMMAND_DEF_RE = re.compile(r'CommandDef\(\s*"(/[a-z][a-z0-9_]*)"')
_DOC_SLASH_COMMAND_RE = re.compile(
    r"(?<![`/a-zA-Z0-9])/(mcp|db|debug|audit|memory|mdq|rag|help|config|"
    r"stats|set|reload|context|compact|system|session|clear|undo|history|"
    r"export|plan|approve|reject|skill)(?:[- ][a-z][a-z0-9_-]*)?\b"
)


def extract_registered_command_names(repo_root: Path) -> frozenset[str] | None:
    """Regex-extract slash command names from command_defs_list.py's CommandDef(...) calls.

    Returns None if the source file cannot be found (best-effort; the caller
    should skip the check rather than fail noisily).
    """
    src = repo_root / "scripts" / "agent" / "commands" / "command_defs_list.py"
    if not src.is_file():
        return None
    content = src.read_text(encoding="utf-8")
    return frozenset(_COMMAND_DEF_RE.findall(content))


def check_command_drift(
    docs_dir: Path, files: list[DocFile], repo_root: Path
) -> list[Issue]:
    """Flag doc-referenced /command names not present in _COMMANDS (WARNING).

    Best-effort: only checks a fixed set of command-name keywords (see
    _DOC_SLASH_COMMAND_RE) to avoid false positives on generic paths like
    "/opt/llm" or URL paths that happen to start with a slash. Skips lines
    marked historical -- this doc set's established convention for citing a
    removed command as migration context. Also matches multi-word commands
    (e.g. "/session rag-consistency", "/db rag rebuild-fts") by capturing
    trailing hyphen/space-joined subcommand tokens and checking both the
    bare command and progressively shorter prefixes against the registry.
    """
    registered = extract_registered_command_names(repo_root)
    if registered is None:
        return []

    issues: list[Issue] = []
    for doc in files:
        for line_no, line in enumerate(doc.lines, start=1):
            if is_historical_line(line):
                continue
            for match in _DOC_SLASH_COMMAND_RE.finditer(line):
                full = match.group(0)
                base = f"/{match.group(1)}"
                if base == "/exit":
                    continue  # REPL-reserved, not in _COMMANDS by design
                # A command is "known" if either the full multi-word form or
                # its base verb is registered — registries only track the
                # base verb (e.g. "/session"), while docs may cite a
                # subcommand (e.g. "/session rag-consistency").
                if base in registered:
                    continue
                if full in registered:
                    continue
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=line_no,
                        severity="WARNING",
                        message=(
                            f"doc references {full!r} whose base command "
                            f"{base!r} is not a registered command in "
                            f"_COMMANDS (command_defs_list.py)"
                        ),
                    )
                )
    return issues


# ---------------------------------------------------------------------------
# scripts/-path and function()-reference existence -- shared because any
# domain's docs cite `scripts/...` file paths and `func_name()` calls, not
# just MCP's. Moved here from check_mcp_docs_consistency.py so
# check_rag_docs_consistency.py (and future domain checkers) can reuse them
# instead of re-implementing the same regex-vs-live-code comparison.
# ---------------------------------------------------------------------------

_PATH_REF_RE = re.compile(
    r"`((?:scripts|config|docs)/[A-Za-z0-9_./-]+\.[a-z]+)(?::(\d+))?`"
)


def check_file_path_references(
    docs_dir: Path, files: list[DocFile], repo_root: Path
) -> list[Issue]:
    """Flag backtick-quoted `scripts/...`, `config/...`, `docs/...` paths that don't exist.

    When a `path:LINE` form is used, also flags the reference if the target
    file has fewer than LINE lines (a weak but zero-false-positive check for
    stale line-number citations; it cannot confirm the line still contains
    the claimed content).
    """
    issues: list[Issue] = []
    for doc in files:
        for line_no, line in enumerate(doc.lines, start=1):
            if is_historical_line(line):
                continue
            for match in _PATH_REF_RE.finditer(line):
                rel_path, line_ref = match.group(1), match.group(2)
                target = repo_root / rel_path
                if not target.is_file():
                    issues.append(
                        Issue(
                            file=doc.rel_path,
                            line_no=line_no,
                            severity="WARNING",
                            message=(
                                f"doc references `{rel_path}` which does not "
                                f"exist in the repository (best-effort check; "
                                f"verify manually)"
                            ),
                        )
                    )
                    continue
                if line_ref is not None:
                    try:
                        actual_lines = len(
                            target.read_text(encoding="utf-8").splitlines()
                        )
                    except OSError:
                        continue
                    if int(line_ref) > actual_lines:
                        issues.append(
                            Issue(
                                file=doc.rel_path,
                                line_no=line_no,
                                severity="WARNING",
                                message=(
                                    f"doc references `{rel_path}:{line_ref}` "
                                    f"but the file only has {actual_lines} "
                                    f"lines (stale line-number citation)"
                                ),
                            )
                        )
    return issues


_FUNC_REF_RE = re.compile(
    r"`(?:[a-zA-Z_][a-zA-Z0-9_]*\.)?([a-zA-Z_][a-zA-Z0-9_]{3,})\(\)`"
)
_FUNC_DEF_RE = re.compile(
    r"^\s*(?:async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", re.MULTILINE
)


def extract_defined_function_names(repo_root: Path) -> frozenset[str]:
    """Regex-extract every `def name(` (sync or async, function or method) under scripts/."""
    found: set[str] = set()
    scripts_dir = repo_root / "scripts"
    if not scripts_dir.is_dir():
        return frozenset()
    for py_file in scripts_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        found.update(_FUNC_DEF_RE.findall(content))
    return frozenset(found)


def check_function_references(
    docs_dir: Path, files: list[DocFile], repo_root: Path
) -> list[Issue]:
    """Flag backtick-quoted `func_name()` / `Class.method_name()` mentions with no matching `def`.

    Best-effort: only catches a function/method name that is entirely absent
    from the codebase (e.g. renamed or never existed); cannot verify that a
    still-existing function of that name lives where the doc claims, and
    cannot distinguish same-named methods on different classes.
    """
    defined = extract_defined_function_names(repo_root)
    if not defined:
        return []

    issues: list[Issue] = []
    for doc in files:
        for line_no, line in enumerate(doc.lines, start=1):
            if is_historical_line(line):
                continue
            for match in _FUNC_REF_RE.finditer(line):
                name = match.group(1)
                if name not in defined:
                    issues.append(
                        Issue(
                            file=doc.rel_path,
                            line_no=line_no,
                            severity="WARNING",
                            message=(
                                f"doc references `{name}()` which is not "
                                f"defined anywhere under scripts/ (best-effort "
                                f"check; verify manually)"
                            ),
                        )
                    )
    return issues


# ---------------------------------------------------------------------------
# CLI reporting helper
# ---------------------------------------------------------------------------


def report_and_exit(all_issues: list[Issue]) -> int:
    """Print issues sorted by (file, line), summarize, and return the exit code."""
    errors = [i for i in all_issues if i.severity == "ERROR"]
    warnings = [i for i in all_issues if i.severity == "WARNING"]
    if all_issues:
        for issue in sorted(all_issues, key=lambda i: (i.file, i.line_no)):
            print(f"[{issue.severity}] {issue.file}:{issue.line_no}: {issue.message}")
        parts = []
        if errors:
            parts.append(f"{len(errors)} error(s)")
        if warnings:
            parts.append(f"{len(warnings)} warning(s)")
        print(f"\nFound {', '.join(parts)}.", file=sys.stderr)
    else:
        print("No issues found.")
    return 1 if errors else 0
