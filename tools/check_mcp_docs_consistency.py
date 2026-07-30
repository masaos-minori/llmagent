#!/usr/bin/env python3
"""check_mcp_docs_consistency.py — Lightweight CI check for MCP documentation drift.

Restored and redesigned after the original tools/check_mcp_docs_consistency.py
was deleted in commit 74906389 ("refactor: remove unsupported MDQ tool/search
surface and stale tool-count doc check"). That commit removed the whole file
to get rid of one check that depended on a hand-maintained, now-obsolete tool
catalog -- but the CI workflow (.github/workflows/mcp-docs-consistency.yml)
and the `check-mcp-docs` entry point in pyproject.toml were never updated,
so "MCP Docs Consistency" has been failing on every docs/**/*.md push since.

This version replaces the old hand-maintained-catalog approach with checks
that read the *live* source of truth (config/agent.toml, scripts/mcp_servers/
TOOL_LIST definitions, scripts/agent/commands/command_defs_list.py) so a
future server/tool/command rename cannot silently make the check itself
stale the way the old catalog did.

Shares its DocFile/Issue dataclasses, file discovery, and generic checks
(broken links, removed-file references, slash-command drift) with
tools/check_agent_docs_consistency.py via tools/_docs_consistency_lib.py.

Checks:
    --all (default)        Run all checks
    --skip links            Skip broken internal Markdown link detection
    --skip removedfiles     Skip removed-legacy-doc-file reference check
    --skip commanddrift     Skip slash-command drift vs command_defs_list.py (WARNING)
    --skip portdrift        Skip MCP server port drift vs config/agent.toml (ERROR)
    --skip tooldrift         Skip tool-name drift vs live TOOL_LIST definitions (WARNING)
    --skip filerefs          Skip scripts/-path reference existence check (WARNING)
    --skip funcrefs          Skip backtick-quoted function()-reference existence check (WARNING)

Usage:
    python tools/check_mcp_docs_consistency.py                 # run all
    python tools/check_mcp_docs_consistency.py --skip portdrift
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

if __package__ in (None, ""):
    # Allow `python tools/check_mcp_docs_consistency.py` (script form, as
    # used by .github/workflows/mcp-docs-consistency.yml) in addition to
    # `python -m tools.check_mcp_docs_consistency` / the pyproject.toml
    # console-script entry point, both of which set up the package import
    # path automatically.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._docs_consistency_lib import (
    DocFile,
    Issue,
    check_broken_internal_links,
    check_command_drift,
    check_removed_file_references,
    discover_md_files,
    is_historical_line,
    report_and_exit,
)

# ---------------------------------------------------------------------------
# Check: MCP server port drift vs config/agent.toml (ERROR)
# ---------------------------------------------------------------------------

_URL_PORT_RE = re.compile(r":(\d{2,5})\"?\s*$")
_DOC_PORT_RE = re.compile(r"\b(\d{4})\b")


def _extract_authoritative_ports(repo_root: Path) -> dict[str, str] | None:
    """Return {canonical-doc-server-name: port} from config/agent.toml's [mcp_servers.*].

    The canonical doc name follows this repo's established convention of
    writing server keys as hyphenated "<key>-mcp" (e.g. "web_search" ->
    "web-search-mcp", "file_read" -> "file-read-mcp"). Returns None if the
    config file is missing or unparsable (best-effort; caller should skip).
    """
    cfg_path = repo_root / "config" / "agent.toml"
    if not cfg_path.is_file():
        return None
    try:
        with cfg_path.open("rb") as f:
            cfg = tomllib.load(f)
    except (tomllib.TOMLDecodeError, OSError):
        return None

    servers = cfg.get("mcp_servers")
    if not isinstance(servers, dict):
        return None

    ports: dict[str, str] = {}
    for key, section in servers.items():
        if not isinstance(section, dict):
            continue
        url = section.get("url")
        if not isinstance(url, str):
            continue
        match = _URL_PORT_RE.search(url)
        if not match:
            continue
        doc_name = f"{key.replace('_', '-')}-mcp"
        ports[doc_name] = match.group(1)
    return ports or None


def check_port_drift(
    docs_dir: Path, files: list[DocFile], repo_root: Path
) -> list[Issue]:
    """Flag a doc-mentioned port next to a server name that disagrees with config.

    Best-effort, same-line heuristic: a line is only checked when it contains
    both a known "<name>-mcp" token and a bare 4-digit number in the 8000s
    port range. Skips historical lines.
    """
    authoritative = _extract_authoritative_ports(repo_root)
    if authoritative is None:
        return []

    name_res = {
        name: re.compile(rf"(?<![a-z-]){re.escape(name)}(?![a-z-])")
        for name in authoritative
    }

    issues: list[Issue] = []
    for doc in files:
        for line_no, line in enumerate(doc.lines, start=1):
            if is_historical_line(line):
                continue
            for name, pattern in name_res.items():
                if not pattern.search(line):
                    continue
                expected = authoritative[name]
                for port_match in _DOC_PORT_RE.finditer(line):
                    mentioned = port_match.group(1)
                    if not mentioned.startswith("80"):
                        continue  # not in this project's MCP port range
                    if mentioned != expected:
                        issues.append(
                            Issue(
                                file=doc.rel_path,
                                line_no=line_no,
                                severity="ERROR",
                                message=(
                                    f"doc pairs {name!r} with port "
                                    f"{mentioned!r}, but config/agent.toml "
                                    f"assigns it port {expected!r}"
                                ),
                            )
                        )
    return issues


# ---------------------------------------------------------------------------
# Check: tool-name drift vs live TOOL_LIST definitions (WARNING)
# ---------------------------------------------------------------------------

_TOOL_LIST_NAME_RE = re.compile(r'\{\s*"name":\s*"([a-z][a-z0-9_]*)"')
_TOOL_ENUM_LINE_RE = re.compile(r"(?:ツール|Tools?)\s*[:：]\s*(.+)")
_BACKTICK_IDENT_RE = re.compile(r"`([a-z][a-z0-9_]*)`")


def _extract_live_tool_names(repo_root: Path) -> frozenset[str]:
    """Regex-extract every `"name": "..."` tool-schema entry under scripts/mcp_servers/.

    Scans all .py files (not just files matching a *_tools.py naming
    convention) because at least one server (github-mcp) assembles its
    TOOL_LIST from several domain-split modules with other filenames.
    """
    found: set[str] = set()
    servers_dir = repo_root / "scripts" / "mcp_servers"
    if not servers_dir.is_dir():
        return frozenset()
    for py_file in servers_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        found.update(_TOOL_LIST_NAME_RE.findall(content))
    return frozenset(found)


def check_tool_name_drift(
    docs_dir: Path, files: list[DocFile], repo_root: Path
) -> list[Issue]:
    """Flag backtick tool names on a "ツール:"/"Tools:" line not in any live TOOL_LIST.

    Best-effort: only inspects lines using this doc set's established
    "ツール: `a`, `b`, ..." / "Tools: `a`, `b`, ..." enumeration phrasing, and
    checks each name against the *union* of tool names across all MCP
    servers (not attributed to a specific server) to avoid needing a
    doc-name-to-server mapping for this check.
    """
    live_names = _extract_live_tool_names(repo_root)
    if not live_names:
        return []

    issues: list[Issue] = []
    for doc in files:
        for line_no, line in enumerate(doc.lines, start=1):
            if is_historical_line(line):
                continue
            enum_match = _TOOL_ENUM_LINE_RE.search(line)
            if not enum_match:
                continue
            for ident_match in _BACKTICK_IDENT_RE.finditer(enum_match.group(1)):
                name = ident_match.group(1)
                if "_" not in name:
                    continue  # too generic (e.g. a bare English word) to be a tool name
                if name not in live_names:
                    issues.append(
                        Issue(
                            file=doc.rel_path,
                            line_no=line_no,
                            severity="WARNING",
                            message=(
                                f"doc lists `{name}` as a tool, but no "
                                f"scripts/mcp_servers/**/*.py TOOL_LIST "
                                f"defines a tool with that name (best-effort "
                                f"check; verify manually)"
                            ),
                        )
                    )
    return issues


# ---------------------------------------------------------------------------
# Check: scripts/-path reference existence (WARNING)
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


# ---------------------------------------------------------------------------
# Check: backtick-quoted function()-reference existence (WARNING)
# ---------------------------------------------------------------------------

_FUNC_REF_RE = re.compile(r"`([a-zA-Z_][a-zA-Z0-9_]{3,})\(\)`")
_FUNC_DEF_RE = re.compile(
    r"^\s*(?:async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", re.MULTILINE
)


def _extract_defined_function_names(repo_root: Path) -> frozenset[str]:
    """Regex-extract every `def name(` (sync or async) under scripts/."""
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
    """Flag backtick-quoted `func_name()` mentions with no matching `def` under scripts/.

    Best-effort: only catches a function name that is entirely absent from
    the codebase (e.g. renamed or never existed); cannot verify that a
    still-existing function of that name lives where the doc claims.
    """
    defined = _extract_defined_function_names(repo_root)
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
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check MCP documentation consistency.",
    )
    parser.add_argument(
        "--docs-dir",
        default=None,
        help="Path to docs/ directory (default: <repo_root>/docs/)",
    )
    skip_choices = [
        "links",
        "removedfiles",
        "commanddrift",
        "portdrift",
        "tooldrift",
        "filerefs",
        "funcrefs",
    ]
    parser.add_argument(
        "--skip",
        nargs="+",
        choices=skip_choices,
        help="Skip one or more checks",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parent.parent
    docs_dir = Path(args.docs_dir) if args.docs_dir else repo_root / "docs"
    if not docs_dir.is_dir():
        print(f"ERROR: docs directory not found: {docs_dir}", file=sys.stderr)
        return 1

    files = discover_md_files(docs_dir, prefix="04_mcp_")
    if not files:
        print("No 04_mcp_*.md files found in docs/.", file=sys.stderr)
        return 0

    skip = set(args.skip or [])
    all_issues: list[Issue] = []

    if "links" not in skip:
        all_issues.extend(check_broken_internal_links(docs_dir, files))
    if "removedfiles" not in skip:
        all_issues.extend(check_removed_file_references(docs_dir, files))
    if "commanddrift" not in skip:
        all_issues.extend(check_command_drift(docs_dir, files, repo_root))
    if "portdrift" not in skip:
        all_issues.extend(check_port_drift(docs_dir, files, repo_root))
    if "tooldrift" not in skip:
        all_issues.extend(check_tool_name_drift(docs_dir, files, repo_root))
    if "filerefs" not in skip:
        all_issues.extend(check_file_path_references(docs_dir, files, repo_root))
    if "funcrefs" not in skip:
        all_issues.extend(check_function_references(docs_dir, files, repo_root))

    return report_and_exit(all_issues)


if __name__ == "__main__":
    sys.exit(main())
