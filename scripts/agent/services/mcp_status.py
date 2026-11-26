"""scripts/agent/services/mcp_status.py

McpStatusService — probe all MCP servers and format the status table.
"""

from __future__ import annotations

import dataclasses
import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, cast

import httpx
from shared.mcp_config import TransportType, get_effective_health_timeout
from shared.mcp_health import McpServerHealthState

from agent.lifecycle import LifecycleState
from agent.services.enums import McpAvailability, McpTier
from agent.services.exceptions import McpProbeError
from agent.services.mcp_health import _probe_mcp_health_detail
from agent.services.models import McpProbeResult
from agent.shared.health_models import McpHealthProbeResult, interpret_health_body

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from agent.context import AgentContext
    from agent.services.config_pending_state import McpChangeKind, PendingMcpRecord

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
    """Get the health state for a server, falling back to UNAVAILABLE."""
    registry = ctx.services_required.health_registry
    if registry is None:
        return McpServerHealthState.UNAVAILABLE
    return cast(McpServerHealthState, registry.get_state(key))


@dataclasses.dataclass(frozen=True)
class McpPendingRow:
    """One MCP definition change `/mcp status` shows as pending, not as a live server.

    A distinct type from `McpProbeResult` on purpose: a pending definition has no
    probe state, so the command layer cannot render one as if it were a running
    server (REQ-008).

    Attributes:
        server_key: MCP server the record names.
        change: Definition change kind.
        field_paths: Config field paths that changed.  Field paths only: no
            configured value reaches the display (REQ-011).
    """

    server_key: str
    change: McpChangeKind
    field_paths: tuple[str, ...]


