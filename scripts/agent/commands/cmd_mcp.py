#!/usr/bin/env python3
"""agent/commands/cmd_mcp.py

MCP server management mixin for CommandRegistry.

Thin dispatcher that delegates to:
  McpStatusService  (agent/services/mcp_status.py)  — /mcp status probe

Formatting (table, next-steps) is handled in this module — not in the services.
"""

import logging
from typing import Any

from shared.mcp_health import McpServerHealthState

from agent.commands.exceptions import UnknownSubcommandError
from agent.commands.mixin_base import MixinBase
from agent.services.enums import McpAvailability
from agent.services.mcp_status import TIER_LABELS, McpStatusService
from agent.services.models import McpProbeResult

logger = logging.getLogger(__name__)


def _format_mcp_table(rows: list[McpProbeResult]) -> str:
    """Format MCP server status rows as a fixed-width table string."""
    col = "{:<14} {:<6} {:<11} {:<5} {:<12} {:<12} {:<16} {:<8} {:>5} {}"
    lines = [
        col.format(
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
        ),
        "-" * 110,
    ]
    for r in rows:
        role_display = (
            f"{r.role} [sb:{r.sandbox_backend}]".strip()
            if r.sandbox_backend
            else r.role
        )
        lifecycle_display = str(r.lifecycle_state) if r.lifecycle_state else "-"
        pid_display = str(r.pid) if r.pid is not None else "-"
        lines.append(
            col.format(
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
            )
        )
    return "\n".join(lines)


class _McpMixin(MixinBase):
    """MCP server management slash-command handlers."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    async def _cmd_mcp_status(self) -> None:
        """Print MCP server status table."""
        ctx = self._ctx
        svc = McpStatusService(ctx)
        self._out.write(
            f"  Tools       {len(ctx.cfg.tool.tool_definitions)} (from config/tools_definitions.toml)"
        )
        self._out.write("")
        rows = await svc.probe_all()
        self._out.write(_format_mcp_table(rows))
        _UNREACHABLE = {
            McpAvailability.FAIL,
            McpAvailability.HTTP_ERROR,
            McpAvailability.DEAD,
        }
        ok_count = sum(1 for r in rows if r.availability == McpAvailability.OK)
        unreachable_count = sum(1 for r in rows if r.availability in _UNREACHABLE)
        self._out.write(
            f"\n  Servers     {len(rows)} configured ({ok_count} ok, {unreachable_count} unreachable)"
        )
        registry = ctx.services_required.health_registry
        degraded_keys = [
            key
            for key in ctx.cfg.mcp.mcp_servers
            if registry is not None
            and registry.get_state(key) == McpServerHealthState.DEGRADED
        ]
        if degraded_keys:
            self._out.write("")
            self._out.write("  Degraded servers:")
            for key in degraded_keys:
                reason = registry.get_degraded_reason(key) if registry else None
                reason_str = f": {reason}" if reason else ""
                self._out.write(f"    [DEGRADED] {key}{reason_str}")
        unavailable_keys = [
            key
            for key in ctx.cfg.mcp.mcp_servers
            if registry is not None
            and registry.get_state(key) == McpServerHealthState.UNAVAILABLE
        ]
        if unavailable_keys:
            self._out.write("")
            self._out.write("  Unavailable servers:")
            for key in unavailable_keys:
                reason = registry.get_degraded_reason(key) if registry else None
                reason_str = f": {reason}" if reason else ""
                self._out.write(f"    [UNAVAILABLE] {key}{reason_str}")
        from agent.tool_runner import get_serialization_stats

        stats = get_serialization_stats()
        if stats["total_events"] > 0:
            ctx = self._ctx
            events = ctx.stats.stat_serialization_events
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

    async def _cmd_mcp(self, args: str = "") -> None:
        """MCP server status probe."""
        parts = args.strip().split(None, 1)
        sub = parts[0] if parts else ""
        if sub in ("status", ""):
            if not sub:
                self._out.write("Usage: /mcp [status]")
                self._out.write("")
            await self._cmd_mcp_status()
        else:
            raise UnknownSubcommandError(sub, ("status",))
