#!/usr/bin/env python3
"""check_docs_consistency.py — Unified docs consistency checker for all domains.

Consolidated from:
  - tools/check_agent_docs_consistency.py
  - tools/check_mcp_docs_consistency.py
  - tools/check_rag_docs_consistency.py
  - tools/check_deployment_docs_consistency.py
  - tools/check_overview_docs_consistency.py

Shares its DocFile/Issue dataclasses, file discovery, and generic checks
(broken links, removed-file references, slash-command drift, file-path refs,
function-name refs, directory-listing completeness) with all domains via
tools/_docs_consistency_lib.py.

Usage:
    python tools/check_docs_consistency.py --domain agent              # check agent docs
    python tools/check_docs_consistency.py --domain mcp                # check mcp docs
    python tools/check_docs_consistency.py --domain rag                # check rag docs
    python tools/check_docs_consistency.py --domain deployment         # check deployment docs
    python tools/check_docs_consistency.py --domain overview           # check overview docs
    python tools/check_docs_consistency.py --domain agent --skip schemadrift  # skip a check
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    # Allow `python tools/check_docs_consistency.py` (script form) in addition
    # to `python -m tools.check_docs_consistency` / pyproject.toml console-script
    # entry point, both of which set up the package import path automatically.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._docs_consistency_lib import (
    DocFile,
    Issue,
    check_broken_internal_links,
    check_command_drift,
    check_directory_listing_completeness,
    check_file_path_references,
    check_function_references,
    check_removed_file_references,
    discover_md_files,
    extract_registered_command_names,
    is_historical_line,
    report_and_exit,
)

# ---------------------------------------------------------------------------
# Domain configuration
# ---------------------------------------------------------------------------

DOMAIN_PREFIXES: dict[str, str] = {
    "agent": "05_agent_",
    "mcp": "04_mcp_",
    "rag": "03_rag_",
    "deployment": "02_deployment",
    "overview": "01_overview",
}

# After docs reorganization (issue docsreorg02), domain files live in subfolders.
# This maps domain names to the subfolder path relative to docs/.
DOMAIN_SUBFOLDERS: dict[str, str] = {
    "agent": "23_agent",
    "mcp": "22_mcp",
    "rag": "21_rag",
    "deployment": "90_deployment",
    "overview": "01_overview",
}

# Which generic checks each domain runs (generic = shared across domains).
DOMAIN_GENERIC_CHECKS: dict[str, frozenset[str]] = {
    "agent": frozenset({"links", "removedfiles", "commanddrift"}),
    "mcp": frozenset({"links", "removedfiles", "commanddrift", "filerefs", "funcrefs"}),
    "rag": frozenset({"links", "removedfiles", "commanddrift", "filerefs", "funcrefs"}),
    "deployment": frozenset(),
    "overview": frozenset(),
}

ALL_SKIP_OPTIONS: frozenset[str] = frozenset(
    {
        "links",
        "removedfiles",
        "commanddrift",
        "commandcoverage",
        "commandcontract",
        "filerefs",
        "funcrefs",
        "schemadrift",
        "diagnostics",
        "portdrift",
        "tooldrift",
        "crawlerconfig",
        "debugoutput",
        "dbcount",
        "dbtable",
        "configkey",
        "portrange",
        "conflisting",
    }
)

REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Shared helpers (used by multiple domains)
# ---------------------------------------------------------------------------

_URL_PORT_RE = re.compile(r":(\d{2,5})\"?\s*$")


def _extract_authoritative_ports(repo_root: Path) -> dict[str, str] | None:
    """Return {canonical-doc-server-name: port} from config/agent.toml's [mcp_servers.*].

    The canonical doc name follows this repo's established convention of
    writing server keys as hyphenated "<key>-mcp" (e.g. "web_search" ->
    "web-search-mcp"). Returns None if the config file is missing or unparsable.
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


# ---------------------------------------------------------------------------
# Check: DB-schema drift vs schema_sql.py (Agent domain, best-effort)
# ---------------------------------------------------------------------------

