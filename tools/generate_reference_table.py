#!/usr/bin/env python3
"""generate_reference_table.py — Unified reference table generator for all domains.

Applies the same "generate objective facts from live code instead of
hand-maintaining a copy" approach across all domains. Each type generates
only mechanically derivable columns; human-authored columns stay as-is.

Usage:
    python tools/generate_reference_table.py --type rag              # print RAG config table
    python tools/generate_reference_table.py --type mcp               # writes MCP table to docs/
    python tools/generate_reference_table.py --type deployment        # writes DB path table to docs/
    python tools/generate_reference_table.py --type rag --dry-run     # dry run
    python tools/generate_reference_table.py --manifests              # write registry/manifests/*.yaml, then re-render guarded docs from them
    python tools/generate_reference_table.py --check                  # two-way drift check (manifest-vs-source and block-vs-manifest)
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import re
import sys
import tomllib
from collections.abc import Callable
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._contract_manifests import (
    ManifestError,
    envelope,
    load_manifest,
    render_symbol_table,
    write_manifest,
)

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

MANIFEST_DIR = REPO_ROOT / "registry" / "manifests"
DB_SCHEMA_SQL_SRC = REPO_ROOT / "scripts" / "db" / "schema_sql.py"
EVENTBUS_SCHEMA_SQL_SRC = REPO_ROOT / "scripts" / "eventbus" / "schema.sql"
EVENTBUS_AUTH_SRC = REPO_ROOT / "scripts" / "eventbus" / "auth.py"
CONFIG_FIELD_REGISTRY_SRC = (
    REPO_ROOT / "scripts" / "agent" / "services" / "config_field_registry.py"
)
POSTURE_CONTRACT_SRC = (
    REPO_ROOT / "scripts" / "shared" / "security" / "posture_contract.py"
)
ADR_INDEX_SRC = REPO_ROOT / "docs" / "10_adr" / "adr_01_index.md"

_URL_PORT_RE = re.compile(r":(\d{2,5})\"?\s*$")
_TOOL_LIST_NAME_RE = re.compile(r'\{\s*"name":\s*"([a-z][a-z0-9_]*)"')
_DB_PATH_FIELD_RE = re.compile(
    r'^\s+(\w+_db_path):\s*str(?:\s*=\s*"([^"]*)")?', re.MULTILINE
)
_PRAGMA_USER_VERSION_RE = re.compile(r"PRAGMA user_version = (\d+)")
_WORKFLOW_VERSION_RE = re.compile(r'^WORKFLOW_SCHEMA_VERSION = "([^"]+)"', re.MULTILINE)

CONFIG_PATHS = [
    _CRAWLER_TOML,
    _CHUNK_SPLITTER_TOML,
    _INGESTER_TOML,
]

# Guard comments for auto-generated sections in doc files.
GUARD_START_MCP = (
    "<!-- AUTO-GENERATED: generate_reference_table.py port-tool-reference -->"
)
GUARD_END = "<!-- END AUTO-GENERATED -->"
GUARD_START_DEPLOYMENT = (
    "<!-- AUTO-GENERATED: generate_reference_table.py db-path-reference -->"
)
GUARD_START_AGENT = "<!-- AUTO-GENERATED: generate_reference_table.py agent-class-function-reference -->"
GUARD_START_EVENTBUS = "<!-- AUTO-GENERATED: generate_reference_table.py eventbus-class-function-reference -->"
GUARD_START_MEMORY = "<!-- AUTO-GENERATED: generate_reference_table.py memory-class-function-reference -->"

REFERENCE_DOC_MCP = REPO_ROOT / "docs" / "22_mcp" / "mcp_01_tool_ownership_matrix.md"
REFERENCE_DOC_DEPLOYMENT = (
    REPO_ROOT / "docs" / "90_deployment" / "deployment_01_deployment.md"
)
REFERENCE_DOC_AGENT = (
    REPO_ROOT / "docs" / "23_agent" / "agent_13_reference-api-generated.md"
)
REFERENCE_DOC_EVENTBUS = (
    REPO_ROOT / "docs" / "24_eventbus" / "eventbus_08_reference_api.md"
)
REFERENCE_DOC_MEMORY = (
    REPO_ROOT / "docs" / "23_agent" / "agent_11_04_memory-module-reference-generated.md"
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


def _mcp_endpoint_entries() -> list[dict[str, Any]]:
    ports = _load_server_ports()
    return [
        {
            "server": key,
            "port": int(ports[key]),
            "tools": _tool_names_for_config_key(key),
        }
        for key in sorted(ports)
    ]


def _render_mcp_table(entries: list[dict[str, Any]]) -> str:
    lines = ["| Server | Port | Tool Count | Tool Names |", "|---|---|---|---|"]
    for entry in entries:
        doc_name = f"{entry['server'].replace('_', '-')}-mcp"
        tools = entry["tools"]
        tool_names_cell = ", ".join(f"`{t}`" for t in tools) if tools else "—"
        lines.append(
            f"| {doc_name} | {entry['port']} | {len(tools)} | {tool_names_cell} |"
        )
    return "\n".join(lines)


def generate_mcp_reference_table() -> str:
    return _render_mcp_table(_mcp_endpoint_entries())


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


def _db_path_entries() -> list[dict[str, Any]]:
    defaults = _default_db_paths()
    configured = _agent_toml_db_paths()
    return [
        {
            "kind": "db_path",
            "name": f"{key.removesuffix('_db_path')}.sqlite",
            "config_key": key,
            "in_agent_toml": key in configured,
        }
        for key in sorted(defaults)
    ]


def _render_deployment_table(entries: list[dict[str, Any]]) -> str:
    lines = [
        "| DB | Config key | Set in `agent.toml`? |",
        "|---|---|---|",
    ]
    for entry in entries:
        if entry["in_agent_toml"]:
            in_toml = "Yes"
        else:
            in_toml = "No (Python-level default in `scripts/db/config.py`)"
        lines.append(f"| `{entry['name']}` | `{entry['config_key']}` | {in_toml} |")
    return "\n".join(lines)


def generate_deployment_reference_table() -> str:
    return _render_deployment_table(_db_path_entries())


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


def _symbol_entries(source_dir: Path) -> list[dict[str, Any]]:
    """Return symbol-manifest entries (file, name, kind, signature, summary)
    for every public top-level class/function in *source_dir*'s
    non-recursive `*.py` files, grouped by file in source order."""
    entries: list[dict[str, Any]] = []
    for path in sorted(source_dir.glob("*.py")):
        if path.name.startswith("_"):
            continue
        for name, signature, summary in _extract_public_top_level_symbols(path):
            if signature.startswith("class "):
                kind = "class"
            elif signature.startswith("async def "):
                kind = "async function"
            else:
                kind = "function"
            try:
                rel_path = str(path.relative_to(REPO_ROOT))
            except ValueError:
                rel_path = str(path)
            entries.append(
                {
                    "file": rel_path,
                    "name": name,
                    "kind": kind,
                    "signature": signature,
                    "summary": summary,
                }
            )
    return entries


def _generate_class_function_reference_table(source_dir: Path) -> str:
    """Return a `| File | Class/Function | Signature | Summary |` table for
    *source_dir*, rendered from its symbol-manifest entries."""
    return render_symbol_table(_symbol_entries(source_dir))


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
    "mcp": "Generated from `registry/manifests/mcp_endpoints.yaml` (`config/agent.toml` and `scripts/mcp_servers/**/*.py` TOOL_LIST definitions). Do not hand-edit between the guard comments; run `python tools/generate_reference_table.py --manifests` to refresh.",
    "deployment": "Generated from `scripts/db/config.py` and `config/agent.toml`. Do not hand-edit between the guard comments; run `python tools/generate_reference_table.py --type deployment` to refresh.",
    "agent": "Generated from `registry/manifests/agent_api.yaml` (`scripts/agent/*.py` top-level public classes and functions). Do not hand-edit between the guard comments; run `python tools/generate_reference_table.py --manifests` to refresh.",
    "eventbus": "Generated from `registry/manifests/eventbus_api.yaml` (`scripts/eventbus/*.py` top-level public classes and functions). Do not hand-edit between the guard comments; run `python tools/generate_reference_table.py --manifests` to refresh.",
    "memory": "Generated from `scripts/agent/memory/*.py` top-level public classes and functions. Do not hand-edit between the guard comments; run `python tools/generate_reference_table.py --type memory` to refresh.",
}

DOMAIN_HEADING = {
    "mcp": "## Server Port & Tool Reference (auto-generated)",
    "deployment": "### DB Path Reference (auto-generated)",
    "agent": "## Module Class/Function Reference (auto-generated)",
    "memory": "## Module Class/Function Reference (auto-generated)",
    "eventbus": "## Module Class/Function Reference (auto-generated)",
}

# ---------------------------------------------------------------------------
# Contract manifests: one builder per registered manifest name (doc 06
# schema; registry/manifests/*.yaml committed artifacts). Fact manifests
# (eventbus_route_roles, config_ownership, health_contracts,
# invariant_coverage) have no guard block of their own.
# ---------------------------------------------------------------------------

_MANIFEST_SOURCES: dict[str, list[str]] = {
    "tool_ownership": ["config/agent.toml", "scripts/mcp_servers"],
    "mcp_endpoints": ["config/agent.toml"],
    "eventbus_route_roles": ["scripts/eventbus/auth.py"],
    "db_schema_versions": [
        "scripts/db/config.py",
        "scripts/db/schema_sql.py",
        "scripts/eventbus/schema.sql",
    ],
    "config_ownership": ["scripts/agent/services/config_field_registry.py"],
    "health_contracts": ["scripts/shared/security/posture_contract.py"],
    "invariant_coverage": ["docs/10_adr/adr_01_index.md"],
    "agent_api": ["scripts/agent"],
    "eventbus_api": ["scripts/eventbus"],
    "memory_api": ["scripts/agent/memory"],
}

MANIFESTS_BY_DOMAIN: dict[str, tuple[str, ...]] = {
    "mcp": ("tool_ownership", "mcp_endpoints"),
    "deployment": ("db_schema_versions",),
    "agent": ("agent_api",),
    "eventbus": ("eventbus_api", "eventbus_route_roles"),
    "memory": ("memory_api",),
}

UNBOUND_MANIFESTS: tuple[str, ...] = (
    "config_ownership",
    "health_contracts",
    "invariant_coverage",
)

# Manifest each domain's guarded table renders FROM. For `mcp` this is
# `mcp_endpoints` (the guarded table is server-centric); `tool_ownership`
# still belongs to the domain and is drift-checked, but its rows are the
# per-tool view, not the table layout.
_RENDER_MANIFEST: dict[str, str] = {
    "mcp": "mcp_endpoints",
    "deployment": "db_schema_versions",
    "agent": "agent_api",
    "eventbus": "eventbus_api",
    "memory": "memory_api",
}


def _module_ast(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _assigned_value(tree: ast.Module, name: str) -> ast.expr:
    """Return the value node of the module-level `name = ...` (or annotated)
    assignment, or raise when the source no longer defines it."""
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets: list[ast.expr] = list(node.targets)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            targets = [node.target]
        else:
            continue
        if any(isinstance(t, ast.Name) and t.id == name for t in targets):
            if node.value is None:
                raise ManifestError(f"{name} assignment has no value in source")
            return node.value
    raise ManifestError(
        f"{name} assignment not found in source — regenerate against the new structure"
    )


def _tool_ownership_entries() -> list[dict[str, Any]]:
    ports = _load_server_ports()
    entries: list[dict[str, Any]] = []
    owners: dict[str, str] = {}
    for key in sorted(ports):
        for tool in _tool_names_for_config_key(key):
            if tool in owners:
                raise ManifestError(
                    f"duplicate tool ownership: {tool} in {owners[tool]} and {key}"
                )
            owners[tool] = key
            entries.append({"tool": tool, "server": key, "port": int(ports[key])})
    entries.sort(key=lambda e: e["tool"])
    return entries


def _schema_version_row(name: str, source: Path, version: int | str) -> dict[str, Any]:
    text = source.read_text(encoding="utf-8")
    return {
        "kind": "schema",
        "name": name,
        "source": str(source.relative_to(REPO_ROOT)),
        "version": version,
        "content_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def _db_schema_version_entries() -> list[dict[str, Any]]:
    eventbus_text = EVENTBUS_SCHEMA_SQL_SRC.read_text(encoding="utf-8")
    eventbus_match = _PRAGMA_USER_VERSION_RE.search(eventbus_text)
    if eventbus_match is None:
        raise ManifestError("eventbus schema.sql does not stamp PRAGMA user_version")
    workflow_text = DB_SCHEMA_SQL_SRC.read_text(encoding="utf-8")
    workflow_match = _WORKFLOW_VERSION_RE.search(workflow_text)
    if workflow_match is None:
        raise ManifestError("schema_sql.py does not define WORKFLOW_SCHEMA_VERSION")
    entries = _db_path_entries()
    entries.append(
        _schema_version_row(
            "eventbus", EVENTBUS_SCHEMA_SQL_SRC, int(eventbus_match.group(1))
        )
    )
    entries.append(
        _schema_version_row("workflow", DB_SCHEMA_SQL_SRC, workflow_match.group(1))
    )
    entries.sort(key=lambda e: (e["kind"], e["name"]))
    return entries


def _route_role_entries() -> list[dict[str, Any]]:
    tree = _module_ast(EVENTBUS_AUTH_SRC)
    value = _assigned_value(tree, "_ROUTE_ROLE_MAP")
    if not isinstance(value, ast.Dict):
        raise ManifestError("_ROUTE_ROLE_MAP is not a dict literal")
    entries: list[dict[str, Any]] = []
    for key_node, roles_node in zip(value.keys, value.values):
        if not isinstance(key_node, ast.Constant) or not isinstance(
            key_node.value, str
        ):
            raise ManifestError("non-literal route key in _ROUTE_ROLE_MAP")
        if not isinstance(roles_node, ast.Set):
            raise ManifestError(
                f"roles for route {key_node.value} are not a set literal"
            )
        roles: set[str] = set()
        for elt in roles_node.elts:
            if isinstance(elt, ast.Attribute):
                roles.add(elt.attr)
            elif isinstance(elt, ast.Name):
                roles.add(elt.id)
            else:
                raise ManifestError(
                    f"unexpected role expression for route {key_node.value}"
                )
        entries.append({"route": key_node.value, "roles": sorted(roles)})
    entries.sort(key=lambda e: e["route"])
    return entries


def _config_ownership_entries() -> list[dict[str, Any]]:
    # AST extraction (doc 11): immune to call formatting (multi-line calls,
    # trailing commas) that a text regex would silently drop.
    tree = _module_ast(CONFIG_FIELD_REGISTRY_SRC)
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for node in ast.walk(tree):
        if (
            not isinstance(node, ast.Call)
            or not isinstance(node.func, ast.Name)
            or node.func.id != "ConfigFieldRegistry"
        ):
            continue
        args = node.args
        if node.keywords or not 3 <= len(args) <= 4:
            raise ManifestError(
                f"unexpected ConfigFieldRegistry call shape: "
                f"{len(args)} positional args, {len(node.keywords)} keywords"
            )
        name, section, hot = args[0], args[1], args[2]
        if not (
            isinstance(name, ast.Constant)
            and isinstance(name.value, str)
            and isinstance(section, ast.Constant)
            and isinstance(section.value, str)
            and isinstance(hot, ast.Constant)
            and isinstance(hot.value, bool)
        ):
            raise ManifestError("non-literal ConfigFieldRegistry positional args")
        validator: str | None = None
        if len(args) == 4:
            if isinstance(args[3], ast.Name):
                validator = args[3].id
            elif isinstance(args[3], ast.Attribute):
                validator = args[3].attr
            else:
                raise ManifestError(
                    f"unexpected validator expression for field {name.value}"
                )
        if name.value in seen:
            raise ManifestError(f"duplicate config field ownership: {name.value}")
        seen.add(name.value)
        entries.append(
            {
                "field": name.value,
                "section": section.value,
                "hot_reloadable": hot.value,
                "validator": validator,
            }
        )
    entries.sort(key=lambda e: e["field"])
    return entries


def _check_id_strings(node: ast.expr, consts: dict[str, list[str]]) -> list[str]:
    """Flatten `"literal"`, `NAME`, and `COMMON_CHECK_IDS + (...)`-style
    check-id expressions into a flat list of strings."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _check_id_strings(node.left, consts) + _check_id_strings(
            node.right, consts
        )
    if isinstance(node, ast.Name) and node.id in consts:
        return list(consts[node.id])
    if isinstance(node, ast.Tuple):
        out: list[str] = []
        for elt in node.elts:
            out.extend(_check_id_strings(elt, consts))
        return out
    raise ManifestError("unexpected check-id expression in REQUIRED_CHECK_IDS")


