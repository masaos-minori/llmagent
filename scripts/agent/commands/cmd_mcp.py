#!/usr/bin/env python3
"""agent/commands/cmd_mcp.py
MCP server management mixin for CommandRegistry.

Thin dispatcher that delegates to:
  McpStatusService  (agent/services/mcp_status.py)  — /mcp status probe
  McpInstallService (agent/services/mcp_install.py) — /mcp install wizard

Formatting (table, next-steps) is handled in this module — not in the services.
"""

import logging

from agent.commands.exceptions import UnknownSubcommandError
from agent.commands.mixin_base import MixinBase
from agent.services.enums import McpAvailability
from agent.services.mcp_install import CliInstallQA, McpInstallService
from agent.services.mcp_status import TIER_LABELS, McpStatusService
from agent.services.models import McpProbeResult

logger = logging.getLogger(__name__)


def _format_mcp_table(rows: list[McpProbeResult]) -> str:
    """Format MCP server status rows as a fixed-width table string."""
    col = "{:<14} {:<6} {:<11} {:<5} {:<12} {:<12} {:<16} {}"
    lines = [
        col.format(
            "SERVER", "TRANS", "MODE", "AUTH", "WRITE", "ROLE", "STATUS", "ENDPOINT/CMD"
        ),
        "-" * 99,
    ]
    for r in rows:
        role_display = (
            f"{r.role} [sb:{r.sandbox_backend}]".strip()
            if r.sandbox_backend
            else r.role
        )
        lines.append(
            col.format(
                r.key,
                r.transport,
                r.startup_mode,
                "yes" if r.auth else "no",
                TIER_LABELS.get(r.tier, r.tier.value),
                role_display,
                f"{r.availability.value}/{r.health}",
                r.endpoint,
            )
        )
    return "\n".join(lines)


class _McpMixin(MixinBase):
    """MCP server management slash-command handlers."""

    async def _cmd_mcp_status(self) -> None:
        """Print MCP server status table."""
        ctx = self._ctx
        svc = McpStatusService(ctx)
        self._out.write(
            f"  Tools       {len(ctx.cfg.tool.tool_definitions)} (from config/agent.toml)"
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
            f"\n  Servers     {len(rows)} configured"
            f" ({ok_count} ok, {unreachable_count} unreachable)"
        )
        wd_interval = ctx.cfg.mcp.mcp_watchdog_interval
        wd_max = ctx.cfg.mcp.mcp_watchdog_max_restarts
        if wd_interval > 0:
            wd_status = f"enabled (interval={wd_interval:.0f}s, max_restarts={wd_max})"
        else:
            wd_status = "disabled (interval=0) — no auto-restart"
        self._out.write(f"  Watchdog    {wd_status}")
        serial_events = getattr(ctx.services, "serialization_events", 0)
        serial_affected = getattr(ctx.services, "serialization_tools_affected", 0)
        self._out.write("")
        self._out.write("--- Tool Scheduling ---")
        self._out.write(f"  Serialization events this session: {serial_events}")
        self._out.write(f"  Tools affected by serialization:   {serial_affected}")

    async def _cmd_mcp_install(self, server_name: str) -> None:
        """Interactive wizard: generate MCP server template files for server_name."""
        from mcp.installer_validation import (
            validate_server_name,  # noqa: PLC0415 — lazy: heavy installer module deferred to /mcp install
        )

        try:
            validate_server_name(server_name)
        except ValueError as e:
            self._out.write(str(e))
            self._out.write("Usage: /mcp install <server-name>  (e.g., my-api)")
            return

        self._out.write(f"MCP install wizard — server: {server_name!r}")
        self._out.write("")

        svc = McpInstallService()
        qa = CliInstallQA()
        try:
            params = await svc.collect_params(server_name, qa)
            result = await svc.run(params)
        except (FileExistsError, ValueError) as e:
            self._out.write(f"Aborted: {e}")
            return
        except OSError as e:
            self._out.write(f"File write error: {e}")
            return

        for path in result.created_files:
            self._out.write(f"  Created: {path}")

        self._out.write(svc.format_next_steps(result))

    async def _cmd_mcp(self, args: str = "") -> None:
        """MCP server status, tool list, connectivity check, or install wizard."""
        parts = args.strip().split(None, 1)
        sub = parts[0] if parts else ""
        if sub == "install":
            name = parts[1].strip() if len(parts) > 1 else ""
            await self._cmd_mcp_install(name)
        elif sub in ("status", ""):
            if not sub:
                self._out.write("Usage: /mcp [status|install <name>]")
                self._out.write("")
            await self._cmd_mcp_status()
        else:
            raise UnknownSubcommandError(sub, ("status", "install"))
