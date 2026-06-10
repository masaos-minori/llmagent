"""mcp/installer_port.py
Port allocation helpers for MCP server installer.

scan_used_ports() gathers used ports from:
  1. config/agent.toml [mcp_servers.*.url] — primary, config-driven
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

# Built-in service ports reserved by the system.
_RESERVED_PORTS: frozenset[int] = frozenset({8001, 8002, 8003, 8004, 8005, 8006})
_PORT_START = 8007

# NOTE: _REPO_ROOT is deprecated; pass repo_root explicitly. To be removed in Phase 2.
_REPO_ROOT = Path(__file__).parent.parent.parent


def _ports_from_config(config_dir: Path) -> set[int]:
    """Extract port numbers from config/agent.toml mcp_servers[*].url."""
    ports: set[int] = set()
    agent_toml = config_dir / "agent.toml"
    if not agent_toml.exists():
        return ports
    try:
        with agent_toml.open("rb") as f:
            cfg = tomllib.load(f)
    except OSError as e:
        raise OSError(f"Cannot read {agent_toml}: {e}") from e
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"Invalid TOML in {agent_toml}: {e}") from e
    for srv in cfg.get("mcp_servers", {}).values():
        url = srv.get("url", "")
        m = re.search(r":(\d+)/?$", url)
        if m:
            ports.add(int(m.group(1)))
    return ports


def scan_used_ports(repo_root: Path | None = None) -> set[int]:
    """Return set of used ports: reserved + agent.toml config."""
    root = repo_root if repo_root is not None else _REPO_ROOT
    used: set[int] = set(_RESERVED_PORTS)
    used |= _ports_from_config(root / "config")
    return used


def suggest_port(repo_root: Path | None = None) -> int:
    """Return the lowest available port >= _PORT_START."""
    used = scan_used_ports(repo_root)
    port = _PORT_START
    while port in used:
        port += 1
    return port