_CREATE_TABLE_RE = re.compile(
    r"CREATE (?:VIRTUAL )?TABLE(?: IF NOT EXISTS)? ([a-z_][a-z0-9_]*)",
    re.IGNORECASE,
)
_DOC_TABLE_MENTION_RE = re.compile(r"`([a-z_][a-z0-9_]*)`\s*テーブル")


def _extract_schema_table_names(repo_root: Path) -> frozenset[str] | None:
    src = repo_root / "scripts" / "db" / "schema_sql.py"
    if not src.is_file():
        return None
    content = src.read_text(encoding="utf-8")
    return frozenset(_CREATE_TABLE_RE.findall(content))


def check_schema_drift(docs_dir: Path, repo_root: Path) -> list[Issue]:
    table_names = _extract_schema_table_names(repo_root)
    if table_names is None:
        return []

    issues: list[Issue] = []
    target_files = discover_md_files(
        docs_dir / "40_shared", prefix="90_shared_04_"
    ) + discover_md_files(docs_dir / "23_agent", prefix="05_agent_09_")
    for doc in target_files:
        for line_no, line in enumerate(doc.lines, start=1):
            for match in _DOC_TABLE_MENTION_RE.finditer(line):
                name = match.group(1)
                if name not in table_names:
                    issues.append(
                        Issue(
                            file=doc.rel_path,
                            line_no=line_no,
                            severity="WARNING",
                            message=(
                                f"doc mentions table `{name}` which does not "
                                f"appear in schema_sql.py's CREATE TABLE "
                                f"statements (best-effort check; verify manually)"
                            ),
                        )
                    )
    return issues


# ---------------------------------------------------------------------------
# Check: slash-command coverage vs command_defs_list.py's _COMMANDS (Agent domain, ERROR)
# ---------------------------------------------------------------------------

_COMMAND_INDEX_DOC = "agent_07_03_"
_COMMAND_CHAPTER_DOCS = ("agent_07_07_", "agent_07_08_", "agent_07_09_", "agent_07_10_")
_INDEX_ROW_RE = re.compile(r"^\|\s*`(/[a-z][a-z0-9_]*)`\s*\|")
# REPL-reserved: handled by the REPL itself, so absent from _COMMANDS by design.
_REPL_RESERVED_COMMANDS = frozenset({"/exit"})


def check_command_coverage(docs_dir: Path, repo_root: Path) -> list[Issue]:
    """Flag command-name mismatches between _COMMANDS and the Agent command docs.

    Covers command names only (not subcommands or arguments): every registered
    command must appear in the Built-in Command Index of agent_07_03 and be
    mentioned in at least one per-command chapter (agent_07_07 to agent_07_10),
    and every index row must name a registered or REPL-reserved command.
    """
    registered = extract_registered_command_names(repo_root)
    if registered is None:
        return []

    agent_dir = docs_dir / DOMAIN_SUBFOLDERS["agent"]
    index_docs = discover_md_files(agent_dir, prefix=_COMMAND_INDEX_DOC)
    chapters = [
        doc
        for prefix in _COMMAND_CHAPTER_DOCS
        for doc in discover_md_files(agent_dir, prefix=prefix)
    ]
    issues: list[Issue] = []

    indexed: set[str] = set()
    for doc in index_docs:
        for line_no, line in enumerate(doc.lines, start=1):
            match = _INDEX_ROW_RE.match(line)
            if not match:
                continue
            name = match.group(1)
            indexed.add(name)
            if name not in registered and name not in _REPL_RESERVED_COMMANDS:
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=line_no,
                        severity="ERROR",
                        message=(
                            f"command index lists {name!r}, which is not "
                            f"registered in _COMMANDS (command_defs_list.py)"
                        ),
                    )
                )

    index_file = index_docs[0].rel_path if index_docs else _COMMAND_INDEX_DOC
    chapter_text = "\n".join(line for doc in chapters for line in doc.lines)
    for name in sorted(registered):
        if index_docs and name not in indexed:
            issues.append(
                Issue(
                    file=index_file,
                    line_no=0,
                    severity="ERROR",
                    message=(
                        f"registered command {name!r} is missing from the "
                        f"Built-in Command Index"
                    ),
                )
            )
        if not re.search(rf"(?<![\w/]){re.escape(name)}(?![\w-])", chapter_text):
            issues.append(
                Issue(
                    file=index_file,
                    line_no=0,
                    severity="ERROR",
                    message=(
                        f"registered command {name!r} is not described in any "
                        f"per-command chapter (agent_07_07 to agent_07_10)"
                    ),
                )
            )
    return issues


