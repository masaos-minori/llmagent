#!/usr/bin/env python3
"""
agent/commands/cmd_mcp.py
MCP server management mixin for CommandRegistry.

Extracted from agent/commands/registry.py.  Provides _McpMixin with:
  _cmd_mcp_http              — /mcp status: transport config + connectivity probe
  _cmd_mcp                   — /mcp dispatcher
  _cmd_mcp_install           — /mcp install wizard: scaffold template files
  _print_mcp_install_next_steps — print post-install checklist
"""

import logging
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)


class _McpMixin:
    """MCP server management slash-command handlers."""

    if TYPE_CHECKING:
        _ctx: "AgentContext"

    async def _cmd_mcp_http(self) -> None:
        """Print MCP server transport config and probe connectivity per server."""
        ctx = self._ctx
        print(f"  Tools       {len(ctx.cfg.tool_definitions)} (from config/agent.toml)")
        print("Servers:")
        for key, cfg in ctx.cfg.mcp_servers.items():
            if cfg.transport == "http":
                print(f"  {key:12s} http  {cfg.url}")
            else:
                alive = (
                    "alive"
                    if ctx.services.stdio_procs.get(key, None)
                    and ctx.services.stdio_procs[key].is_alive()
                    else "dead"
                )
                cmd_str = " ".join(cfg.cmd)
                print(f"  {key:12s} stdio [{alive}] {cmd_str}")
        print("Connectivity:")
        async with httpx.AsyncClient(timeout=5.0) as probe:
            for key, cfg in ctx.cfg.mcp_servers.items():
                if cfg.transport == "http" and cfg.url:
                    try:
                        r = await probe.get(f"{cfg.url}/health")
                        status = (
                            "OK" if r.status_code == 200 else f"HTTP {r.status_code}"
                        )
                    except Exception as e:
                        status = f"FAIL ({e})"
                    print(f"  {key:12s} {status}")
                elif cfg.transport == "stdio":
                    transport = ctx.services.stdio_procs.get(key)
                    status = "alive" if transport and transport.is_alive() else "dead"
                    print(f"  {key:12s} {status}")

    async def _cmd_mcp(self, args: str = "") -> None:
        """MCP server status, tool list, connectivity check, or install wizard."""
        parts = args.strip().split(None, 1)
        sub = parts[0] if parts else ""
        if sub == "install":
            name = parts[1].strip() if len(parts) > 1 else ""
            await self._cmd_mcp_install(name)
        else:
            await self._cmd_mcp_http()

    async def _cmd_mcp_install(self, server_name: str) -> None:
        """Interactive wizard: generate MCP server template files for server_name."""
        from mcp.installer import (  # noqa: PLC0415
            install_mcp_server,
            name_to_module,
            suggest_port,
            tool_definition_snippet,
            validate_server_name,
        )

        err = validate_server_name(server_name)
        if err:
            print(err)
            print("Usage: /mcp install <server-name>  (e.g., my-api)")
            return

        module = name_to_module(server_name)
        port_default = suggest_port()

        print(f"MCP install wizard — server: {server_name!r}  module: {module}")
        print()

        raw_port = input(f"Port [{port_default}]: ").strip()
        try:
            port = int(raw_port) if raw_port else port_default
            if not 1024 <= port <= 65535:
                raise ValueError
        except ValueError:
            print("Invalid port number. Aborting.")
            return

        raw_confd = input("Generate conf.d API key template? [y/N]: ").strip().lower()
        with_confd = raw_confd in ("y", "yes")

        print()
        print(f"Creating MCP server templates for {server_name!r}...")
        try:
            created = install_mcp_server(server_name, port, with_confd=with_confd)
        except (FileExistsError, ValueError) as e:
            print(f"Aborted: {e}")
            return
        except OSError as e:
            print(f"File write error: {e}")
            return

        for path in created:
            print(f"  Created: {path}")

        self._print_mcp_install_next_steps(
            server_name,
            module,
            port,
            with_confd,
            tool_definition_snippet(module, server_name),
        )

    def _print_mcp_install_next_steps(
        self,
        server_name: str,
        module: str,
        port: int,
        with_confd: bool,
        snippet: str,
    ) -> None:
        """Print manual post-install checklist."""
        print()
        print("Next steps:")
        print(
            f"  1. Edit scripts/mcp/{module}/server.py — implement _DISPATCH handlers"
        )
        print()
        print("  2. Add tool definition to config/agent.toml (tool_definitions array):")
        for line in snippet.splitlines():
            print(f"     {line}")
        print()
        print("  3. Add to agent/repl.py _MCP_SERVICE_MAP:")
        print(f'     "http://127.0.0.1:{port}": "{server_name}",')
        print()
        print("  4. Add to deploy/deploy.sh:")
        print(
            f'     cp -r "${{REPO_ROOT}}/scripts/mcp/{module}"'
            f' "${{DEPLOY_SCRIPTS}}/mcp/"'
        )
        print(
            f'     cp "${{REPO_ROOT}}/config/{module}_mcp_server.toml"'
            f' "${{DEPLOY_CONFIG}}/"'
        )
        print()
        print("  5. Add to deploy/setup_services.sh (service list and conf.d copy):")
        print(f"     {server_name}  (add to the for-loop service list)")
        if with_confd:
            print(
                f'     cp "${{REPO_ROOT}}/conf.d/{server_name}"'
                f' "/etc/conf.d/{server_name}"'
            )
        print()
        print("  6. Deploy and start:")
        print("     bash deploy/deploy.sh")
        print(f"     cp init.d/{server_name} /etc/init.d/{server_name}")
        print(f"     chmod +x /etc/init.d/{server_name}")
        print(f"     rc-update add {server_name} default")
        print(f"     rc-service {server_name} start")
