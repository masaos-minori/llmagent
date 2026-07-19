"""tests/test_github_tool_registry.py
Consistency tests for GitHub MCP tools — ensures TOOL_LIST stays in sync
with ToolRegistry and discovery metadata.
"""

from __future__ import annotations


class TestGitHubToolListConsistency:
    """Verify TOOL_LIST and ToolRegistry cannot drift silently."""

    def test_tool_list_has_21_tools(self) -> None:
        """TOOL_LIST has exactly 21 GitHub tools."""
        from mcp_servers.github.github_tools import TOOL_LIST

        assert len(TOOL_LIST) == 21, (
            f"Expected 21 tools in TOOL_LIST, got {len(TOOL_LIST)}"
        )

    def test_tool_list_names_match_registry(self) -> None:
        """Every TOOL_LIST tool name is registered in ToolRegistry."""
        from mcp_servers.github.github_tools import TOOL_LIST
        from shared.tool_registry import get_registry

        registry = get_registry()
        for tool in TOOL_LIST:
            tool_name = tool["name"]
            assert registry.get_server_for_tool(tool_name) == "github", (
                f"Tool {tool_name!r} in TOOL_LIST is not registered in ToolRegistry"
            )

    def test_tool_list_all_map_to_github_server_key(self) -> None:
        """Every GitHub tool maps to server_key='github'."""
        from mcp_servers.github.github_tools import TOOL_LIST
        from shared.tool_registry import get_registry

        registry = get_registry()
        for tool in TOOL_LIST:
            tool_name = tool["name"]
            key = registry.get_server_for_tool(tool_name)
            assert key == "github", f"Expected {tool_name!r} -> 'github', got {key!r}"

    def test_github_tools_match_tool_list_names(self) -> None:
        """ToolRegistry GitHub tools match TOOL_LIST names exactly."""
        from mcp_servers.github.github_tools import TOOL_LIST
        from shared.tool_registry import get_registry

        registry = get_registry()
        tool_list_names = {tool["name"] for tool in TOOL_LIST}
        registry_github_tools = registry.get_tool_names("github")

        assert tool_list_names == set(registry_github_tools), (
            f"TOOL_LIST names and ToolRegistry GitHub tools differ:\n"
            f"  TOOL_LIST only:  {tool_list_names - set(registry_github_tools)}\n"
            f"  Registry only:   {set(registry_github_tools) - tool_list_names}"
        )

    def test_tool_list_schema_has_name_field(self) -> None:
        """Every TOOL_LIST entry has a 'name' field."""
        from mcp_servers.github.github_tools import TOOL_LIST

        for tool in TOOL_LIST:
            assert "name" in tool, f"TOOL_LIST entry missing 'name': {tool}"

    def test_tool_list_no_duplicated_names(self) -> None:
        """TOOL_LIST has no duplicate tool names."""
        from mcp_servers.github.github_tools import TOOL_LIST

        names = [tool["name"] for tool in TOOL_LIST]
        assert len(names) == len(set(names)), (
            f"Duplicate names in TOOL_LIST: {[n for n in names if names.count(n) > 1]}"
        )