# ---------------------------------------------------------------------------
# Check: subcommand / argument contract vs the structured registry (Agent, ERROR)
# ---------------------------------------------------------------------------

# Commands whose documented contract is known to differ from the registry; each is
# tracked as a Known Issue and excluded until it is resolved (remove the entry then).
_CONTRACT_EXEMPT_COMMANDS: dict[str, str] = {"/memory": "AGENT-013"}
_CODE_SPAN_RE = re.compile(r"`([^`\n]+)`")


def _load_registered_commands(repo_root: Path) -> list[Any] | None:
    """Import _COMMANDS from command_defs_list.py; None when it cannot be imported."""
    scripts_dir = repo_root / "scripts"
    if not (scripts_dir / "agent" / "commands" / "command_defs_list.py").is_file():
        return None
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    try:
        from agent.commands.command_defs_list import _COMMANDS  # noqa: PLC0415
    except ImportError:
        return None
    return list(_COMMANDS)


def _default_documented(blocks: list[list[str]], usage: str, default: str) -> bool:
    """True when the block holding usage (or the one after it) states the default."""
    pattern = re.compile(rf"default[^\n]*{re.escape(default)}", re.IGNORECASE)
    for index, block in enumerate(blocks):
        if any(usage in line.replace("\\|", "|") for line in block):
            window = block + (blocks[index + 1] if index + 1 < len(blocks) else [])
            return bool(pattern.search("\n".join(window)))
    return False


def check_command_contracts(docs_dir: Path, repo_root: Path) -> list[Issue]:
    """Flag subcommand and argument drift between _COMMANDS and the command chapters.

    The structured registry (CommandDef / SubcommandSpec / ArgSpec) is the canonical
    source. Every usage line it renders must appear as an inline code span in a
    per-command chapter (agent_07_07 to agent_07_10), and every documented
    `/<command> ...` code span must be a registered usage, a registered subcommand
    name, or the bare command. An argument with a default must state it next to its
    usage. Commands listed in _CONTRACT_EXEMPT_COMMANDS are skipped.
    """
    commands = _load_registered_commands(repo_root)
    if commands is None:
        return []
    agent_dir = docs_dir / DOMAIN_SUBFOLDERS["agent"]
    chapters = [
        doc
        for prefix in _COMMAND_CHAPTER_DOCS
        for doc in discover_md_files(agent_dir, prefix=prefix)
    ]
    if not chapters:
        return []
    issues: list[Issue] = []
    active = [c for c in commands if c.name not in _CONTRACT_EXEMPT_COMMANDS]
    by_name = {c.name: c for c in active}
    allowed: dict[str, set[str]] = {}
    for cmd in active:
        names = {cmd.name, *cmd.usages()}
        names.update(f"{cmd.name} {sub.name}" for sub in cmd.subcommands)
        names.update(f"{cmd.name} {arg.token}" for arg in cmd.args)
        allowed[cmd.name] = names

    spans: dict[str, list[tuple[str, int]]] = {}
    blocks_by_file: dict[str, list[list[str]]] = {}
    for doc in chapters:
        blocks: list[list[str]] = [[]]
        for line_no, line in enumerate(doc.lines, start=1):
            if not line.strip():
                blocks.append([])
                continue
            blocks[-1].append(line)
            for match in _CODE_SPAN_RE.finditer(line):
                text = match.group(1).replace("\\|", "|").strip()
                spans.setdefault(doc.rel_path, []).append((text, line_no))
        blocks_by_file[doc.rel_path] = blocks

    documented = {text for entries in spans.values() for text, _ in entries}
    index_file = chapters[0].rel_path
    for cmd in active:
        for sub_usage, spec_args in _usage_pairs(cmd):
            if sub_usage not in documented:
                issues.append(
                    Issue(
                        file=index_file,
                        line_no=0,
                        severity="ERROR",
                        message=(
                            f"registered usage `{sub_usage}` is not documented in "
                            f"any per-command chapter (agent_07_07 to agent_07_10)"
                        ),
                    )
                )
                continue
            for arg in spec_args:
                if arg.default is None:
                    continue
                if not any(
                    _default_documented(blocks, sub_usage, arg.default)
                    for blocks in blocks_by_file.values()
                ):
                    issues.append(
                        Issue(
                            file=index_file,
                            line_no=0,
                            severity="ERROR",
                            message=(
                                f"`{sub_usage}`: default {arg.default!r} of argument "
                                f"{arg.token!r} is not stated next to its usage"
                            ),
                        )
                    )

    for rel_path, entries in spans.items():
        for text, line_no in entries:
            head = text.split(" ", 1)[0]
            cmd_def = by_name.get(head)
            if cmd_def is None or text in allowed[head]:
                continue
            issues.append(
                Issue(
                    file=rel_path,
                    line_no=line_no,
                    severity="ERROR",
                    message=(
                        f"documented form `{text}` is not a registered usage of "
                        f"{head} (subcommand or argument drift against _COMMANDS)"
                    ),
                )
            )
    return issues


