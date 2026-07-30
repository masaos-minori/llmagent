#!/usr/bin/env python3
"""gen_mcp_reference.py — Auto-generate the MCP server port/tool-count reference table.

Companion to tools/gen_rag_reference.py, applying the same
"generate the objective facts from live code instead of hand-maintaining a
copy" approach to the MCP domain. This tool intentionally generates *only*
the facts that are mechanically derivable from config/agent.toml and
scripts/mcp_servers/**/*.py TOOL_LIST definitions (server name, port, tool
count, tool names) -- it does not attempt to regenerate the human-authored
risk-tier / approval-required / workflow-stage judgment columns that also
live in docs/04_mcp_01_tool_ownership_matrix.md, since those require domain
judgment a generator cannot safely infer.

Usage:
    python tools/gen_mcp_reference.py          # writes to docs/
    python tools/gen_mcp_reference.py --dry-run # print to stdout only
"""

from __future__ import annotations

import argparse
import re
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENT_TOML = REPO_ROOT / "config" / "agent.toml"
MCP_SERVERS_DIR = REPO_ROOT / "scripts" / "mcp_servers"
REFERENCE_DOC = REPO_ROOT / "docs" / "04_mcp_01_tool_ownership_matrix.md"
GUARD_START = "<!-- AUTO-GENERATED: gen_mcp_reference.py port-tool-reference -->"
GUARD_END = "<!-- END AUTO-GENERATED -->"

_URL_PORT_RE = re.compile(r":(\d{2,5})\"?\s*$")
_TOOL_LIST_NAME_RE = re.compile(r'\{\s*"name":\s*"([a-z][a-z0-9_]*)"')


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
    """Return the sorted tool names owned by the server identified by *key*.

    Handles the file/ directory's three-way split (file_read / file_write /
    file_delete each own a subset of scripts/mcp_servers/file/*.py) and
    github-mcp's multi-module TOOL_LIST assembly (tools_repository.py,
    tools_file.py, tools_issues.py, tools_pull_requests.py all feed into
    tools.py's combined TOOL_LIST) by scanning every .py file under the
    server's directory rather than assuming one fixed *_tools.py filename.
    """
    if key.startswith("file_"):
        stem = key.removeprefix("file_")  # "read" | "write" | "delete"
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


def generate_reference_table() -> str:
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    table = generate_reference_table()
    generated = (
        f"{GUARD_START}\n"
        f"Generated from `config/agent.toml` and `scripts/mcp_servers/**/*.py` "
        f"TOOL_LIST definitions. Do not hand-edit between the guard comments; "
        f"run `python tools/gen_mcp_reference.py` to refresh.\n\n"
        f"{table}\n"
        f"{GUARD_END}"
    )

    if args.dry_run:
        print(generated)
        return

    doc = REFERENCE_DOC.read_text(encoding="utf-8")
    start = doc.find(GUARD_START)
    end = doc.find(GUARD_END)
    if start != -1 and end != -1:
        updated = doc[:start] + generated + doc[end + len(GUARD_END) :]
    else:
        updated = (
            doc.rstrip("\n")
            + "\n\n## Server Port & Tool Reference (auto-generated)\n\n"
            + generated
            + "\n"
        )
    REFERENCE_DOC.write_text(updated, encoding="utf-8")
    print(f"Updated {REFERENCE_DOC.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
