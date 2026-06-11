#!/usr/bin/env python3
"""agent/commands/cmd_mcp.py
MCP server management mixin for CommandRegistry.

Thin dispatcher that delegates to:
  McpStatusService  (agent/services/mcp_status.py)  — /mcp status probe
  McpInstallService (agent/services/mcp_install.py) — /mcp install wizard

Formatting (table, next-steps) is handled in this module — not in the services.
"""

import logging

from agent.commands.mixin_base import MixinBase
from agent.services.mcp_install import CliInstallQA, McpInstallService, ScaffoldResult
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
        lines.append(
            col.format(
                r.key,
                r.transport,
                r.startup_mode,
                "yes" if r.auth else "no",
                TIER_LABELS.get(r.tier, r.tier.value),
                r.role,
                f"{r.availability.value}/{r.health}",
                r.endpoint,
            )
        )
    return "\n".join(lines)


def _print_mcp_install_next_steps(result: ScaffoldResult) -> None:
    """Print post-install checklist for the newly scaffolded MCP server."""
    print()
    print("Next steps:")
    print(
        f"  1. Edit scripts/mcp/{result.module}/server.py — implement _DISPATCH handlers",
    )
    print()
    print("  2. Add tool definition to config/agent.toml (tool_definitions array):")
    for line in result.tool_snippet.splitlines():
        print(f"     {line}")
    print()
    print("  3. Add to config/agent.toml [mcp_servers]:")
    for line in (result.agent_toml_snippet or "").splitlines():
        print(f"     {line}")
    print()
    print("  4. Add to deploy/deploy.sh:")
    print(
        f'     cp -r "${{REPO_ROOT}}/scripts/mcp/{result.module}"'
        f' "${{DEPLOY_SCRIPTS}}/mcp/"',
    )
    print(
        f'     cp "${{REPO_ROOT}}/config/{result.module}_mcp_server.toml"'
        f' "${{DEPLOY_CONFIG}}/"',
    )
    print()
    print("  5. Add to deploy/setup_services.sh (service list and conf.d copy):")
    print(f"     {result.server_name}  (add to the for-loop service list)")
    if result.with_confd:
        print(
            f'     cp "${{REPO_ROOT}}/conf.d/{result.server_name}"'
            f' "/etc/conf.d/{result.server_name}"',
        )
    print()
    print("  6. Deploy and start:")
    print("     bash deploy/deploy.sh")
    print(f"     cp init.d/{result.server_name} /etc/init.d/{result.server_name}")
    print(f"     chmod +x /etc/init.d/{result.server_name}")
    print(f"     rc-update add {result.server_name} default")
    print(f"     rc-service {result.server_name} start")


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
        print(_format_mcp_table(rows))

    async def _cmd_mcp_install(self, server_name: str) -> None:
        """Interactive wizard: generate MCP server template files for server_name."""
        from mcp.installer_validation import (
            validate_server_name,  # noqa: PLC0415 — lazy: heavy installer module deferred to /mcp install
        )

        try:
            validate_server_name(server_name)
        except ValueError as e:
            print(str(e))
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

        _print_mcp_install_next_steps(result)

    async def _cmd_mcp(self, args: str = "") -> None:
        """MCP server status, tool list, connectivity check, or install wizard."""
        parts = args.strip().split(None, 1)
        sub = parts[0] if parts else ""
        if sub == "install":
            name = parts[1].strip() if len(parts) > 1 else ""
            await self._cmd_mcp_install(name)
        elif sub in ("status", ""):
            if not sub:
                print("Usage: /mcp [status|install <name>]")
                print()
            await self._cmd_mcp_status()
        else:
            print(f"Unknown subcommand: {sub!r}. Usage: /mcp [status|install <name>]")
