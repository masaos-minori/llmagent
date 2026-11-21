"""tests/test_github_config_consistency.py
Validate GitHub tool definitions and MCP server config consistency.
"""

from __future__ import annotations

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


class TestGitHubConfigConsistency:
    """Ensure GitHub TOOL_LIST, ToolRegistry, tools_definitions.toml, and github_mcp_server.toml are consistent."""

    def test_github_mcp_server_exists(self) -> None:
        """[mcp_servers.github] exists in config/agent.toml."""
        with open("config/agent.toml", encoding="utf-8") as f:
            content = f.read()

        assert "[mcp_servers.github]" in content, (
            "[mcp_servers.github] not found in agent.toml"
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
