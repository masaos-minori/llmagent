#!/usr/bin/env python3
"""scripts/mcp_launcher.py

Unified standalone launcher for individual MCP servers. Finds every MCPServer
subclass under mcp_servers.* by static source analysis (no server module is
imported to list or resolve a key) and launches one by key, for local
development/debugging without hand-editing sys.path or memorizing each server's
entry-point module path. The chosen server's own config file is the only one the
process may read: the restriction is applied before its module is imported.

Usage:
    uv run python scripts/mcp_launcher.py --list
    uv run python scripts/mcp_launcher.py <server_key>
    uv run python scripts/mcp_launcher.py <server_key> --force
"""

from __future__ import annotations

import argparse
import ast
import dataclasses
import importlib
import sys
from pathlib import Path

import httpx
from shared.config_loader import ConfigLoader

_SCRIPTS_DIR = Path(__file__).resolve().parent
_SERVERS_DIR = _SCRIPTS_DIR / "mcp_servers"


@dataclasses.dataclass(frozen=True)
class ServerMeta:
    """Static description of one MCPServer subclass, read without importing it."""

    key: str
    module: str
    class_name: str
    own_config_file: str
    http_port: int


def _literal_class_attrs(node: ast.ClassDef) -> dict[str, object]:
    """Return the class-level `name = <literal>` assignments of a class body."""
    attrs: dict[str, object] = {}
    for stmt in node.body:
        if (
            isinstance(stmt, ast.Assign)
            and len(stmt.targets) == 1
            and isinstance(stmt.targets[0], ast.Name)
        ):
            try:
                attrs[stmt.targets[0].id] = ast.literal_eval(stmt.value)
            except ValueError:
                continue
    return attrs


def _is_mcp_server_subclass(node: ast.ClassDef) -> bool:
    """Return True when a class directly derives from MCPServer."""
    return any(
        isinstance(base, ast.Name) and base.id == "MCPServer" for base in node.bases
    )


def discover_server_metadata() -> dict[str, ServerMeta]:
    """Find every MCPServer subclass under mcp_servers.* keyed by server_key.

    Parses source files with `ast`; nothing is imported, so no module-level side
    effect (config loading, log files, database probes) runs. A file that cannot
    be parsed is skipped with a warning.
    """
    registry: dict[str, ServerMeta] = {}
    for path in sorted(_SERVERS_DIR.rglob("*_server.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeDecodeError) as exc:
            print(f"warning: could not parse {path}: {exc}", file=sys.stderr)
            continue
        module = ".".join(path.relative_to(_SCRIPTS_DIR).with_suffix("").parts)
        for node in tree.body:
            if not isinstance(node, ast.ClassDef) or not _is_mcp_server_subclass(node):
                continue
            attrs = _literal_class_attrs(node)
            name = attrs.get("server_name")
            if not isinstance(name, str):
                continue
            key = attrs.get("server_key") or name.removesuffix("-mcp")
            config_file = attrs.get("own_config_file")
            port = attrs.get("http_port")
            if not isinstance(key, str) or not isinstance(config_file, str):
                continue
            if not isinstance(port, int):
                continue
            registry[key] = ServerMeta(key, module, node.name, config_file, port)
    return registry


def port_is_responding(port: int, timeout: float = 0.5) -> bool:
    """Return True if something is already listening on port's /health endpoint."""
    try:
        resp = httpx.get(f"http://127.0.0.1:{port}/health", timeout=timeout)
        is_up: bool = resp.status_code < 500
        return is_up  # any response at all indicates something is listening
    except httpx.HTTPError:
        return False


def main() -> None:
    """Entry point for launching MCP servers from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "server_key", nargs="?", help="Server key to launch (see --list)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all discovered server keys"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the port-collision guard"
    )
    args = parser.parse_args()

    registry = discover_server_metadata()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    meta = registry.get(args.server_key)
    if meta is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not args.force and port_is_responding(meta.http_port):
        print(
            f"port {meta.http_port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    ConfigLoader.restrict_to(meta.own_config_file)
    module = importlib.import_module(meta.module)
    getattr(module, meta.class_name)().run_http()


if __name__ == "__main__":
    main()
