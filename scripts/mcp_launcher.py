#!/usr/bin/env python3
"""scripts/mcp_launcher.py

Unified standalone launcher for individual MCP servers. Discovers every
MCPServer subclass under mcp_servers.* by reflection and launches one by key,
for local development/debugging without hand-editing sys.path or memorizing
each server's entry-point module path.

Usage:
    uv run python scripts/mcp_launcher.py --list
    uv run python scripts/mcp_launcher.py <server_key>
    uv run python scripts/mcp_launcher.py <server_key> --force
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import pkgutil
import sys

import httpx
from mcp_servers.server import MCPServer


def discover_servers() -> dict[str, type[MCPServer]]:
    """Discover every MCPServer subclass under mcp_servers.*, keyed by server_key.

    A module that raises on import is skipped (logged as a warning) rather than
    aborting discovery of the remaining servers.
    """
    registry: dict[str, type[MCPServer]] = {}
    import mcp_servers

    for _, modname, _ in pkgutil.walk_packages(
        mcp_servers.__path__, prefix="mcp_servers."
    ):
        if modname.rpartition(".")[2] == "__main__":
            # __main__ submodules (e.g. mdq's `python -m mcp_servers.mdq`) run a
            # server unconditionally at import time; they carry no class the
            # discovery loop below needs, since the real class lives in the
            # sibling `server` module.
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
            print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, MCPServer) and obj is not MCPServer:
                key = getattr(obj, "server_key", None) or obj.server_name.removesuffix(
                    "-mcp"
                )
                registry[key] = obj
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

    registry = discover_servers()
    if args.list or not args.server_key:
        for key in sorted(registry):
            print(key)
        return

    server_cls = registry.get(args.server_key)
    if server_cls is None:
        print(
            f"unknown server_key: {args.server_key!r}. Use --list to see available keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    instance = server_cls()
    port = instance.http_port
    if not args.force and port_is_responding(port):
        print(
            f"port {port} is already responding — {args.server_key} may be running under the agent. "
            "Use --force to start anyway.",
            file=sys.stderr,
        )
        sys.exit(1)
    instance.run_http()  # type: ignore[attr-defined]


if __name__ == "__main__":
    main()
