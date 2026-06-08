"""agent/services/mcp_install.py
McpInstallService — scaffold new MCP server template files.

Extracted from cmd_mcp._McpMixin so install logic is testable
without an interactive REPL session. Uses InstallQA Protocol to
decouple I/O from business logic.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Protocol


@dataclass
class ScaffoldResult:
    server_name: str
    module: str
    port: int
    with_confd: bool
    created_files: list[str]
    tool_snippet: str
    agent_toml_snippet: str


class InstallQA(Protocol):
    """I/O abstraction for the /mcp install wizard."""

    async def ask_port(self, default: int) -> int: ...
    async def ask_role(self) -> str: ...
    async def ask_confd(self) -> bool: ...


class CliInstallQA:
    """Interactive CLI implementation of InstallQA.

    Fields pre-supplied via constructor are returned as-is; None values
    trigger an input() prompt so the wizard can also be driven by flags.
    """

    def __init__(
        self,
        port: int | None = None,
        role: str | None = None,
        with_confd: bool | None = None,
    ) -> None:
        self._port = port
        self._role = role
        self._with_confd = with_confd

    async def ask_port(self, default: int) -> int:
        if self._port is not None:
            return self._port
        raw = (await asyncio.to_thread(input, f"Port [{default}]: ")).strip()
        try:
            port = int(raw) if raw else default
            if not 1024 <= port <= 65535:
                raise ValueError
            return port
        except ValueError:
            raise ValueError("Invalid port number.")

    async def ask_role(self) -> str:
        if self._role is not None:
            return self._role
        print("Role [generic | sqlite | shell | git | ci] (default: generic):")
        raw = (await asyncio.to_thread(input, "Role: ")).strip().lower()
        return raw if raw in ("sqlite", "shell", "git", "ci") else "generic"

    async def ask_confd(self) -> bool:
        if self._with_confd is not None:
            return self._with_confd
        raw = (
            (
                await asyncio.to_thread(
                    input, "Generate conf.d API key template? [y/N]: "
                )
            )
            .strip()
            .lower()
        )
        return raw in ("y", "yes")


class McpInstallService:
    """Generate MCP server scaffold files from wizard answers."""

    async def run(self, server_name: str, qa: InstallQA) -> ScaffoldResult:
        """Prompt the user via qa, create files, and return a ScaffoldResult."""
        from mcp.installer import (  # noqa: PLC0415 — lazy: heavy installer module deferred to /mcp install
            generate_agent_toml_mcp_snippet,
            install_mcp_server,
            name_to_module,
            suggest_port,
            tool_definition_snippet,
        )

        module = name_to_module(server_name)
        port_default = suggest_port()
        port = await qa.ask_port(port_default)
        role = await qa.ask_role()
        with_confd = await qa.ask_confd()

        created = install_mcp_server(
            server_name, port, with_confd=with_confd, role=role
        )
        return ScaffoldResult(
            server_name=server_name,
            module=module,
            port=port,
            with_confd=with_confd,
            created_files=[str(p) for p in created],
            tool_snippet=tool_definition_snippet(module, server_name),
            agent_toml_snippet=generate_agent_toml_mcp_snippet(server_name, port, role),
        )

    def print_next_steps(self, result: ScaffoldResult) -> None:
        """Print manual post-install checklist."""
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