def _usage_pairs(cmd: Any) -> list[tuple[str, tuple[Any, ...]]]:
    """Return (usage line, ArgSpecs) for each form of a registered command."""
    from agent.commands.command_defs import format_usage  # noqa: PLC0415

    if cmd.subcommands:
        return [
            (format_usage(cmd.name, sub.name, sub.args), sub.args)
            for sub in cmd.subcommands
        ]
    return [(format_usage(cmd.name, "", cmd.args), cmd.args)]


# ---------------------------------------------------------------------------
# Check: Obsolete diagnostics / audit-event references (Agent domain, best-effort)
# ---------------------------------------------------------------------------

_EVENT_KIND_DEF_RE = re.compile(
    r'(?:"event":\s*"([a-z_]+)"|event\s*=\s*"([a-z_]+)"|kind\s*=\s*"([a-z_]+)"'
    r'|\.save\(\s*[^,]+,\s*"([a-z_]+)"\s*,)'
)
_DOC_EVENT_MENTION_RE = re.compile(r'"event":\s*"([a-z_]+)"|kind="([a-z_]+)"')


def _extract_known_event_kinds(repo_root: Path) -> frozenset[str]:
    found: set[str] = set()
    agent_dir = repo_root / "scripts" / "agent"
    if not agent_dir.is_dir():
        return frozenset()
    for py_file in agent_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for match in _EVENT_KIND_DEF_RE.finditer(content):
            for group in match.groups():
                if group:
                    found.add(group)
    return frozenset(found)


def check_obsolete_diagnostics_references(
    docs_dir: Path, files: list[DocFile], repo_root: Path
) -> list[Issue]:
    known = _extract_known_event_kinds(repo_root)
    if not known:
        return []

    issues: list[Issue] = []
    for doc in files:
        for line_no, line in enumerate(doc.lines, start=1):
            for match in _DOC_EVENT_MENTION_RE.finditer(line):
                name = match.group(1) or match.group(2)
                if name and name not in known:
                    issues.append(
                        Issue(
                            file=doc.rel_path,
                            line_no=line_no,
                            severity="WARNING",
                            message=(
                                f"doc references event/diagnostic kind "
                                f"{name!r} not found as a string literal "
                                f"under scripts/agent/ (best-effort check; "
                                f"verify manually)"
                            ),
                        )
                    )
    return issues