def _health_contract_entries() -> list[dict[str, Any]]:
    tree = _module_ast(POSTURE_CONTRACT_SRC)
    consts: dict[str, list[str]] = {}
    for node in tree.body:
        value: ast.expr | None = None
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            value, targets = node.value, list(node.targets)
        elif isinstance(node, ast.AnnAssign):
            value, targets = node.value, [node.target]
        if value is None:
            continue
        try:
            items = _check_id_strings(value, consts)
        except ManifestError:
            continue
        if not items:
            continue
        for target in targets:
            if isinstance(target, ast.Name):
                consts[target.id] = items
    required = _assigned_value(tree, "REQUIRED_CHECK_IDS")
    if not isinstance(required, ast.Dict):
        raise ManifestError("REQUIRED_CHECK_IDS is not a dict literal")
    entries: list[dict[str, Any]] = []
    for key_node, checks_node in zip(required.keys, required.values):
        if not isinstance(key_node, ast.Constant) or not isinstance(
            key_node.value, str
        ):
            raise ManifestError("non-literal server key in REQUIRED_CHECK_IDS")
        checks = _check_id_strings(checks_node, consts)
        if not checks:
            raise ManifestError(f"empty check set for server {key_node.value}")
        entries.append(
            {
                "server": key_node.value,
                "checks": sorted(set(checks)),
                # ADR-004 Decision #14: posture-check failure fails the server
                # at startup; no shipped server degrades to partial posture.
                "disposition": "fail-fast",
            }
        )
    entries.sort(key=lambda e: e["server"])
    return entries


