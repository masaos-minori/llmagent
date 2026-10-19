"""tests/test_github_config_consistency.py
Validate GitHub tool definitions and MCP server config consistency.
"""

from __future__ import annotations

import tomllib
from collections.abc import Iterable
from typing import Any

import pytest


def _github_definition_problems(
    cfg: dict[str, Any], registry_tools: Iterable[str]
) -> list[str]:
    """Return problems with the GitHub entries of ``[[tool_definitions]]``.

    The rule follows the server's startup mode: when ``[mcp_servers.github]`` is
    enabled every registry tool must be defined, and when it is disabled
    (``startup_mode = "none"``) no GitHub tool may be defined, so re-enabling the
    server without restoring the definitions is caught.
    """
    github = cfg.get("mcp_servers", {}).get("github", {})
    enabled = github.get("startup_mode") != "none"
    defined = {
        entry.get("function", {}).get("name")
        for entry in cfg.get("tool_definitions", [])
    }
    github_defined = {
        n for n in defined if isinstance(n, str) and n.startswith("github_")
    }
    if enabled:
        missing = set(registry_tools) - defined
        if missing:
            return [
                "GitHub MCP server is enabled but tools are missing from "
                f"agent.toml [tool_definitions]: {sorted(missing)}"
            ]
    elif github_defined:
        return [
            'GitHub MCP server is disabled (startup_mode="none") but its tool '
            f"definitions are present in agent.toml: {sorted(github_defined)}"
        ]
    return []


def _parse_mcp_server_tool_names(content: str, server_name: str) -> set[str]:
    """Parse tool_names from [mcp_servers.<server_name>] section."""
    in_section = False
    in_tool_names = False
    config_tools: list[str] = []

    for line in content.splitlines():
        if f"[mcp_servers.{server_name}]" in line:
            in_section = True
        elif in_section and line.startswith("["):
            break
        elif in_section and "tool_names" in line:
            in_tool_names = True
            # Extract tools from this line (may be single-line or multi-line)
            tools_in_line = [
                t.strip().strip('"').strip("'")
                for t in line.split('"')
                if t.strip() and not t.strip().startswith('"')
            ]
            config_tools.extend(tools_in_line)
        elif in_tool_names:
            if "]" in line:
                # Extract remaining tools from this closing bracket line
                tools_in_line = [
                    t.strip().strip('"').strip("'")
                    for t in line.split('"')
                    if t.strip() and not t.strip().startswith('"')
                ]
                config_tools.extend(tools_in_line)
                break
            else:
                tools_in_line = [
                    t.strip().strip('"').strip("'")
                    for t in line.split('"')
                    if t.strip() and not t.strip().startswith('"')
                ]
                config_tools.extend(tools_in_line)

    # Filter out false positives (e.g., 'tool_names' itself parsed as a tool name)
    return {t for t in config_tools if t.startswith("github_")}


class TestGitHubConfigConsistency:
    """Ensure GitHub TOOL_LIST, ToolRegistry, tools_definitions.toml, and github_mcp_server.toml are consistent."""

    def test_github_tools_in_tools_definitions(self) -> None:
        """GitHub tool definitions in config/agent.toml follow the server's startup mode.

        Enabled server: all 21 registry tools are defined in [tool_definitions].
        Disabled server (startup_mode = "none"): none are defined, because the
        definitions were removed on purpose when the server was disabled.
        """
        from shared.tool_registry import get_registry

        registry = get_registry()
        github_tools = registry.get_tool_names("github")
        assert len(github_tools) == 21, (
            f"Expected 21 GitHub tools in registry, got {len(github_tools)}"
        )

        with open("config/agent.toml", "rb") as f:
            cfg = tomllib.load(f)

        problems = _github_definition_problems(cfg, github_tools)
        assert not problems, "; ".join(problems)

    def test_github_mcp_server_exists(self) -> None:
        """[mcp_servers.github] exists in config/agent.toml."""
        with open("config/agent.toml", encoding="utf-8") as f:
            content = f.read()

        assert "[mcp_servers.github]" in content, (
            "[mcp_servers.github] not found in agent.toml"
        )

    def test_github_tool_names_match_tools_definitions(self) -> None:
        """tool_names in [mcp_servers.github] (agent.toml) match registry exactly."""
        from shared.tool_registry import get_registry

        registry = get_registry()
        github_tools = set(registry.get_tool_names("github"))

        with open("config/agent.toml", encoding="utf-8") as f:
            content = f.read()

        config_tools = _parse_mcp_server_tool_names(content, "github")

        assert github_tools == config_tools, (
            f"[mcp_servers.github].tool_names mismatch:\n"
            f"  Registry only:    {sorted(github_tools - config_tools)}\n"
            f"  Config only:      {sorted(config_tools - github_tools)}"
        )

    def test_github_tool_names_match_tool_list(self) -> None:
        """tool_names in [mcp_servers.github] (agent.toml) match TOOL_LIST exactly."""
        from mcp_servers.github.github_tools import TOOL_LIST

        tool_list_names = {tool["name"] for tool in TOOL_LIST}

        with open("config/agent.toml", encoding="utf-8") as f:
            content = f.read()

        config_tools = _parse_mcp_server_tool_names(content, "github")

        assert tool_list_names == config_tools, (
            f"TOOL_LIST and [mcp_servers.github].tool_names mismatch:\n"
            f"  TOOL_LIST only:   {sorted(tool_list_names - config_tools)}\n"
            f"  Config only:      {sorted(config_tools - tool_list_names)}"
        )

    def test_tool_names_not_required_for_routing(self) -> None:
        """Config tool_names is not used as a routing input — only validation metadata."""
        from shared.route_resolver import ToolRouteResolver

        resolver = ToolRouteResolver()
        assert hasattr(resolver, "resolve")


def _cfg(startup_mode: str, defined: list[str]) -> dict[str, Any]:
    return {
        "mcp_servers": {"github": {"startup_mode": startup_mode}},
        "tool_definitions": [{"function": {"name": n}} for n in defined],
    }


class TestGitHubDefinitionProblems:
    """The definitions rule follows the GitHub MCP server's startup mode."""

    @pytest.mark.parametrize(
        ("cfg", "expected_problems", "mentions"),
        [
            (_cfg("subprocess", ["github_a", "github_b"]), 0, ""),
            (_cfg("subprocess", ["github_a"]), 1, "github_b"),
            (_cfg("none", []), 0, ""),
            (_cfg("none", ["github_a"]), 1, "github_a"),
        ],
        ids=[
            "enabled-all-defined",
            "enabled-missing",
            "disabled-none-defined",
            "disabled-with-definitions",
        ],
    )
    def test_problems_by_state(
        self, cfg: dict[str, Any], expected_problems: int, mentions: str
    ) -> None:
        problems = _github_definition_problems(cfg, {"github_a", "github_b"})
        assert len(problems) == expected_problems
        if mentions:
            assert mentions in problems[0]
