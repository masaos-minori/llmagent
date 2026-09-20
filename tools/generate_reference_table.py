#!/usr/bin/env python3
"""generate_reference_table.py — Unified reference table generator for all domains.

Consolidated from:
  - tools/gen_rag_reference.py
  - tools/gen_mcp_reference.py
  - tools/gen_deployment_reference.py

Applies the same "generate objective facts from live code instead of
hand-maintaining a copy" approach across all domains. Each type generates
only mechanically derivable columns; human-authored columns stay as-is.

Usage:
    python tools/generate_reference_table.py --type rag              # print RAG config table
    python tools/generate_reference_table.py --type mcp               # writes MCP table to docs/
    python tools/generate_reference_table.py --type deployment        # writes DB path table to docs/
    python tools/generate_reference_table.py --type rag --dry-run     # dry run
"""

from __future__ import annotations

import argparse
import ast
import re
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENT_TOML = REPO_ROOT / "config" / "agent.toml"
MCP_SERVERS_DIR = REPO_ROOT / "scripts" / "mcp_servers"
DB_CONFIG_SRC = REPO_ROOT / "scripts" / "db" / "config.py"
AGENT_DIR = REPO_ROOT / "scripts" / "agent"
EVENTBUS_DIR = REPO_ROOT / "scripts" / "eventbus"
MEMORY_DIR = REPO_ROOT / "scripts" / "agent" / "memory"
_CRAWLER_TOML = REPO_ROOT / "config" / "crawler.toml"
_CHUNK_SPLITTER_TOML = REPO_ROOT / "config" / "chunk_splitter.toml"
_INGESTER_TOML = REPO_ROOT / "config" / "ingester.toml"

_URL_PORT_RE = re.compile(r":(\d{2,5})\"?\s*$")
_TOOL_LIST_NAME_RE = re.compile(r'\{\s*"name":\s*"([a-z][a-z0-9_]*)"')
_DB_PATH_FIELD_RE = re.compile(
    r'^\s+(\w+_db_path):\s*str(?:\s*=\s*"([^"]*)")?', re.MULTILINE
)

CONFIG_PATHS = [
    _CRAWLER_TOML,
    _CHUNK_SPLITTER_TOML,
    _INGESTER_TOML,
]

# Guard comments for auto-generated sections in doc files.
GUARD_START_MCP = "<!-- AUTO-GENERATED: gen_mcp_reference.py port-tool-reference -->"
GUARD_END = "<!-- END AUTO-GENERATED -->"
GUARD_START_DEPLOYMENT = (
    "<!-- AUTO-GENERATED: gen_deployment_reference.py db-path-reference -->"
)
GUARD_START_AGENT = (
    "<!-- AUTO-GENERATED: gen_agent_reference.py class-function-reference -->"
)
GUARD_START_EVENTBUS = (
    "<!-- AUTO-GENERATED: gen_eventbus_reference.py class-function-reference -->"
)
GUARD_START_MEMORY = (
    "<!-- AUTO-GENERATED: gen_memory_reference.py class-function-reference -->"
)

REFERENCE_DOC_MCP = REPO_ROOT / "docs" / "04_mcp_01_tool_ownership_matrix.md"
REFERENCE_DOC_DEPLOYMENT = REPO_ROOT / "docs" / "02_deployment-part2.md"
REFERENCE_DOC_AGENT = REPO_ROOT / "docs" / "05_agent_14_reference-api-generated.md"
REFERENCE_DOC_EVENTBUS = REPO_ROOT / "docs" / "06_eventbus_06_reference-api.md"
REFERENCE_DOC_MEMORY = (
    REPO_ROOT / "docs" / "05_agent_12_07_memory-module-reference-generated.md"
)

# ---------------------------------------------------------------------------
# RAG domain: generate configuration tables
# ---------------------------------------------------------------------------