_MATRIX_STATUS_TOKENS = ("Confirmed", "Partial", "Manual", "Not verified")
_COV_ADR_INV_RE = re.compile(r"^(ADR-\d{3})\s+(INV.+)$")
_COV_CITED_RE = re.compile(r"`(tests/[^`]+\.py(?:::[^`]+)*)`")
_COV_CADENCE_RE = re.compile(r"Cadence:\s*(.+?)\s*Expected evidence:")
_COV_EXPECTED_RE = re.compile(r"Expected evidence:\s*(.+?)\s+Owner:")
_COV_EXCEPTION_RE = re.compile(r"Exception: ([A-Za-z0-9._-]+)")


def _invariant_coverage_entries() -> list[dict[str, Any]]:
    # Reuse the matrix checker's row parsers in-process: single parsing
    # implementation (same rule as the CI runner against this checker).
    from tools.check_adr_invariant_matrix import (
        ADR_INDEX,
        _matrix_rows,
        _read_lines,
        _split_row,
    )

    entries: list[dict[str, Any]] = []
    for _, row in _matrix_rows(_read_lines(ADR_INDEX)):
        cells = _split_row(row)
        if len(cells) < 2:
            continue
        match = _COV_ADR_INV_RE.match(cells[0])
        if match is None:
            # Not a matrix row: another table inside the same section
            # (e.g. the Pipeline Mapping Summary).
            continue
        if len(cells) != 6:
            raise ManifestError(
                f"invariant matrix row has {len(cells)} columns: {row[:60]}"
            )
        id_cell, _invariant_text, gate, timing, _blocking, status_cell = cells
        status = next(
            (t for t in _MATRIX_STATUS_TOKENS if status_cell.startswith(t)), None
        )
        if status is None:
            raise ManifestError(f"unknown Verification Status cell: {status_cell[:40]}")
        entry: dict[str, Any] = {
            "invariant": match.group(2).strip(),
            "adr": match.group(1),
            "gate": gate,
            "timing": timing,
            "status": status,
        }
        cited = _COV_CITED_RE.findall(status_cell)
        if cited:
            entry["cited"] = sorted(set(cited))
        cadence = _COV_CADENCE_RE.search(status_cell)
        if cadence:
            entry["cadence"] = cadence.group(1).strip()
        expected = _COV_EXPECTED_RE.search(status_cell)
        if expected:
            entry["expected_evidence"] = expected.group(1).strip()
        exception = _COV_EXCEPTION_RE.search(status_cell)
        if exception:
            entry["exception"] = exception.group(1)
        entries.append(entry)
    entries.sort(key=lambda e: (e["adr"], e["invariant"]))
    return entries