# ---------------------------------------------------------------------------
# Check: MCP server port drift vs config/agent.toml (MCP domain, ERROR)
# ---------------------------------------------------------------------------

_DOC_PORT_RE = re.compile(r"\b(\d{4})\b")


def check_port_drift(
    docs_dir: Path, files: list[DocFile], repo_root: Path
) -> list[Issue]:
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
                        continue
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
# Check: tool-name drift vs live TOOL_LIST definitions (MCP domain, WARNING)
# ---------------------------------------------------------------------------

_TOOL_LIST_NAME_RE = re.compile(r'\{\s*"name":\s*"([a-z][a-z0-9_]*)"')
_TOOL_ENUM_LINE_RE = re.compile(r"(?:ツール|Tools?)\s*[:：]\s*(.+)")
_BACKTICK_IDENT_RE = re.compile(r"`([a-z][a-z0-9_]*)`")


def _extract_live_tool_names(repo_root: Path) -> frozenset[str]:
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
                    continue
                if name.endswith("_"):
                    continue  # a name prefix (e.g. "github_"), not a tool name
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
# Check: crawler max_depth/max_pages claim vs config/crawler.toml (RAG domain, ERROR)
# ---------------------------------------------------------------------------

_CRAWLER_TOML = REPO_ROOT / "config" / "crawler.toml"
_HOP_CLAIM_RE = re.compile(r"最大\s*(\d+)\s*ホップ")
_PAGE_CLAIM_RE = re.compile(r"最大\s*(\d+)\s*ページ")


def _crawler_config_values(repo_root: Path) -> tuple[int, int] | None:
    if not _CRAWLER_TOML.is_file():
        return None
    with _CRAWLER_TOML.open("rb") as f:
        cfg = tomllib.load(f)
    max_depth = cfg.get("max_depth")
    max_pages = cfg.get("max_pages")
    if not isinstance(max_depth, int) or not isinstance(max_pages, int):
        return None
    return max_depth, max_pages


def check_crawler_config_drift(
    docs_dir: Path, files: list[DocFile], repo_root: Path
) -> list[Issue]:
    values = _crawler_config_values(repo_root)
    if values is None:
        return []
    max_depth, max_pages = values

    issues: list[Issue] = []
    for doc in files:
        for line_no, line in enumerate(doc.lines, start=1):
            if is_historical_line(line):
                continue
            hop_match = _HOP_CLAIM_RE.search(line)
            if hop_match and int(hop_match.group(1)) != max_depth:
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=line_no,
                        severity="ERROR",
                        message=(
                            f"claims max depth {hop_match.group(1)!r} hops, but "
                            f"config/crawler.toml sets max_depth={max_depth}"
                        ),
                    )
                )
            page_match = _PAGE_CLAIM_RE.search(line)
            if page_match and int(page_match.group(1)) != max_pages:
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=line_no,
                        severity="ERROR",
                        message=(
                            f"claims max {page_match.group(1)!r} pages, but "
                            f"config/crawler.toml sets max_pages={max_pages}"
                        ),
                    )
                )
    return issues


# ---------------------------------------------------------------------------
# Check: fabricated `[debug] ...` output example (RAG domain, ERROR)
# ---------------------------------------------------------------------------

_DEBUG_OUTPUT_RE = re.compile(r"`(\[debug\][^`]*)`")


def check_debug_output_existence(
    docs_dir: Path, files: list[DocFile], repo_root: Path
) -> list[Issue]:
    scripts_dir = repo_root / "scripts"
    if not scripts_dir.is_dir():
        return []
    exists_in_code = any(
        "[debug]" in py_file.read_text(encoding="utf-8")
        for py_file in scripts_dir.rglob("*.py")
    )
    if exists_in_code:
        return []

    issues: list[Issue] = []
    for doc in files:
        for line_no, line in enumerate(doc.lines, start=1):
            if is_historical_line(line):
                continue
            for match in _DEBUG_OUTPUT_RE.finditer(line):
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=line_no,
                        severity="ERROR",
                        message=(
                            f"quotes literal output {match.group(1)[:60]!r}, but "
                            f"the string '[debug]' does not appear anywhere "
                            f"under scripts/ (fabricated example output)"
                        ),
                    )
                )
    return issues


