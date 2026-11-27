#!/usr/bin/env python3
"""scripts/agent/commands/cmd_mcp.py

MCP server management mixin for CommandRegistry.

Thin dispatcher that delegates to:
  McpStatusService  (agent/services/mcp_status.py)  — /mcp status probe

Formatting (table, next-steps) is handled in this module — not in the services.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Any

from shared.mcp_health import (
    HEALTH_REASON_HALF_OPEN_TRIAL_IN_PROGRESS,
    HEALTH_REASON_SERVER_UNAVAILABLE,
    McpServerHealthRegistry,
    McpServerHealthState,
)

from agent.commands.exceptions import UnknownSubcommandError
from agent.commands.mixin_base import MixinBase
from agent.secrets_masker import _mask_secrets, redact_path
from agent.services.config_pending_state import pending_state_for
from agent.services.enums import McpAvailability
from agent.services.mcp_status import (
    TIER_LABELS,
    McpPendingRow,
    McpStatusService,
)
from agent.services.models import McpProbeResult
from agent.shared.health_models import interpret_health_body

if TYPE_CHECKING:
    from shared.runtime_tool_registry import RuntimeToolRegistry

logger = logging.getLogger(__name__)

# Column headers of the live MCP probe table.
_MCP_STATUS_HEADERS = [
    "SERVER",
    "TRANS",
    "MODE",
    "AUTH",
    "WRITE",
    "ROLE",
    "STATUS",
    "LIFECYCLE",
    "PID",
    "ENDPOINT/CMD",
]

# Column headers of the RuntimeToolRegistry diagnostics table.
_TOOL_DIAGNOSTIC_HEADERS = [
    "NAME",
    "SERVER",
    "CONFIG_DEP",
    "ENABLED",
    "DISABLED_REASON",
    "LLM_VISIBLE",
]

# Availability values the status line counts as unreachable.
_UNREACHABLE_AVAILABILITY = {
    McpAvailability.FAIL,
    McpAvailability.HTTP_ERROR,
    McpAvailability.DEAD,
}


def _display_value(value: object) -> str:
    """Render one health-interpretation value for display (REQ-005, AC-1).

    A value that is an absolute filesystem path is reduced to its logical identifier;
    every value is masked before it reaches the display line.
    """
    text = str(value)
    if text.startswith("/") and "/" in text[1:]:
        text = redact_path(text)
    return _mask_secrets(text)


def _format_health_interpretation(result: McpProbeResult) -> str:
    """Format health interpretation details for a single MCP server."""
    max_detail_len = 200
    lines: list[str] = []
    try:
        interp = interpret_health_body(result.body)
        # Status comparison
        agent_observed = "reachable" if result.reachable else "unreachable"
        lines.append(f"  Self-reported: {_display_value(interp.self_reported_status)}")
        lines.append(f"  Agent observed: {agent_observed}")
        # Ready state
        lines.append(f"  Ready: {_display_value(interp.ready)}")
        # Dependency failures
        if interp.dependency_summary:
            lines.append("  Dependencies:")
            for dep in interp.dependency_summary:
                lines.append(f"    - {_display_value(dep)}")
        # Details summary (masked first, then truncated, so the cut cannot open a masked value)
        if interp.details_summary:
            detail_text = _display_value("; ".join(interp.details_summary))
            if len(detail_text) > max_detail_len:
                detail_text = detail_text[:max_detail_len] + "..."
            lines.append(f"  Details: {detail_text}")
        # Action items
        if interp.restart_recommended:
            lines.append("  [!] Restart recommended")
        if interp.operator_action_required:
            lines.append("  [!] Operator action required")
        # Parse failure
        if interp.parse_failure_reason:
            lines.append(
                f"  [!] Parse failure: {_display_value(interp.parse_failure_reason)}"
            )
    except Exception as e:  # noqa: BLE001 — status display must not abort on unexpected health-interpretation shape
        lines.append(f"  [!] Interpretation error: {_display_value(e)}")
    return "\n".join(lines)


def _format_availability_display(
    result: McpProbeResult,
    registry: McpServerHealthRegistry | None,
) -> tuple[str, str]:
    """Return the static-visibility and dynamic-health lines for one server row.

    Static visibility is the config-derived fact (startup_mode=none means the
    server's tools are excluded from the LLM tool surface). Dynamic health is
    the registry circuit state composed at display time, with a closed reason
    code and retry timing only for UNAVAILABLE/HALF_OPEN rows. Both values
    are display-only: they never gate, reroute, or retry anything.
    """
    static_line = (
        f"Static visibility: {'visible' if result.static_visibility else 'excluded'}"
    )
    parts = [f"Dynamic health: {result.health}"]
    if result.health == McpServerHealthState.UNAVAILABLE.value.upper():
        parts.append(f"reason={HEALTH_REASON_SERVER_UNAVAILABLE}")
        if registry is not None:
            retry_after = registry.retry_after_seconds(result.key)
            if retry_after is not None:
                parts.append(f"retry_after={retry_after}")
    elif result.health == McpServerHealthState.HALF_OPEN.value.upper():
        parts.append(f"reason={HEALTH_REASON_HALF_OPEN_TRIAL_IN_PROGRESS}")
    return static_line, " ".join(parts)


def _format_mcp_status_rows(rows: Sequence[McpProbeResult]) -> list[list[str]]:
    """Render the live probe rows of the `/mcp status` table.

    One row per probed server: the probe state only, so a definition that is pending
    a restart cannot appear here (REQ-008).
    """
    table_rows: list[list[str]] = []
    for r in rows:
        role_display = (
            f"{r.role} [sb:{r.sandbox_backend}]".strip()
            if r.sandbox_backend
            else r.role
        )
        lifecycle_display = str(r.lifecycle_state) if r.lifecycle_state else "-"
        pid_display = str(r.pid) if r.pid is not None else "-"
        table_rows.append(
            [
                r.key,
                r.transport,
                r.startup_mode,
                "yes" if r.auth else "no",
                TIER_LABELS.get(r.tier, r.tier.value),
                role_display,
                f"{r.availability.value}/{r.health}",
                lifecycle_display,
                pid_display,
                r.endpoint,
            ]
        )
    return table_rows


def _format_tool_diagnostic_rows(
    diag_rows: Sequence[dict[str, Any]],
) -> list[list[str]]:
    """Render the RuntimeToolRegistry diagnostic rows."""
    table_rows: list[list[str]] = []
    for row in diag_rows:
        name_display = row.get("name", "-")
        marker = "[DISABLED] " if not row.get("enabled", True) else ""
        table_rows.append(
            [
                f"{marker}{name_display}",
                row.get("server_key", "-"),
                str(row.get("config_dependent", "-")),
                str(row.get("enabled", "-")),
                row.get("disabled_reason", "-") or "-",
                str(row.get("enabled_for_llm", "-")),
            ]
        )
    return table_rows


def _format_pending_mcp_rows(rows: Sequence[McpPendingRow]) -> list[str]:
    """Render the pending MCP definition rows, one line per pending record.

    The server key, the change kind, and the field paths that changed: a pending
    `auth_token` change is named by its field path and its value is never printed
    (REQ-011).
    """
    return [
        f"    [{row.server_key}] {row.change}: {', '.join(row.field_paths)}"
        for row in rows
    ]


class _McpMixin(MixinBase):
    """MCP server management slash-command handlers."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the MCP mixin via MixinBase constructor."""
        super().__init__(*args, **kwargs)

    def _write_servers_in_state(
        self,
        registry: McpServerHealthRegistry | None,
        server_keys: Iterable[str],
        state: McpServerHealthState,
        label: str,
    ) -> None:
        """Write a '<label> servers:' block listing server_keys currently in `state`."""
        keys = [
            key
            for key in server_keys
            if registry is not None and registry.get_state(key) == state
        ]
        if not keys:
            return
        self._out.write("")
        self._out.write(f"  {label} servers:")
        for key in keys:
            self._out.write(f"    [{label.upper()}] {key}")

    async def _cmd_mcp_status(self) -> None:
        """Print MCP server status table.

        Live probe rows come from `McpStatusService.probe_all` and pending MCP
        definition rows come from the container's `PendingConfigState`; the two are
        printed under separate headings so a pending definition is never shown as a
        running server (REQ-008, REQ-009).
        """
        ctx = self._ctx
        tool_registry = ctx.services_required.runtime_tools
        self._write_tool_summary(tool_registry)
        self._out.write("")
        rows = await McpStatusService(ctx).probe_all()
        self._out.write_table(_MCP_STATUS_HEADERS, _format_mcp_status_rows(rows))
        self._write_server_counts(rows)
        # Static visibility (config-derived) and dynamic health (registry
        # circuit state) are shown as separate labeled values per server.
        display_registry = ctx.services_required.health_registry
        self._write_availability_section(rows, display_registry)
        self._write_health_interpretation_section(rows)
        self._write_servers_in_state(
            display_registry,
            ctx.cfg.mcp.mcp_servers,
            McpServerHealthState.DEGRADED,
            "Degraded",
        )
        self._write_servers_in_state(
            display_registry,
            ctx.cfg.mcp.mcp_servers,
            McpServerHealthState.UNAVAILABLE,
            "Unavailable",
        )
        self._write_serialization_stats()
        self._write_tool_diagnostics(tool_registry)
        self._write_pending_mcp_section()

    def _write_tool_summary(self, tool_registry: RuntimeToolRegistry | None) -> None:
        """Write the one-line RuntimeToolRegistry tool summary."""
        if tool_registry is None:
            self._out.write("  Tools       — (no RuntimeToolRegistry available)")
            return
        diag_rows = tool_registry.diagnostics()
        llm_visible = sum(1 for r in diag_rows if r.get("enabled_for_llm"))
        disabled = sum(1 for r in diag_rows if r.get("disabled_reason"))
        unavailable = sum(
            1 for r in diag_rows if r.get("disabled_reason") == "unavailable"
        )
        self._out.write(
            f"  Tools       {llm_visible} LLM-visible / "
            f"{disabled} disabled / {unavailable} unavailable "
            "(from RuntimeToolRegistry)"
        )

    def _write_server_counts(self, rows: Sequence[McpProbeResult]) -> None:
        """Write the configured-server count line under the status table."""
        ok_count = sum(1 for r in rows if r.availability == McpAvailability.OK)
        unreachable_count = sum(
            1 for r in rows if r.availability in _UNREACHABLE_AVAILABILITY
        )
        self._out.write(
            f"\n  Servers     {len(rows)} configured ({ok_count} ok, {unreachable_count} unreachable)"
        )

    def _write_availability_section(
        self,
        rows: Sequence[McpProbeResult],
        registry: McpServerHealthRegistry | None,
    ) -> None:
        """Write the static-visibility and dynamic-health lines per server."""
        self._out.write("")
        self._out.write("  Availability:")
        for r in sorted(rows, key=lambda x: x.key):
            static_line, dynamic_line = _format_availability_display(r, registry)
            self._out.write(f"  [{r.key}]")
            self._out.write(f"    {static_line}")
            self._out.write(f"    {dynamic_line}")

    def _write_health_interpretation_section(
        self, rows: Sequence[McpProbeResult]
    ) -> None:
        """Write health interpretation details for the servers that have any."""
        has_interpretation = any(
            r.dependency_summary or r.parse_failure_reason or r.details_summary
            for r in rows
        )
        if not has_interpretation:
            return
        self._out.write("")
        self._out.write("  Health interpretation:")
        for r in sorted(rows, key=lambda x: x.key):
            interp_lines = _format_health_interpretation(r)
            if interp_lines.strip():
                self._out.write(f"\n  [{r.key}]")
                self._out.write(interp_lines)

    def _write_serialization_stats(self) -> None:
        """Write the tool-serialization event summary, when any event was recorded."""
        from agent.tool_run_recorder import get_serialization_stats

        stats = get_serialization_stats()
        if stats["total_events"] <= 0:
            return
        events = self._ctx.stats.stat_serialization_events
        total_events = len(events) or stats["total_events"]
        reason_counts: dict[str, int] = {}
        trigger_counts: dict[str, int] = {}
        total_affected = 0
        for e in events:
            reason = e.get("serial_reason") or e.get("reason", "unknown")
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
            trigger = e.get("trigger_tool", "unknown")
            trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1
            total_affected += e.get("affected_count", 0)
        avg_affected = total_affected / total_events if total_events > 0 else 0
        self._out.write(
            f"  Serialization {total_events} events (avg {avg_affected:.1f} tools/event)"
        )
        if reason_counts:
            reason_str = ", ".join(
                f"{k}: {v}" for k, v in sorted(reason_counts.items())
            )
            self._out.write(f"    By reason: {reason_str}")
        if trigger_counts:
            top_triggers = sorted(trigger_counts.items(), key=lambda x: -x[1])[:5]
            trigger_str = ", ".join(f"{k} ({v})" for k, v in top_triggers)
            self._out.write(f"    Top triggers: {trigger_str}")

    def _write_tool_diagnostics(
        self, tool_registry: RuntimeToolRegistry | None
    ) -> None:
        """Write the RuntimeToolRegistry diagnostics table under the status table.

        A tool dropped at construction has no diagnostic row, so the excluded tools are
        listed separately with the reason the registry recorded (REQ-006). When the reason is
        `capability` the section states that the mapping is fixed at construction and a change
        in tool availability needs a restart (REQ-008, AC-08): there is no live swap.
        """
        if tool_registry is None:
            return
        diag_rows = tool_registry.diagnostics()
        excluded = tool_registry.excluded_tools()
        if not diag_rows and not excluded:
            return
        self._out.write("")
        self._out.write("  Tools (RuntimeToolRegistry):")
        if diag_rows:
            self._out.write_table(
                _TOOL_DIAGNOSTIC_HEADERS, _format_tool_diagnostic_rows(diag_rows)
            )
        if excluded:
            self._out.write("    Excluded tools:")
            for name, reason in sorted(excluded.items()):
                self._out.write(f"      {name}: {reason}")
            if any(reason == "capability" for reason in excluded.values()):
                self._out.write(
                    "      [!] Availability is fixed at construction: "
                    "a capability change requires a restart"
                )

    def _write_pending_mcp_section(self) -> None:
        """Write the pending MCP definition rows, separate from the live probe rows.

        The rows come from the container's `PendingConfigState`, so a definition an
        earlier `/reload` recorded is shown here even though no probe was run for it
        and no live process exists for it (REQ-008, AC-4, AC-5).  Prints nothing when
        nothing is pending.
        """
        pending = pending_state_for(self._ctx)
        if pending is None:
            return
        rows = McpStatusService.pending_rows(pending.pending_mcp_records())
        if not rows:
            return
        self._out.write("")
        self._out.write("  Pending restart (MCP definitions):")
        for line in _format_pending_mcp_rows(rows):
            self._out.write(line)

    async def _cmd_mcp(self, args: str = "") -> None:
        """MCP server status probe."""
        parts = args.strip().split(None, 1)
        sub = parts[0] if parts else ""
        if sub in ("status", ""):
            await self._cmd_mcp_status()
        elif sub == "tools":
            await self._cmd_mcp_tools()
        else:
            raise UnknownSubcommandError(sub, ("status", "tools"))

    async def _cmd_mcp_tools(self) -> None:
        """Print RuntimeToolRegistry diagnostics table."""
        tool_registry = self._ctx.services_required.runtime_tools
        if tool_registry is None:
            self._out.write("  No RuntimeToolRegistry available.")
            return
        diag_rows = tool_registry.diagnostics()
        if not diag_rows:
            self._out.write("  No tools registered.")
            return
        self._out.write_table(
            _TOOL_DIAGNOSTIC_HEADERS, _format_tool_diagnostic_rows(diag_rows)
        )
