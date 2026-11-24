"""tests/test_github_tool_registry.py
Consistency tests for GitHub MCP tools — ensures TOOL_LIST stays in sync
with ToolRegistry and discovery metadata.
"""

from __future__ import annotations

import pytest
from mcp_servers.github.github_models_file import (
    CreateOrUpdateFileRequest,
    DeleteRepoFileRequest,
    GetFileContentsRequest,
    PushFilesRequest,
)
from mcp_servers.github.github_models_issues import (
    AddIssueCommentRequest,
    CreateIssueRequest,
    GetIssueRequest,
    ListIssuesRequest,
    SearchIssuesRequest,
)
from mcp_servers.github.github_models_pull_requests import (
    CreatePullRequestRequest,
    GetPullRequestRequest,
    ListPullRequestsRequest,
    MergePullRequestRequest,
    SearchPullRequestsRequest,
    UpdatePullRequestRequest,
)
from mcp_servers.github.github_models_repository import (
    CreateBranchRequest,
    GetCommitRequest,
    ListBranchesRequest,
    ListCommitsRequest,
    SearchCodeRequest,
    SearchRepositoriesRequest,
)
from mcp_servers.models import McpTool
from mcp_servers.request_contract import build_input_schema
from pydantic import BaseModel

# Every published GitHub tool mapped to the request model its inputSchema must come
# from. The coverage test below fails if a tool is added, removed, or renamed without
# updating this map, so the gate cannot silently lag the registry.
_TOOL_MODEL_MAP: dict[str, type[BaseModel]] = {
    # issues
    "github_list_issues": ListIssuesRequest,
    "github_get_issue": GetIssueRequest,
    "github_create_issue": CreateIssueRequest,
    "github_search_issues": SearchIssuesRequest,
    "github_add_issue_comment": AddIssueCommentRequest,
    # pull requests
    "github_list_pull_requests": ListPullRequestsRequest,
    "github_get_pull_request": GetPullRequestRequest,
    "github_create_pull_request": CreatePullRequestRequest,
    "github_search_pull_requests": SearchPullRequestsRequest,
    "github_update_pull_request": UpdatePullRequestRequest,
    "github_merge_pull_request": MergePullRequestRequest,
    # repository
    "github_search_repositories": SearchRepositoriesRequest,
    "github_list_branches": ListBranchesRequest,
    "github_create_branch": CreateBranchRequest,
    "github_list_commits": ListCommitsRequest,
    "github_get_commit": GetCommitRequest,
    "github_search_code": SearchCodeRequest,
    # file
    "github_get_file_contents": GetFileContentsRequest,
    "github_create_or_update_file": CreateOrUpdateFileRequest,
    "github_push_files": PushFilesRequest,
    "github_delete_file": DeleteRepoFileRequest,
}


def _tool_by_name(tool_name: str) -> McpTool:
    """Look up one TOOL_LIST entry by name."""
    from mcp_servers.github.github_tools import TOOL_LIST

    return next(tool for tool in TOOL_LIST if tool["name"] == tool_name)


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


class TestGitHubModelSchemaConsistency:
    """REQ-009: a published GitHub inputSchema and its request model cannot drift."""

    def test_tool_model_map_covers_tool_list(self) -> None:
        """The model map covers exactly the tools in TOOL_LIST, no more and no less."""
        from mcp_servers.github.github_tools import TOOL_LIST

        tool_list_names = {tool["name"] for tool in TOOL_LIST}
        assert set(_TOOL_MODEL_MAP) == tool_list_names, (
            f"_TOOL_MODEL_MAP and TOOL_LIST differ:\n"
            f"  map only:    {set(_TOOL_MODEL_MAP) - tool_list_names}\n"
            f"  TOOL_LIST only: {tool_list_names - set(_TOOL_MODEL_MAP)}"
        )

    @pytest.mark.parametrize("tool_name", sorted(_TOOL_MODEL_MAP))
    def test_published_schema_equals_model_schema(self, tool_name: str) -> None:
        """The published schema is byte-for-byte what build_input_schema produces."""
        tool = _tool_by_name(tool_name)
        model = _TOOL_MODEL_MAP[tool_name]
        expected = build_input_schema(model)

        assert tool["inputSchema"] == expected, (
            f"{tool_name}: published inputSchema drifted from "
            f"build_input_schema({model.__name__}):\n"
            f"  published: {tool['inputSchema']}\n"
            f"  generated: {expected}"
        )

    def test_write_tools_publish_dry_run(self) -> None:
        """Every write tool publishes dry_run with a generated default of false."""
        from mcp_servers.github.github_tools import TOOL_LIST

        write_tools = [tool for tool in TOOL_LIST if tool["is_write"]]
        assert len(write_tools) == 9, (
            f"Expected 9 GitHub write tools, got {len(write_tools)}: "
            f"{sorted(t['name'] for t in write_tools)}"
        )
        for tool in write_tools:
            properties = tool["inputSchema"]["properties"]
            assert "dry_run" in properties, (
                f"{tool['name']}: write tool publishes no dry_run property"
            )
            dry_run = properties["dry_run"]
            assert dry_run["type"] == "boolean", (
                f"{tool['name']}: dry_run is not a boolean: {dry_run}"
            )
            assert dry_run["default"] is False, (
                f"{tool['name']}: dry_run does not default to false: {dry_run}"
            )

    def test_generated_schemas_are_deterministic(self) -> None:
        """Two generator calls agree, and no generated title noise reaches the payload."""
        for tool_name, model in _TOOL_MODEL_MAP.items():
            first = build_input_schema(model)
            second = build_input_schema(model)
            assert first == second, (
                f"{tool_name}: build_input_schema is not deterministic"
            )
            assert "title" not in first, f"{tool_name}: schema root carries a title key"
            assert "title" not in first.get("$defs", {}), (
                f"{tool_name}: a $defs entry carries a title key"
            )
        for tool_name in _TOOL_MODEL_MAP:
            published = _tool_by_name(tool_name)["inputSchema"]
            assert published == build_input_schema(_TOOL_MODEL_MAP[tool_name])