# ---------------------------------------------------------------------------
# Check: "N SQLite databases" claim vs actual DbConfig field count (Deployment domain, ERROR)
# ---------------------------------------------------------------------------

_DB_CONFIG_SRC = REPO_ROOT / "scripts" / "db" / "config.py"
_NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
}
_DB_COUNT_CLAIM_RE = re.compile(
    r"(?:uses|has)\s+(" + "|".join(_NUMBER_WORDS) + r")\s+SQLite databases?",
    re.IGNORECASE,
)
_TABLE_ROW_SQLITE_RE = re.compile(r"`([a-z]+\.sqlite)`")
_AGENT_TOML = REPO_ROOT / "config" / "agent.toml"
_DEPLOY_DIR = REPO_ROOT / "deploy"
_CONF_D_DOC = "overview_02_files.md"
_CONF_D_DOC_PATH = REPO_ROOT / "docs" / "01_overview" / _CONF_D_DOC
_TREE_BRANCH_RE = re.compile(r"[├└]─\s*([A-Za-z0-9_.-]+)")


def _known_db_names(repo_root: Path) -> list[str]:
    if not _DB_CONFIG_SRC.is_file():
        return []
    content = _DB_CONFIG_SRC.read_text(encoding="utf-8")
    fields = re.findall(r"^\s+(\w+_db_path):\s*str", content, re.MULTILINE)
    return sorted(f"{f.removesuffix('_db_path')}.sqlite" for f in fields)


def check_db_count_claim(
    docs_dir: Path, files: list[DocFile], repo_root: Path
) -> list[Issue]:
    known = _known_db_names(repo_root)
    if not known:
        return []
    issues: list[Issue] = []
    for doc in files:
        for line_no, line in enumerate(doc.lines, start=1):
            match = _DB_COUNT_CLAIM_RE.search(line)
            if not match:
                continue
            declared = _NUMBER_WORDS[match.group(1).lower()]
            if declared != len(known):
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=line_no,
                        severity="ERROR",
                        message=(
                            f"claims {match.group(1)!r} SQLite databases ({declared}), "
                            f"but scripts/db/config.py's DbConfig declares "
                            f"{len(known)}: {', '.join(known)}"
                        ),
                    )
                )
    return issues


# ---------------------------------------------------------------------------
# Check: DB-overview-table completeness (Deployment domain, ERROR)
# ---------------------------------------------------------------------------


def check_db_table_completeness(
    docs_dir: Path, files: list[DocFile], repo_root: Path
) -> list[Issue]:
    known = set(_known_db_names(repo_root))
    if not known:
        return []
    issues: list[Issue] = []
    for doc in files:
        block_start: int | None = None
        found: set[str] = set()
        for line_no, line in enumerate(doc.lines, start=1):
            if line.strip().startswith("|"):
                if block_start is None:
                    block_start = line_no
                found.update(_TABLE_ROW_SQLITE_RE.findall(line))
                continue
            if block_start is not None:
                if len(found) >= 2:
                    missing = sorted(known - found)
                    if missing:
                        issues.append(
                            Issue(
                                file=doc.rel_path,
                                line_no=block_start,
                                severity="ERROR",
                                message=(
                                    f"DB overview table at line {block_start} omits "
                                    f"entries present on disk: {missing}"
                                ),
                            )
                        )
                block_start = None
                found = set()
    return issues


# ---------------------------------------------------------------------------
# Check: cited *_db_path config key presence in agent.toml (Deployment domain, WARNING)
# ---------------------------------------------------------------------------

_DB_PATH_FIELD_RE = re.compile(
    r'^\s+(\w+_db_path):\s*str(?:\s*=\s*"([^"]*)")?', re.MULTILINE
)
_DOC_DB_PATH_RE = re.compile(r"`(\w+_db_path)`")


