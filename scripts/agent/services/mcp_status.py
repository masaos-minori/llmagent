"""agent/services/mcp_status.py
McpStatusService — probe all MCP servers and format the status table.

Extracted from cmd_mcp._McpMixin so the presentation logic can be
tested without a running REPL.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from agent.context import AgentContext

# Tier priority for determining the highest-risk tier across a server's tool set.
_TIER_PRIORITY: dict[str, int] = {
    "READ_ONLY": 0,
    "WRITE_SAFE": 1,
    "WRITE_DANGEROUS": 2,
    "ADMIN": 3,
}

# Display labels for each tier value in the WRITE column.
_TIER_LABEL: dict[str, str] = {
    "READ_ONLY": "no",
    "WRITE_SAFE": "write-safe",
    "WRITE_DANGEROUS": "dangerous",
    "ADMIN": "admin",
}


@dataclass
class McpServerStatus:
    key: str
    transport: str
    startup_mode: str
    auth: str
    write: str
    role: str
    status: str
    endpoint: str


class McpStatusService:
    """Probe all configured MCP servers and format their status table."""

    def __init__(self, ctx: AgentContext) -> None:
        self._ctx = ctx

    async def probe_all(self) -> list[McpServerStatus]:
        ctx = self._ctx
        tiers: dict[str, str] = ctx.cfg.approval.tool_safety_tiers
        results: list[McpServerStatus] = []
        async with httpx.AsyncClient(timeout=5.0) as probe:
            for key, cfg in ctx.cfg.mcp.mcp_servers.items():
                auth = "yes" if cfg.auth_token else "no"
                write = _tier_label_for_server(cfg.tool_names, tiers)
                if cfg.transport == "http":
                    status = await self._get_http_status(probe, cfg.url)
                    endpoint = cfg.url
                else:
                    status = self._get_stdio_status(ctx, key, cfg.startup_mode)
                    endpoint = " ".join(cfg.cmd) if cfg.cmd else ""
                results.append(
                    McpServerStatus(
                        key=key,
                        transport=cfg.transport,
                        startup_mode=cfg.startup_mode,
                        auth=auth,
                        write=write,
                        role=cfg.role or "",
                        status=status,
                        endpoint=endpoint,
                    )
                )
        return results

    def format_table(self, rows: list[McpServerStatus]) -> str:
        col = "{:<14} {:<6} {:<11} {:<5} {:<12} {:<12} {:<16} {}"
        lines = [
            col.format(
                "SERVER",
                "TRANS",
                "MODE",
                "AUTH",
                "WRITE",
                "ROLE",
                "STATUS",
                "ENDPOINT/CMD",
            ),
            "-" * 99,
        ]
        for r in rows:
            lines.append(
                col.format(
                    r.key,
                    r.transport,
                    r.startup_mode,
                    r.auth,
                    r.write,
                    r.role,
                    r.status,
                    r.endpoint,
                )
            )
        return "\n".join(lines)

    async def _get_http_status(self, probe: httpx.AsyncClient, url: str) -> str:
        if not url:
            return "no-url"
        try:
            r = await probe.get(f"{url}/health")
            return "OK" if r.status_code == 200 else f"HTTP {r.status_code}"
        except Exception as e:
            return f"FAIL ({e})"

    def _get_stdio_status(self, ctx: AgentContext, key: str, startup_mode: str) -> str:
        transport = ctx.services.stdio_procs.get(key)
        if transport is None:
            return "STOPPED" if startup_mode == "ondemand" else "NOT_STARTED"
        return "RUNNING" if transport.is_alive() else "DEAD"


def _tier_label_for_server(tool_names: list[str], tiers: dict[str, str]) -> str:
    """Return the WRITE column label for a server based on its tool_safety_tiers.

    Iterates the server's tool_names, looks each up in the global tiers map,
    and returns the label for the highest-risk tier found.  Falls back to
    'no' (READ_ONLY) when tiers is empty or no tool is classified.
    """
    best = "READ_ONLY"
    for name in tool_names:
        tier = tiers.get(name, "READ_ONLY")
        if _TIER_PRIORITY.get(tier, 0) > _TIER_PRIORITY.get(best, 0):
            best = tier
    return _TIER_LABEL.get(best, "no")