def generate_rag_config_table() -> str:
    lines = ["| Key | Default | Description |", "|---|---|---|"]
    for config_path in CONFIG_PATHS:
        with config_path.open("rb") as f:
            cfg = tomllib.load(f)
        for section, values in cfg.items():
            if isinstance(values, dict):
                for key, val in values.items():
                    lines.append(f"| `{section}.{key}` | `{val}` | — |")
            else:
                lines.append(f"| `{section}` | `{values}` | — |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MCP domain: generate server port/tool-count reference table
# ---------------------------------------------------------------------------


def _load_server_ports() -> dict[str, str]:
    """Return {config-key: port} for every [mcp_servers.*] section in agent.toml."""
    with AGENT_TOML.open("rb") as f:
        cfg = tomllib.load(f)
    servers = cfg.get("mcp_servers", {})
    ports: dict[str, str] = {}
    for key, section in servers.items():
        if not isinstance(section, dict):
            continue
        url = section.get("url")
        if not isinstance(url, str):
            continue
        match = _URL_PORT_RE.search(url)
        if match:
            ports[key] = match.group(1)
    return ports


def _tool_names_for_config_key(key: str) -> list[str]:
    """Return sorted tool names owned by the server identified by *key*."""
    if key.startswith("file_"):
        stem = key.removeprefix("file_")
        candidates = [MCP_SERVERS_DIR / "file" / f"{stem}_tools.py"]
    else:
        server_dir = MCP_SERVERS_DIR / key
        candidates = sorted(server_dir.glob("*.py")) if server_dir.is_dir() else []

    names: set[str] = set()
    for path in candidates:
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        names.update(_TOOL_LIST_NAME_RE.findall(content))
    return sorted(names)


def generate_mcp_reference_table() -> str:
    ports = _load_server_ports()
    lines = ["| Server | Port | Tool Count | Tool Names |", "|---|---|---|---|"]
    for key in sorted(ports):
        doc_name = f"{key.replace('_', '-')}-mcp"
        tools = _tool_names_for_config_key(key)
        tool_names_cell = ", ".join(f"`{t}`" for t in tools) if tools else "—"
        lines.append(
            f"| {doc_name} | {ports[key]} | {len(tools)} | {tool_names_cell} |"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Deployment domain: generate platform DB path/config-key reference table
# ---------------------------------------------------------------------------


def _default_db_paths() -> dict[str, str | None]:
    """Return {config_key: python_level_default_or_None} from DbConfig's fields."""
    content = DB_CONFIG_SRC.read_text(encoding="utf-8")
    return {key: default for key, default in _DB_PATH_FIELD_RE.findall(content)}


def _agent_toml_db_paths() -> dict[str, str]:
    """Return {config_key: path} for every `*_db_path` set in agent.toml."""
    with AGENT_TOML.open("rb") as f:
        cfg = tomllib.load(f)
    return {
        k: v for k, v in cfg.items() if k.endswith("_db_path") and isinstance(v, str)
    }


def generate_deployment_reference_table() -> str:
    defaults = _default_db_paths()
    configured = _agent_toml_db_paths()

    lines = [
        "| DB | Default path | Config key | Set in `agent.toml`? |",
        "|---|---|---|---|",
    ]
    for key in sorted(defaults):
        db_name = f"{key.removesuffix('_db_path')}.sqlite"
        if key in configured:
            path = configured[key]
            in_toml = "Yes"
        else:
            path = defaults[key] or "(no default)"
            in_toml = "No (Python-level default in `scripts/db/config.py`)"
        lines.append(f"| `{db_name}` | `{path}` | `{key}` | {in_toml} |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Agent/EventBus/Memory domains: generate class/function reference tables
# ---------------------------------------------------------------------------


def _first_docstring_line(
    node: ast.AsyncFunctionDef | ast.FunctionDef | ast.ClassDef,
) -> str:
    """Return the first line of *node*'s docstring, or '—' if it has none."""
    doc = ast.get_docstring(node)
    if not doc:
        return "—"
    return doc.strip().splitlines()[0]


def _format_function_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Return a compact `[async] def name(args) -> returns` string for *node*."""
    parts = [a.arg for a in node.args.posonlyargs]
    parts += [a.arg for a in node.args.args]
    if node.args.vararg:
        parts.append(f"*{node.args.vararg.arg}")
    elif node.args.kwonlyargs:
        parts.append("*")
    parts += [a.arg for a in node.args.kwonlyargs]
    if node.args.kwarg:
        parts.append(f"**{node.args.kwarg.arg}")
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    return f"{prefix} {node.name}({', '.join(parts)}){returns}"


def _extract_public_top_level_symbols(path: Path) -> list[tuple[str, str, str]]:
    """Return (name, signature, docstring-summary) for every public top-level
    class/function in *path* — skips private (`_`-prefixed) names and does not
    descend into class bodies (methods are not individually listed)."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return []
    rows: list[tuple[str, str, str]] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if node.name.startswith("_"):
            continue
        if isinstance(node, ast.ClassDef):
            rows.append((node.name, f"class {node.name}", _first_docstring_line(node)))
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            rows.append(
                (
                    node.name,
                    _format_function_signature(node),
                    _first_docstring_line(node),
                )
            )
    return rows


def _escape_table_cell(value: str) -> str:
    """Escape `|` so *value* cannot be mistaken for a Markdown table column
    separator (e.g. a `X | None` union-type annotation inside a signature)."""
    return value.replace("|", "\\|")


def _generate_class_function_reference_table(source_dir: Path) -> str:
    """Return a `| File | Class/Function | Signature | Summary |` table for
    every public top-level class/function in *source_dir*'s non-recursive
    `*.py` files (private `_`-prefixed files and symbols are skipped). The
    File column is left blank after a file's first row to avoid repeating
    the same path on every row."""
    lines = ["| File | Class/Function | Signature | Summary |", "|---|---|---|---|"]
    for path in sorted(source_dir.glob("*.py")):
        if path.name.startswith("_"):
            continue
        rows = _extract_public_top_level_symbols(path)
        if not rows:
            continue
        try:
            rel_path = path.relative_to(REPO_ROOT)
        except ValueError:
            rel_path = path
        for i, (name, signature, summary) in enumerate(rows):
            signature = _escape_table_cell(signature)
            summary = _escape_table_cell(summary)
            file_cell = f"`{rel_path}`" if i == 0 else ""
            lines.append(f"| {file_cell} | `{name}` | `{signature}` | {summary} |")
    return "\n".join(lines)


def generate_agent_reference_table() -> str:
    return _generate_class_function_reference_table(AGENT_DIR)


def generate_eventbus_reference_table() -> str:
    return _generate_class_function_reference_table(EVENTBUS_DIR)


def generate_memory_reference_table() -> str:
    return _generate_class_function_reference_table(MEMORY_DIR)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

DOMAIN_GENERATORS = {
    "rag": ("RAG configuration table", generate_rag_config_table),
    "mcp": ("MCP server port & tool reference table", generate_mcp_reference_table),
    "deployment": (
        "Platform DB path / config-key reference table",
        generate_deployment_reference_table,
    ),
    "agent": (
        "Agent module class/function reference table",
        generate_agent_reference_table,
    ),
    "eventbus": (
        "EventBus module class/function reference table",
        generate_eventbus_reference_table,
    ),
    "memory": (
        "Memory module class/function reference table",
        generate_memory_reference_table,
    ),
}

DOMAIN_DOCS = {
    "mcp": REFERENCE_DOC_MCP,
    "deployment": REFERENCE_DOC_DEPLOYMENT,
    "agent": REFERENCE_DOC_AGENT,
    "eventbus": REFERENCE_DOC_EVENTBUS,
    "memory": REFERENCE_DOC_MEMORY,
}

DOMAIN_GUARDS = {
    "mcp": (GUARD_START_MCP, GUARD_END),
    "deployment": (GUARD_START_DEPLOYMENT, GUARD_END),
    "agent": (GUARD_START_AGENT, GUARD_END),
    "eventbus": (GUARD_START_EVENTBUS, GUARD_END),
    "memory": (GUARD_START_MEMORY, GUARD_END),
}

DOMAIN_WELCOME_LINES = {
    "mcp": "Generated from `config/agent.toml` and `scripts/mcp_servers/**/*.py` TOOL_LIST definitions. Do not hand-edit between the guard comments; run `python tools/generate_reference_table.py --type mcp` to refresh.",
    "deployment": "Generated from `scripts/db/config.py` and `config/agent.toml`. Do not hand-edit between the guard comments; run `python tools/generate_reference_table.py --type deployment` to refresh.",
    "agent": "Generated from `scripts/agent/*.py` top-level public classes and functions. Do not hand-edit between the guard comments; run `python tools/generate_reference_table.py --type agent` to refresh.",
    "eventbus": "Generated from `scripts/eventbus/*.py` top-level public classes and functions. Do not hand-edit between the guard comments; run `python tools/generate_reference_table.py --type eventbus` to refresh.",
    "memory": "Generated from `scripts/agent/memory/*.py` top-level public classes and functions. Do not hand-edit between the guard comments; run `python tools/generate_reference_table.py --type memory` to refresh.",
}

DOMAIN_HEADING = {
    "mcp": "## Server Port & Tool Reference (auto-generated)",
    "deployment": "### DB Path Reference (auto-generated)",
    "agent": "## Module Class/Function Reference (auto-generated)",
    "memory": "## Module Class/Function Reference (auto-generated)",
    "eventbus": "## Module Class/Function Reference (auto-generated)",
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate reference tables from live code."
    )
    parser.add_argument("--type", required=True, choices=list(DOMAIN_GENERATORS.keys()))
    parser.add_argument("--dry-run", action="store_true", help="Print to stdout only")
    args = parser.parse_args()

    description, generator = DOMAIN_GENERATORS[args.type]
    table = generator()

    if args.dry_run:
        print(f"<!-- DRY-RUN ONLY: {description} -->\n{table}\n")
    else:
        doc_path = DOMAIN_DOCS.get(args.type)
        if doc_path is None:
            # No target doc file — just print the table.
            print(table)
        else:
            guard_start, guard_end = DOMAIN_GUARDS.get(args.type, (None, None))
            generated = ""
            if guard_start and guard_end:
                welcome = DOMAIN_WELCOME_LINES.get(args.type, "")
                heading = DOMAIN_HEADING.get(args.type, "")
                generated = f"{guard_start}\n{welcome}\n\n{table}\n{guard_end}"
            else:
                generated = table

            doc_content = doc_path.read_text(encoding="utf-8")
            start = doc_content.find(guard_start) if guard_start else -1
            end = doc_content.find(guard_end) if guard_end else -1
            if start != -1 and end != -1 and guard_end is not None:
                updated = (
                    doc_content[:start]
                    + generated
                    + doc_content[end + len(guard_end) :]
                )
            else:
                heading = DOMAIN_HEADING.get(args.type, "")
                updated = (
                    doc_content.rstrip("\n") + f"\n\n{heading}\n\n" + generated + "\n"
                )
            doc_path.write_text(updated, encoding="utf-8")
            print(f"Updated {doc_path.relative_to(REPO_ROOT)}")
