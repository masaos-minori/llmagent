"""agent/services/mcp_status.py
McpStatusService — probe all MCP servers and format the status table.

Extracted from cmd_mcp._McpMixin so the presentation logic can be
tested without a running REPL.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import httpx
from shared.tool_constants import DELETE_TOOLS, WRITE_TOOLS

if TYPE_CHECKING:
    from agent.context import AgentContext

# Tools that imply write capability; used to set the WRITE column in /mcp status.
_WRITE_CAPABLE_TOOLS: frozenset[str] = (
    WRITE_TOOLS | DELETE_TOOLS | frozenset({"shell_run"})
)


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
        results: list[McpServerStatus] = []
        async with httpx.AsyncClient(timeout=5.0) as probe:
            for key, cfg in ctx.cfg.mcp_servers.items():
                auth = "yes" if cfg.auth_token else "no"
                write = (
                    "yes"
                    if any(t in _WRITE_CAPABLE_TOOLS for t in cfg.tool_names)
                    else "no"
                )
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
        col = "{:<14} {:<6} {:<11} {:<5} {:<6} {:<12} {:<16} {}"
        lines = [
            col.format(
                "SERVER", "TRANS", "MODE", "AUTH", "WRITE", "ROLE", "STATUS", "ENDPOINT/CMD"
            ),
            "-" * 95,
        ]
        for r in rows:
            lines.append(
                col.format(
                    r.key, r.transport, r.startup_mode, r.auth, r.write,
                    r.role, r.status, r.endpoint,
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

    def _get_stdio_status(
        self, ctx: AgentContext, key: str, startup_mode: str
    ) -> str:
        transport = ctx.services.stdio_procs.get(key)
        if transport is None:
            return "STOPPED" if startup_mode == "ondemand" else "NOT_STARTED"
        return "RUNNING" if transport.is_alive() else "DEAD"
