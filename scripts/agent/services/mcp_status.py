"""agent/services/mcp_status.py
McpStatusService — probe all MCP servers and format the status table.

Extracted from cmd_mcp._McpMixin so the presentation logic can be
tested without a running REPL.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any

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


def _resolve_health_state(ctx: AgentContext, key: str) -> McpServerHealthState:
    """Get the health state for a server, falling back to HEALTHY."""
    registry = ctx.services.health_registry
    if registry is None:
        return McpServerHealthState.HEALTHY
    return registry.get_state(key)


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
                result = await self._probe_single_server(probe, ctx, key, cfg, tiers)
                results.append(result)
        return results

    async def _probe_single_server(
        self,
        probe: httpx.AsyncClient,
        ctx: AgentContext,
        key: str,
        cfg: Any,
        tiers: dict[str, str],
    ) -> McpProbeResult:
        """Probe a single MCP server and return its status result."""
        auth = bool(cfg.auth_token)
        tier = _tier_for_server(cfg.tool_names, tiers)
        availability, endpoint, sandbox_backend = await self._resolve_endpoint(
            probe, ctx, key, cfg
        )
        health = _resolve_health_state(ctx, key).value.upper()
        return McpProbeResult(
            key=key,
            transport=cfg.transport,
            startup_mode=cfg.startup_mode,
            auth=auth,
            tier=tier,
            role=cfg.role or "",
            availability=availability,
            health=health,
            endpoint=endpoint,
            sandbox_backend=sandbox_backend,
        )

    async def _resolve_endpoint(
        self,
        probe: httpx.AsyncClient,
        ctx: AgentContext,
        key: str,
        cfg: Any,
    ) -> tuple[McpAvailability, str, str]:
        """Resolve availability, endpoint string, and sandbox_backend for a single server."""
        if cfg.transport == "http":
            availability, sandbox_backend = await self._get_http_status(probe, cfg.url)
            return availability, cfg.url, sandbox_backend
        return (
            self._get_stdio_status(ctx, key, cfg.startup_mode),
            " ".join(cfg.cmd) if cfg.cmd else "",
            "",
        )

    async def _get_http_status(
        self, probe: httpx.AsyncClient, url: str
    ) -> tuple[McpAvailability, str]:
        if not url:
            return McpAvailability.NO_URL, ""
        try:
            r = await probe.get(f"{url}/health")
            if r.status_code == HTTPStatus.OK:
                try:
                    body = r.json()
                    sandbox = (
                        body.get("details", {}).get("sandbox_backend", "")
                        if isinstance(body, dict)
                        else ""
                    )
                except httpx.DecodingError:
                    sandbox = ""
                return McpAvailability.OK, str(sandbox) if sandbox else ""
            return McpAvailability.HTTP_ERROR, ""
        except (httpx.RequestError, httpx.HTTPStatusError):
            return McpAvailability.FAIL, ""

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