def _api_manifest_entries(domain: str) -> list[dict[str, Any]]:
    dirs = {"agent": AGENT_DIR, "eventbus": EVENTBUS_DIR, "memory": MEMORY_DIR}
    return _symbol_entries(dirs[domain])


_MANIFEST_BUILDERS: dict[str, Callable[[], list[dict[str, Any]]]] = {
    "tool_ownership": _tool_ownership_entries,
    "mcp_endpoints": _mcp_endpoint_entries,
    "eventbus_route_roles": _route_role_entries,
    "db_schema_versions": _db_schema_version_entries,
    "config_ownership": _config_ownership_entries,
    "health_contracts": _health_contract_entries,
    "invariant_coverage": _invariant_coverage_entries,
    "agent_api": lambda: _api_manifest_entries("agent"),
    "eventbus_api": lambda: _api_manifest_entries("eventbus"),
    "memory_api": lambda: _api_manifest_entries("memory"),
}


def build_manifest(name: str) -> dict[str, Any]:
    """Return the validated manifest envelope for *name*, built from live sources."""
    return envelope(name, _MANIFEST_SOURCES[name], _MANIFEST_BUILDERS[name]())


def _table_from_entries(domain: str, entries: list[dict[str, Any]]) -> str:
    """Render the domain's guarded table markdown from manifest entries."""
    if domain == "mcp":
        return _render_mcp_table(entries)
    if domain == "deployment":
        return _render_deployment_table([e for e in entries if e["kind"] == "db_path"])
    return render_symbol_table(entries)


