"""tests/mcp_servers/github/test_github_tool_schema.py

Security-contract tests for schema publication at the GitHub MCP HTTP boundary
(`GET /v1/tools`): the `inputSchema` a client discovers is the generated strict
model schema, including the `dry_run` argument every write tool advertises.

Contract tests, not characterization tests: they read the wire payload through the
real FastAPI application, so a published schema that drifts from the model fails
here rather than only in an in-process equality gate. Consumes the shared
`http_boundary` fixture (mcpai010 REQ-003); the GitHub API client is not called
because no request reaches the business layer. Marker: `security_contract`
(REQ-004).
"""

from __future__ import annotations

from collections.abc import Callable
from types import ModuleType
from typing import Any

import pytest
from mcp_servers.github import github_server
from mcp_servers.github.github_models_file import (
    CreateOrUpdateFileRequest,
    DeleteRepoFileRequest,
    GetFileContentsRequest,
    PushFilesRequest,
)
from mcp_servers.request_contract import build_input_schema

from tests.mcp_servers.conftest import HttpBoundary

# The file tools asserted are the entries of scripts/mcp_servers/github/tools_file.py's
# TOOL_LIST; the mapping is the model each published schema must equal.
_FILE_TOOL_MODELS: dict[str, type[Any]] = {
    "github_get_file_contents": GetFileContentsRequest,
    "github_create_or_update_file": CreateOrUpdateFileRequest,
    "github_push_files": PushFilesRequest,
    "github_delete_file": DeleteRepoFileRequest,
}


def _published_tools(boundary: HttpBoundary) -> list[dict[str, Any]]:
    """The tool entries the boundary publishes.

    `include_disabled=true` is required: this test environment has no
    GITHUB_TOKEN set, so the default visibility filter would return an empty
    list and every assertion below would pass vacuously.
    """
    resp = boundary.client.get("/v1/tools?include_disabled=true")
    assert resp.status_code == 200
    body: dict[str, Any] = resp.json()
    return list(body["tools"])


@pytest.mark.security_contract
class TestPublishedToolSchemas:
    def test_file_tool_schemas_are_the_generated_model_schemas(
        self, http_boundary: Callable[[ModuleType], HttpBoundary]
    ) -> None:
        boundary = http_boundary(github_server)
        published = {tool["name"]: tool for tool in _published_tools(boundary)}
        for name, model in _FILE_TOOL_MODELS.items():
            assert name in published, sorted(published)
            assert published[name]["inputSchema"] == build_input_schema(model)

    def test_published_schemas_are_strict(
        self, http_boundary: Callable[[ModuleType], HttpBoundary]
    ) -> None:
        """The wire advertises the same posture `_validate_request` enforces."""
        boundary = http_boundary(github_server)
        tools = _published_tools(boundary)
        assert tools, "no tool published at the boundary"
        for tool in tools:
            assert tool["inputSchema"].get("additionalProperties") is False, tool[
                "name"
            ]

    def test_write_tools_publish_dry_run(
        self, http_boundary: Callable[[ModuleType], HttpBoundary]
    ) -> None:
        """Every `is_write` tool publishes `dry_run` as a boolean defaulting to false."""
        boundary = http_boundary(github_server)
        write_tools = [
            tool for tool in _published_tools(boundary) if tool.get("is_write")
        ]
        assert write_tools, "no write tool published at the boundary"
        for tool in write_tools:
            dry_run = tool["inputSchema"]["properties"].get("dry_run")
            assert dry_run is not None, tool["name"]
            assert dry_run["type"] == "boolean", tool["name"]
            assert dry_run.get("default") is False, tool["name"]
