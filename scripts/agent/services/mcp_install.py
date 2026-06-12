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

_VALID_ROLES: frozenset[str] = frozenset({"generic", "sqlite", "shell", "git", "ci"})


@dataclass(frozen=True)
class McpInstallParams:
    """Validated parameters collected from the install wizard."""

    server_name: str
    port: int
    role: str
    with_confd: bool


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
            if self._role not in _VALID_ROLES:
                raise ValueError(
                    f"Unknown role: {self._role!r}. Valid: {sorted(_VALID_ROLES)}"
                )
            return self._role
        raw = (
            (
                await asyncio.to_thread(
                    input, "Role [generic|sqlite|shell|git|ci] (default: generic): "
                )
            )
            .strip()
            .lower()
        )
        if not raw:
            return "generic"
        if raw not in _VALID_ROLES:
            raise ValueError(f"Unknown role: {raw!r}. Valid: {sorted(_VALID_ROLES)}")
        return raw

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

    async def collect_params(self, server_name: str, qa: InstallQA) -> McpInstallParams:
        """Collect and validate install parameters from InstallQA; return frozen DTO."""
        from mcp.installer_port import (
            suggest_port,  # noqa: PLC0415 — lazy: heavy installer module deferred to /mcp install
        )

        port_default = suggest_port()
        port = await qa.ask_port(port_default)
        role = await qa.ask_role()
        if role not in _VALID_ROLES:
            raise ValueError(
                f"Invalid role {role!r}. Valid: {', '.join(sorted(_VALID_ROLES))}"
            )
        with_confd = await qa.ask_confd()
        return McpInstallParams(
            server_name=server_name,
            port=port,
            role=role,
            with_confd=with_confd,
        )

    async def run(self, params: McpInstallParams) -> ScaffoldResult:
        """Create scaffold files from validated McpInstallParams; return ScaffoldResult."""
        from mcp.installer_templates import (
            generate_agent_toml_mcp_snippet,  # noqa: PLC0415 — lazy: heavy installer module deferred to /mcp install
            tool_definition_snippet,  # noqa: PLC0415 — lazy: heavy installer module deferred to /mcp install
        )
        from mcp.installer_validation import (
            name_to_module,  # noqa: PLC0415 — lazy: heavy installer module deferred to /mcp install
        )
        from mcp.installer_writer import (
            install_mcp_server,  # noqa: PLC0415 — lazy: heavy installer module deferred to /mcp install
        )

        module = name_to_module(params.server_name)
        created = install_mcp_server(
            params.server_name,
            params.port,
            with_confd=params.with_confd,
            role=params.role,
        )
        return ScaffoldResult(
            server_name=params.server_name,
            module=module,
            port=params.port,
            with_confd=params.with_confd,
            created_files=[str(p) for p in created],
            tool_snippet=tool_definition_snippet(module, params.server_name),
            agent_toml_snippet=generate_agent_toml_mcp_snippet(
                params.server_name, params.port, params.role
            ),
        )

    def format_next_steps(self, result: ScaffoldResult) -> str:
        """Format post-install checklist as a string (no I/O side effects)."""
        lines: list[str] = [
            "",
            "Next steps:",
            f"  1. Edit scripts/mcp/{result.module}/server.py — implement _DISPATCH handlers",
            "",
            "  2. Add tool definition to config/agent.toml (tool_definitions array):",
        ]
        for line in result.tool_snippet.splitlines():
            lines.append(f"     {line}")
        lines += [
            "",
            "  3. Add to config/agent.toml [mcp_servers]:",
        ]
        for line in (result.agent_toml_snippet or "").splitlines():
            lines.append(f"     {line}")
        lines += [
            "",
            "  4. Add to deploy/deploy.sh:",
            f'     cp -r "${{REPO_ROOT}}/scripts/mcp/{result.module}"'
            f' "${{DEPLOY_SCRIPTS}}/mcp/"',
            f'     cp "${{REPO_ROOT}}/config/{result.module}_mcp_server.toml"'
            f' "${{DEPLOY_CONFIG}}/"',
            "",
            "  5. Add to deploy/setup_services.sh (service list and conf.d copy):",
            f"     {result.server_name}  (add to the for-loop service list)",
        ]
        if result.with_confd:
            lines.append(
                f'     cp "${{REPO_ROOT}}/conf.d/{result.server_name}"'
                f' "/etc/conf.d/{result.server_name}"'
            )
        lines += [
            "",
            "  6. Deploy and start:",
            "     bash deploy/deploy.sh",
            f"     cp init.d/{result.server_name} /etc/init.d/{result.server_name}",
            f"     chmod +x /etc/init.d/{result.server_name}",
            f"     rc-update add {result.server_name} default",
            f"     rc-service {result.server_name} start",
        ]
        return "\n".join(lines)