def _manifest_entries(domain: str, *, from_committed: bool) -> list[dict[str, Any]]:
    """Return the primary rendering manifest entries for *domain*.

    from_committed=False rebuilds from live sources (the --type write path);
    from_committed=True reads the committed manifest, so a stale manifest
    stays stale until --manifests rewrites it (block-vs-manifest direction).
    """
    primary = _RENDER_MANIFEST[domain]
    if from_committed:
        committed = load_manifest(primary, MANIFEST_DIR)
        if committed is None:
            raise ManifestError(f"{primary} manifest is not committed")
        return list(committed["entries"])
    return _MANIFEST_BUILDERS[primary]()


def _domain_table(domain: str) -> str:
    """Return the domain's table markdown rebuilt from live sources.

    `rag` has no contract manifest (its table is outside all guards), so it
    keeps calling its generator directly.
    """
    if domain in MANIFESTS_BY_DOMAIN:
        return _table_from_entries(
            domain, _manifest_entries(domain, from_committed=False)
        )
    return DOMAIN_GENERATORS[domain][1]()


def render_updated_doc(domain: str, doc_content: str) -> str:
    """Return doc_content with the domain's guarded block regenerated from live code."""
    table = _table_from_entries(domain, _manifest_entries(domain, from_committed=False))
    guard_start, guard_end = DOMAIN_GUARDS[domain]
    welcome = DOMAIN_WELCOME_LINES.get(domain, "")
    generated = f"{guard_start}\n{welcome}\n\n{table}\n{guard_end}"
    start = doc_content.find(guard_start)
    end = doc_content.find(guard_end)
    if start != -1 and end != -1:
        return doc_content[:start] + generated + doc_content[end + len(guard_end) :]
    heading = DOMAIN_HEADING.get(domain, "")
    return doc_content.rstrip("\n") + f"\n\n{heading}\n\n" + generated + "\n"


