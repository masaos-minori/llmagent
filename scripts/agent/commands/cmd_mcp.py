#!/usr/bin/env python3
"""agent/commands/cmd_mcp.py
MCP server management mixin for CommandRegistry.

Thin dispatcher that delegates to:
  McpStatusService  (agent/services/mcp_status.py)  — /mcp status table
  McpInstallService (agent/services/mcp_install.py) — /mcp install wizard
"""

import logging

from agent.commands.mixin_base import MixinBase
from agent.services.mcp_install import CliInstallQA, McpInstallService
from agent.services.mcp_status import McpStatusService

logger = logging.getLogger(__name__)


class _McpMixin(MixinBase):
    """MCP server management slash-command handlers."""

    async def _cmd_mcp_status(self) -> None:
        """Print MCP server status table."""
        ctx = self._ctx
        svc = McpStatusService(ctx)
        print(
            f"  Tools       {len(ctx.cfg.tool.tool_definitions)} (from config/agent.toml)"
        )
        print()
        rows = await svc.probe_all()
        print(svc.format_table(rows))

    async def _cmd_mcp_install(self, server_name: str) -> None:
        """Interactive wizard: generate MCP server template files for server_name."""
        from mcp.installer import (
            validate_server_name,  # noqa: PLC0415 — lazy: heavy installer module deferred to /mcp install
        )

        err = validate_server_name(server_name)
        if err:
            print(err)
            print("Usage: /mcp install <server-name>  (e.g., my-api)")
            return

        print(f"MCP install wizard — server: {server_name!r}")
        print()

        svc = McpInstallService()
        qa = CliInstallQA()
        try:
            result = await svc.run(server_name, qa)
        except (FileExistsError, ValueError) as e:
            print(f"Aborted: {e}")
            return
        except OSError as e:
            print(f"File write error: {e}")
            return

        for path in result.created_files:
            print(f"  Created: {path}")

        svc.print_next_steps(result)

    async def _cmd_mcp(self, args: str = "") -> None:
        """MCP server status, tool list, connectivity check, or install wizard."""
        parts = args.strip().split(None, 1)
        sub = parts[0] if parts else ""
        if sub == "install":
            name = parts[1].strip() if len(parts) > 1 else ""
            await self._cmd_mcp_install(name)
        else:
            await self._cmd_mcp_status()