class McpStatusService:
    """Probe all configured MCP servers and collect their health statuses."""

    def __init__(self, ctx: AgentContext) -> None:
        """Initialize the MCP status service with the agent context."""
        self._ctx = ctx

    @staticmethod
    def pending_rows(records: tuple[PendingMcpRecord, ...]) -> list[McpPendingRow]:
        """Return the display rows for the pending MCP records passed in.

        The records are an argument and no lifecycle or probe state is read: a
        pending definition has no live process, so a pending row can neither be
        built from a probe nor rendered as one (REQ-008, AC-4).
        """
        return [
            McpPendingRow(
                server_key=record.server_key,
                change=record.change,
                field_paths=record.field_paths,
            )
            for record in records
        ]

    async def probe_all(self) -> list[McpProbeResult]:
        """Probe every configured MCP server and collect health statuses."""
        ctx = self._ctx
        results: list[McpProbeResult] = []
        for key, cfg in ctx.cfg.mcp.mcp_servers.items():
            effective_timeout = get_effective_health_timeout(cfg)
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(timeout=effective_timeout)
            ) as probe:
                result = await self._probe_single_server_with_interpretation(
                    probe, ctx, key, cfg
                )
                results.append(result)
        return results

    async def _probe_single_server_with_interpretation(
        self,
        probe: httpx.AsyncClient,
        ctx: AgentContext,
        key: str,
        cfg: Any,
    ) -> McpProbeResult:
        """Probe a single MCP server and return its status result with interpretation fields."""
        auth = bool(cfg.auth_token)
        _reg = ctx.services_required.runtime_tools
        _server_tool_tiers = [
            str(t.agent_safety_tier)
            for t in (_reg.all_tools() if _reg is not None else [])
            if t.server_key == key
        ]
        tier = _tier_for_server(_server_tool_tiers)
        (
            availability,
            sandbox_backend,
            restart_rec_http,
            op_action_http,
            body_reason,
            self_reported_status,
            dep_summary,
            detail_summary,
            parse_failure_reason,
            probe_result,
        ) = await self._get_http_status_with_interpretation(
            probe, cfg.url, cfg.auth_headers()
        )
        health = _resolve_health_state(ctx, key).value.upper()
        lifecycle = ctx.services_required.lifecycle
        lifecycle_state = lifecycle.get_transport_state(key).value
        snapshot_fn = getattr(lifecycle, "get_process_snapshot", None)
        snapshot = snapshot_fn(key) if snapshot_fn is not None else None
        # A retained record (exit not confirmed) names a live process: the row
        # shows its outcome and asks for operator action (REQ-009, AC-1).
        unconfirmed_state = lifecycle_state in (
            LifecycleState.EXIT_UNCONFIRMED.value,
            LifecycleState.SIGNAL_NOT_DELIVERED.value,
        )
        termination_outcome = (
            snapshot.get("termination_outcome") if snapshot is not None else None
        )
        restart_recommended = (
            lifecycle_state == LifecycleState.FAILED.value or unconfirmed_state
        ) or restart_rec_http
        operator_action_required = op_action_http or unconfirmed_state
        health_reason = body_reason
        if not health_reason and unconfirmed_state:
            health_reason = lifecycle_state
        elif not health_reason and op_action_http:
            health_reason = "operator_action_required"
        elif not health_reason and restart_rec_http:
            health_reason = "restart_recommended"
        reachable = probe_result.reachable if probe_result else False
        raw_body = probe_result.body if probe_result else {}
        # Log dependency failures and parse failures
        if dep_summary:
            logger.warning(
                "MCP server '%s' has dependency failures: %s",
                key,
                ", ".join(dep_summary),
            )
        if parse_failure_reason:
            logger.warning(
                "MCP server '%s' health parse failure: %s",
                key,
                parse_failure_reason,
            )
        result = McpProbeResult(
            key=key,
            transport=cfg.transport,
            startup_mode=cfg.startup_mode,
            auth=auth,
            tier=tier,
            role=cfg.role or "",
            availability=availability,
            health=health,
            endpoint=cfg.url if cfg.transport == TransportType.HTTP else "",
            sandbox_backend=sandbox_backend,
            managed=snapshot is not None,
            pid=snapshot.get("pid") if snapshot else None,
            pgid=snapshot.get("pgid") if snapshot else None,
            running=snapshot.get("running") if snapshot else None,
            last_exit_code=snapshot.get("last_exit_code") if snapshot else None,
            lifecycle_state=lifecycle_state,
            restart_recommended=restart_recommended,
            operator_action_required=operator_action_required,
            last_shutdown_result=termination_outcome or "",
            health_reason=health_reason,
            reachable=reachable,
            body=raw_body,
            self_reported_status=self_reported_status,
            dependency_summary=dep_summary,
            details_summary=detail_summary,
            parse_failure_reason=parse_failure_reason,
            static_visibility=not cfg.is_disabled,
        )
        return result

    async def _get_http_status(
        self,
        probe: httpx.AsyncClient,
        url: str,
        headers: dict[str, str] | None = None,
    ) -> tuple[McpAvailability, str, bool, bool, str]:
        """Probe the MCP server health endpoint and return availability with details."""
        if not url:
            return McpAvailability.NO_URL, "", False, False, ""
        probe_result = await _probe_mcp_health_detail(probe, url, headers)
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

    async def _get_http_status_with_interpretation(
        self,
        probe: httpx.AsyncClient,
        url: str,
        headers: dict[str, str] | None = None,
    ) -> tuple[
        McpAvailability,
        str,
        bool,
        bool,
        str,
        str,
        list[str],
        list[str],
        str | None,
        McpHealthProbeResult,
    ]:
        """Probe the MCP server health endpoint and return availability with interpretation.

        Returns (availability, sandbox, restart_rec, op_action, reason,
                 self_reported_status, dep_summary, detail_summary, parse_failure_reason,
                 probe_result).
        """
        from agent.shared.health_models import McpHealthProbeResult

        if not url:
            return (
                McpAvailability.NO_URL,
                "",
                False,
                False,
                "",
                "",
                [],
                [],
                None,
                McpHealthProbeResult(
                    reachable=False,
                    status_code=None,
                    restart_recommended=False,
                    operator_action_required=False,
                    body={},
                ),
            )
        probe_result = await _probe_mcp_health_detail(probe, url, headers)
        sandbox = ""
        reason = ""
        self_reported_status = ""
        dep_summary: list[str] = []
        detail_summary: list[str] = []
        parse_failure_reason: str | None = None
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
            # Interpret the health body for structured fields
            try:
                interp = interpret_health_body(probe_result.body)
                self_reported_status = interp.self_reported_status
                dep_summary = interp.dependency_summary
                detail_summary = interp.details_summary
            except Exception:  # noqa: BLE001 — non-crashing on interpretation error
                pass
        if probe_result.parse_failed:
            parse_failure_reason = probe_result.parse_error
        elif not probe_result.reachable or probe_result.status_code is None:
            return (
                McpAvailability.FAIL,
                sandbox,
                False,
                False,
                reason,
                self_reported_status,
                dep_summary,
                detail_summary,
                parse_failure_reason,
                probe_result,
            )
        if probe_result.status_code == HTTPStatus.OK:
            return (
                McpAvailability.OK,
                sandbox,
                probe_result.restart_recommended,
                probe_result.operator_action_required,
                reason,
                self_reported_status,
                dep_summary,
                detail_summary,
                parse_failure_reason,
                probe_result,
            )
        return (
            McpAvailability.HTTP_ERROR,
            sandbox,
            probe_result.restart_recommended,
            probe_result.operator_action_required,
            reason,
            self_reported_status,
            dep_summary,
            detail_summary,
            parse_failure_reason,
            probe_result,
        )


def _tier_for_server(declared_tiers: list[str]) -> McpTier:
    """Return the highest-risk McpTier from each tool's declared agent_safety_tier.

    Agentcfg003 REQ-004 (AC-04): the tiers come from the registered RuntimeTool
    entries their producers declared, not from a configuration map.
    Raises McpProbeError for unknown tier strings.
    Falls back to READ_ONLY when the server has no registered tools.
    """
    best = McpTier.READ_ONLY
    for raw in declared_tiers:
        try:
            tier = McpTier(raw)
        except ValueError:
            raise McpProbeError(f"Unknown declared tier {raw!r}")
        if _TIER_PRIORITY.get(tier, 0) > _TIER_PRIORITY.get(best, 0):
            best = tier
    return best