def check_manifest_drift(names: list[str]) -> list[str]:
    """Return a drift entry per committed manifest missing or stale vs its live sources."""
    drifted: list[str] = []
    for name in names:
        committed = load_manifest(name, MANIFEST_DIR)
        if committed is None:
            drifted.append(f"registry/manifests/{name}.yaml (manifest missing)")
            continue
        if committed != build_manifest(name):
            drifted.append(f"registry/manifests/{name}.yaml (manifest stale)")
    return drifted


def check_drift(domains: list[str]) -> list[str]:
    """Return the repository-relative path of every manifest or doc block that drifted.

    Two directions per domain: the committed manifest against the manifest
    rebuilt from live sources (manifest vs source), and the guarded block
    against the block rendered from the committed manifest (block vs manifest).
    A doc drifts when its guard-comment block is missing or differs; a missing
    committed manifest is itself drift.
    """
    drifted: list[str] = []
    for domain in domains:
        drifted += check_manifest_drift(list(MANIFESTS_BY_DOMAIN[domain]))
        doc_path = DOMAIN_DOCS.get(domain)
        if doc_path is None:
            continue
        content = doc_path.read_text(encoding="utf-8")
        guard_start, guard_end = DOMAIN_GUARDS[domain]
        if guard_start not in content or guard_end not in content:
            drifted.append(f"{doc_path.relative_to(REPO_ROOT)} (guarded block missing)")
            continue
        try:
            entries = _manifest_entries(domain, from_committed=True)
        except ManifestError:
            # The manifest-drift entry above already reports the cause.
            continue
        table = _table_from_entries(domain, entries)
        generated = f"{guard_start}\n{DOMAIN_WELCOME_LINES.get(domain, '')}\n\n{table}\n{guard_end}"
        start = content.find(guard_start)
        end = content.find(guard_end)
        if content[start : end + len(guard_end)] != generated:
            drifted.append(f"{doc_path.relative_to(REPO_ROOT)} (--type {domain})")
    return drifted


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate reference tables from live code."
    )
    parser.add_argument("--type", choices=list(DOMAIN_GENERATORS.keys()))
    parser.add_argument("--dry-run", action="store_true", help="Print to stdout only")
    parser.add_argument(
        "--manifests",
        action="store_true",
        help="Write registry/manifests/*.yaml for every registered manifest "
        "(--type restricts to that domain's manifests), then re-render the "
        "guarded doc blocks from the committed manifests",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Write nothing; exit 1 when a committed manifest drifted from its live "
        "sources or a generated doc block drifted from its committed manifest "
        "(all doc-backed domains unless --type is given)",
    )
    args = parser.parse_args()

    if args.check:
        domains = [args.type] if args.type else list(DOMAIN_DOCS)
        drifted = check_drift(domains)
        if not args.type:
            drifted += check_manifest_drift(list(UNBOUND_MANIFESTS))
        for entry in drifted:
            print(f"DRIFT: {entry}")
        if drifted:
            print(
                "Run `uv run python tools/generate_reference_table.py --manifests` "
                "and commit the result."
            )
            raise SystemExit(1)
        print("No drift found")
        raise SystemExit(0)

    if args.manifests:
        if args.type:
            names = list(MANIFESTS_BY_DOMAIN.get(args.type, ()))
            if not names:
                parser.error(f"--type {args.type} has no contract manifests")
        else:
            names = list(_MANIFEST_BUILDERS)
        for name in names:
            path = write_manifest(
                build_manifest(name), MANIFEST_DIR, dry_run=args.dry_run
            )
            print(
                f"{'Would write' if args.dry_run else 'Wrote'} {path.relative_to(REPO_ROOT)}"
            )
        for domain in DOMAIN_DOCS:
            if args.type and args.type != domain:
                continue
            doc_path = DOMAIN_DOCS[domain]
            doc_content = doc_path.read_text(encoding="utf-8")
            table = _table_from_entries(
                domain, _manifest_entries(domain, from_committed=not args.dry_run)
            )
            updated = render_updated_doc(domain, doc_content)
            if args.dry_run:
                print(f"<!-- DRY-RUN ONLY: {domain} block -->\n{table}\n")
            elif updated != doc_content:
                doc_path.write_text(updated, encoding="utf-8")
                print(f"Updated {doc_path.relative_to(REPO_ROOT)}")
        raise SystemExit(0)

    if args.type is None:
        parser.error("--type is required unless --check or --manifests is given")

    description, _ = DOMAIN_GENERATORS[args.type]

    if args.dry_run:
        table = _domain_table(args.type)
        print(f"<!-- DRY-RUN ONLY: {description} -->\n{table}\n")
    else:
        target_doc: Path | None = DOMAIN_DOCS.get(args.type)
        if target_doc is None:
            # No target doc file — just print the table.
            print(_domain_table(args.type))
        else:
            doc_content = target_doc.read_text(encoding="utf-8")
            target_doc.write_text(
                render_updated_doc(args.type, doc_content), encoding="utf-8"
            )
            print(f"Updated {target_doc.relative_to(REPO_ROOT)}")