def _optional_db_path_keys(repo_root: Path) -> frozenset[str]:
    """`*_db_path` keys that `DbConfig` defaults in Python (optional in agent.toml)."""
    src = repo_root / "scripts" / "db" / "config.py"
    if not src.is_file():
        return frozenset()
    content = src.read_text(encoding="utf-8")
    return frozenset(
        key for key, default in _DB_PATH_FIELD_RE.findall(content) if default
    )


def check_config_key_presence(
    docs_dir: Path, files: list[DocFile], repo_root: Path
) -> list[Issue]:
    """Flag cited `*_db_path` keys that agent.toml lacks and DbConfig does not default.

    A key with a Python-level default is optional by design, so citing it
    without a value in agent.toml is not reported.
    """
    if not _AGENT_TOML.is_file():
        return []
    with _AGENT_TOML.open("rb") as f:
        cfg = tomllib.load(f)
    configured_keys = {k for k in cfg.keys() if k.endswith("_db_path")}
    configured_keys |= _optional_db_path_keys(repo_root)

    issues: list[Issue] = []
    for doc in files:
        for line_no, line in enumerate(doc.lines, start=1):
            if is_historical_line(line):
                continue
            for match in _DOC_DB_PATH_RE.finditer(line):
                key = match.group(1)
                if key not in configured_keys:
                    issues.append(
                        Issue(
                            file=doc.rel_path,
                            line_no=line_no,
                            severity="WARNING",
                            message=(
                                f"cites `{key}` as a config key in agent.toml, "
                                f"but it is not set there and DbConfig has no default for it"
                            ),
                        )
                    )
    return issues


# ---------------------------------------------------------------------------
# Check: MCP port range claim vs config/agent.toml (Deployment domain, ERROR)
# ---------------------------------------------------------------------------

_PORT_RANGE_CLAIM_RE = re.compile(r"\b(\d{4})-(\d{4})\b")


def check_port_range_claim(
    docs_dir: Path, files: list[DocFile], repo_root: Path
) -> list[Issue]:
    ports = _extract_authoritative_ports(repo_root)
    if ports is None:
        return []

    # Find the min/max port from authoritative sources.
    all_ports = [int(p) for p in ports.values()]
    if not all_ports:
        return []
    expected_min = min(all_ports)
    expected_max = max(all_ports)

    issues: list[Issue] = []
    for doc in files:
        for line_no, line in enumerate(doc.lines, start=1):
            if is_historical_line(line):
                continue
            match = _PORT_RANGE_CLAIM_RE.search(line)
            if match:
                claimed_min = int(match.group(1))
                claimed_max = int(match.group(2))
                if claimed_min != expected_min or claimed_max != expected_max:
                    issues.append(
                        Issue(
                            file=doc.rel_path,
                            line_no=line_no,
                            severity="ERROR",
                            message=(
                                f"claims MCP port range {claimed_min}-{claimed_max}, "
                                f"but config/agent.toml assigns ports {expected_min}-{expected_max}"
                            ),
                        )
                    )
    return issues


# ---------------------------------------------------------------------------
# Check: conf.d/ directory listing completeness (Overview domain, WARNING)
# ---------------------------------------------------------------------------


