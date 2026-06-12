"""agent/services/mcp_status.py
McpStatusService — probe all MCP servers and format the status table.

Extracted from cmd_mcp._McpMixin so the presentation logic can be
tested without a running REPL.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

import httpx
from shared.mcp_config import McpServerHealthState

from agent.services.enums import McpAvailability, McpTier
from agent.services.exceptions import McpProbeError
from agent.services.models import McpProbeResult

if TYPE_CHECKING:
    from agent.context import AgentContext

# Tier priority for determining the highest-risk tier across a server's tool set.
_TIER_PRIORITY: dict[McpTier, int] = {
    McpTier.READ_ONLY: 0,
    McpTier.WRITE_SAFE: 1,
    McpTier.WRITE_DANGEROUS: 2,
    McpTier.ADMIN: 3,
}

# Display labels for each tier value in the WRITE column (used by renderers).
TIER_LABELS: dict[McpTier, str] = {
    McpTier.READ_ONLY: "no",
    McpTier.WRITE_SAFE: "write-safe",
    McpTier.WRITE_DANGEROUS: "dangerous",
    McpTier.ADMIN: "admin",
}


class McpStatusService:
    """Probe all configured MCP servers and format their status table."""

    def __init__(self, ctx: AgentContext) -> None:
        self._ctx = ctx

    async def probe_all(self) -> list[McpProbeResult]:
        ctx = self._ctx
        tiers: dict[str, str] = ctx.cfg.approval.tool_safety_tiers
        results: list[McpProbeResult] = []
        async with httpx.AsyncClient(timeout=5.0) as probe:
            for key, cfg in ctx.cfg.mcp.mcp_servers.items():
                auth = bool(cfg.auth_token)
                tier = _tier_for_server(cfg.tool_names, tiers)
                if cfg.transport == "http":
                    availability = await self._get_http_status(probe, cfg.url)
                    endpoint = cfg.url
                else:
                    availability = self._get_stdio_status(ctx, key, cfg.startup_mode)
                    endpoint = " ".join(cfg.cmd) if cfg.cmd else ""
                health_state = (
                    ctx.services.health_registry.get_state(key)
                    if ctx.services.health_registry
                    else McpServerHealthState.HEALTHY
                )
                health = health_state.value.upper()
                results.append(
                    McpProbeResult(
                        key=key,
                        transport=cfg.transport,
                        startup_mode=cfg.startup_mode,
                        auth=auth,
                        tier=tier,
                        role=cfg.role or "",
                        availability=availability,
                        health=health,
                        endpoint=endpoint,
                    )
                )
        return results

    async def _get_http_status(
        self, probe: httpx.AsyncClient, url: str
    ) -> McpAvailability:
        if not url:
            return McpAvailability.NO_URL
        try:
            r = await probe.get(f"{url}/health")
            return (
                McpAvailability.OK
                if r.status_code == HTTPStatus.OK
                else McpAvailability.HTTP_ERROR
            )
        except (httpx.RequestError, httpx.HTTPStatusError):
            return McpAvailability.FAIL

    def _get_stdio_status(
        self, ctx: AgentContext, key: str, startup_mode: str
    ) -> McpAvailability:
        transport = ctx.services.stdio_procs.get(key)
        if transport is None:
            return (
                McpAvailability.STOPPED
                if startup_mode == "ondemand"
                else McpAvailability.NOT_STARTED
            )
        return McpAvailability.OK if transport.is_alive() else McpAvailability.DEAD


def _tier_for_server(tool_names: list[str], tiers: dict[str, str]) -> McpTier:
    """Return the highest-risk McpTier for a server based on its tool_safety_tiers.

    Raises McpProbeError for unknown tier strings.
    Falls back to READ_ONLY when tiers is empty or no tool is classified.
    """
    best = McpTier.READ_ONLY
    for name in tool_names:
        raw = tiers.get(name)
        if raw is None:
            continue
        try:
            tier = McpTier(raw)
        except ValueError:
            raise McpProbeError(f"Unknown tier {raw!r} for tool {name!r}")
        if _TIER_PRIORITY.get(tier, 0) > _TIER_PRIORITY.get(best, 0):
            best = tier
    return best
