"""agent/services/mcp_status.py

McpStatusService — probe all MCP servers and format the status table.

Extracted from cmd_mcp._McpMixin so the presentation logic can be
tested without a running REPL.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any, cast

import httpx
from shared.mcp_config import McpServerHealthState, TransportType

from agent.lifecycle import LifecycleState
from agent.repl_health import _probe_mcp_health_detail
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
    """Get the health state for a server, falling back to UNKNOWN."""
    registry = ctx.services_required.health_registry
    if registry is None:
        return McpServerHealthState.UNKNOWN
    return cast(McpServerHealthState, registry.get_state(key))


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
        (
            availability,
            endpoint,
            sandbox_backend,
            restart_rec_http,
            op_action_http,
            body_reason,
        ) = await self._resolve_endpoint(probe, ctx, key, cfg)
        health = _resolve_health_state(ctx, key).value.upper()
        lifecycle = ctx.services_required.lifecycle
        lifecycle_state = lifecycle.get_transport_state(key).value
        snapshot_fn = getattr(lifecycle, "get_process_snapshot", None)
        snapshot = snapshot_fn(key) if snapshot_fn is not None else None
        restart_recommended = (
            lifecycle_state == LifecycleState.FAILED.value
        ) or restart_rec_http
        health_reason = body_reason
        if not health_reason and op_action_http:
            health_reason = "operator_action_required"
        elif not health_reason and restart_rec_http:
            health_reason = "restart_recommended"
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
            managed=snapshot is not None,
            pid=snapshot.get("pid") if snapshot else None,
            pgid=snapshot.get("pgid") if snapshot else None,
            running=snapshot.get("running") if snapshot else None,
            last_exit_code=snapshot.get("last_exit_code") if snapshot else None,
            lifecycle_state=lifecycle_state,
            restart_recommended=restart_recommended,
            operator_action_required=op_action_http,
            health_reason=health_reason,
        )

    async def _resolve_endpoint(
        self,
        probe: httpx.AsyncClient,
        ctx: AgentContext,
        key: str,
        cfg: Any,
    ) -> tuple[McpAvailability, str, str, bool, bool, str]:
        """Resolve availability, endpoint string, sandbox_backend, restart_recommended, operator_action_required, and body reason for a single server."""
        if cfg.transport == TransportType.HTTP:
            (
                availability,
                sandbox_backend,
                restart_rec,
                op_action,
                body_reason,
            ) = await self._get_http_status(probe, cfg.url)
            return (
                availability,
                cfg.url,
                sandbox_backend,
                restart_rec,
                op_action,
                body_reason,
            )
        return McpAvailability.UNKNOWN, "", "", False, False, ""

    async def _get_http_status(
        self, probe: httpx.AsyncClient, url: str
    ) -> tuple[McpAvailability, str, bool, bool, str]:
        if not url:
            return McpAvailability.NO_URL, "", False, False, ""
        probe_result = await _probe_mcp_health_detail(probe, url)
        sandbox = ""
        reason = ""
        if probe_result.body and isinstance(probe_result.body, dict):
            details = probe_result.body.get("details", {})
            if isinstance(details, dict):
                sb = details.get("sandbox_backend", "")
                if sb:
                    sandbox = str(sb)
            reason_raw = probe_result.body.get("reason") or probe_result.body.get(
                "message"
            )
            if reason_raw is not None:
                reason = str(reason_raw)
        if not probe_result.reachable or probe_result.status_code is None:
            return McpAvailability.FAIL, sandbox, False, False, reason
        if probe_result.status_code == HTTPStatus.OK:
            return (
                McpAvailability.OK,
                sandbox,
                probe_result.restart_recommended,
                probe_result.operator_action_required,
                reason,
            )
        return (
            McpAvailability.HTTP_ERROR,
            sandbox,
            probe_result.restart_recommended,
            probe_result.operator_action_required,
            reason,
        )


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