def check_conf_d_listing(docs_dir: Path, repo_root: Path) -> list[Issue]:
    doc = None
    for f in _CONF_D_DOC_PATH.parent.glob("*.md"):
        if f.name == _CONF_D_DOC:
            content = f.read_text(encoding="utf-8")
            lines = content.splitlines()
            doc = DocFile(path=f, rel_path=_CONF_D_DOC, lines=lines)
            break
    if doc is None:
        return []

    for line_no, line in enumerate(doc.lines, start=1):
        if line.strip() == "conf.d/":
            listed: set[str] = set()
            block_start = line_no
            for later_line in doc.lines[line_no:]:
                match = _TREE_BRANCH_RE.search(later_line)
                if match:
                    listed.add(match.group(1))
                    continue
                break
            return check_directory_listing_completeness(
                doc.rel_path,
                block_start,
                frozenset(listed),
                repo_root / "conf.d",
                label="conf.d/",
            )
    return []


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check documentation consistency across domains.",
    )
    parser.add_argument(
        "--domain",
        required=True,
        choices=list(DOMAIN_PREFIXES.keys()),
        help="Domain to check (agent, mcp, rag, deployment, overview)",
    )
    parser.add_argument(
        "--docs-dir",
        default=None,
        help="Path to docs/ directory (default: <repo_root>/docs/)",
    )
    parser.add_argument(
        "--skip",
        nargs="+",
        choices=sorted(ALL_SKIP_OPTIONS),
        help="Skip one or more checks (unknown skip options are silently ignored)",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parent.parent
    docs_dir = Path(args.docs_dir) if args.docs_dir else repo_root / "docs"
    if not docs_dir.is_dir():
        print(f"ERROR: docs directory not found: {docs_dir}", file=sys.stderr)
        return 1

    subfolder = DOMAIN_SUBFOLDERS[args.domain]
    skip = set(args.skip or [])
    files = discover_md_files(docs_dir / subfolder, prefix="")
    if not files:
        print(f"No *.md files found in docs/{subfolder}/.", file=sys.stderr)
        return 0

    all_issues: list[Issue] = []

    # Generic checks
    if "links" not in skip:
        all_issues.extend(check_broken_internal_links(docs_dir, files))
    if "removedfiles" not in skip:
        all_issues.extend(check_removed_file_references(docs_dir, files))
    if "commanddrift" not in skip:
        all_issues.extend(check_command_drift(docs_dir, files, repo_root))
    if "filerefs" not in skip:
        all_issues.extend(check_file_path_references(docs_dir, files, repo_root))
    if "funcrefs" not in skip:
        all_issues.extend(check_function_references(docs_dir, files, repo_root))

    # Domain-specific checks
    if args.domain == "agent":
        if "commandcoverage" not in skip:
            all_issues.extend(check_command_coverage(docs_dir, repo_root))
        if "commandcontract" not in skip:
            all_issues.extend(check_command_contracts(docs_dir, repo_root))
        if "schemadrift" not in skip:
            all_issues.extend(check_schema_drift(docs_dir, repo_root))
        if "diagnostics" not in skip:
            all_issues.extend(
                check_obsolete_diagnostics_references(docs_dir, files, repo_root)
            )
    elif args.domain == "mcp":
        if "portdrift" not in skip:
            all_issues.extend(check_port_drift(docs_dir, files, repo_root))
        if "tooldrift" not in skip:
            all_issues.extend(check_tool_name_drift(docs_dir, files, repo_root))
    elif args.domain == "rag":
        if "crawlerconfig" not in skip:
            all_issues.extend(check_crawler_config_drift(docs_dir, files, repo_root))
        if "debugoutput" not in skip:
            all_issues.extend(check_debug_output_existence(docs_dir, files, repo_root))
    elif args.domain == "deployment":
        if "dbcount" not in skip:
            all_issues.extend(check_db_count_claim(docs_dir, files, repo_root))
        if "dbtable" not in skip:
            all_issues.extend(check_db_table_completeness(docs_dir, files, repo_root))
        if "configkey" not in skip:
            all_issues.extend(check_config_key_presence(docs_dir, files, repo_root))
        if "portrange" not in skip:
            all_issues.extend(check_port_range_claim(docs_dir, files, repo_root))
    elif args.domain == "overview":
        if "conflisting" not in skip:
            all_issues.extend(check_conf_d_listing(docs_dir, repo_root))

    return report_and_exit(all_issues)


def main_mcp(argv: list[str] | None = None) -> int:
    """Console-script entry point for MCP domain docs consistency check."""
    return main((argv if argv is not None else sys.argv[1:]) + ["--domain", "mcp"])


def main_agent(argv: list[str] | None = None) -> int:
    """Console-script entry point for Agent domain docs consistency check."""
    return main((argv if argv is not None else sys.argv[1:]) + ["--domain", "agent"])


if __name__ == "__main__":
    sys.exit(main())
