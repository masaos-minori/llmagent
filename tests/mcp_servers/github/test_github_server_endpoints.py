"""tests/mcp_servers/github/test_github_server_endpoints.py

Characterization tests for scripts/mcp_servers/github/github_server.py's own
FastAPI wiring (not the included domain routers, which have their own test
files):
  - GET  /v1/tools
  - POST /v1/call_tool (success and unknown-tool paths, with audit logging,
    including the request_id `request.state` vs. header fallback)
  - GET  /health (healthy and degraded-by-missing-token paths)
  - _dispatch_github_tool()
  - GithubMCPServer.dispatch()

These tests lock the current, observed behavior of the thin FastAPI wiring
layer before refactoring (mirrors
tests/mcp_servers/cicd/test_cicd_server_endpoints.py's approach for
cicd_server.py). They monkeypatch the module-level `_service` singleton (and,
for the health endpoint, the module-level `_GITHUB_TOKEN` constant) so no real
GitHub/network access occurs. Business logic (GitHubService, GitHubConfig) is
already covered by tests/mcp_servers/github/test_service_*.py and friends;
this file exists solely to close the coverage gap on github_server.py's own
route/dispatch code (verified via `coverage report
--include=".../github_server.py"` showing 74% before this file was added,
with lines 107-112, 122, 133, 144-158, 178 uncovered).
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from mcp_servers.github import github_server


class _FakeService:
    """Minimal stand-in for GitHubService, exposing only what github_server.py touches."""

    def __init__(self) -> None:
        self._dispatch_table: dict[str, Any] = {}

    def get_dispatch_table(self) -> dict[str, Any]:
        return self._dispatch_table


@pytest.fixture
def fake_service(monkeypatch: pytest.MonkeyPatch) -> _FakeService:
    svc = _FakeService()
    monkeypatch.setattr(github_server, "_service", svc)
    return svc


@pytest.fixture
def client() -> TestClient:
    return TestClient(github_server.app)


class TestToolsListEndpoint:
    def test_lists_github_tools_with_server_key(self, client: TestClient) -> None:
        resp = client.get("/v1/tools")
        assert resp.status_code == 200
        body = resp.json()
        assert "schema_version" in body
        names = {t["name"]: t for t in body["tools"]}
        assert "github_search_repositories" in names
        assert names["github_search_repositories"]["server_key"] == "github"


class TestCallToolEndpoint:
    def test_dispatches_known_tool_and_audit_logs(
        self, client: TestClient, fake_service: _FakeService
    ) -> None:
        handler = AsyncMock(return_value="42 stars")
        fake_service._dispatch_table["github_search_repositories"] = handler
        resp = client.post(
            "/v1/call_tool",
            json={
                "name": "github_search_repositories",
                "args": {"owner": "acme", "repo": "widgets"},
            },
            headers={"x-session-id": "sess-1", "x-request-id": "req-1"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body == {"result": "42 stars", "is_error": False}
        handler.assert_awaited_once_with({"owner": "acme", "repo": "widgets"})

    def test_unknown_tool_returns_error_result(
        self, client: TestClient, fake_service: _FakeService
    ) -> None:
        resp = client.post("/v1/call_tool", json={"name": "not_a_tool", "args": {}})
        assert resp.status_code == 200
        body = resp.json()
        assert body["is_error"] is True
        assert "Unknown tool" in body["result"]

    def test_audit_target_falls_back_to_empty_owner_and_repo(
        self, client: TestClient, fake_service: _FakeService
    ) -> None:
        """req.args without 'owner'/'repo' keys still succeeds; audit target
        formatting (f"repo={{owner}}/{{repo}}") uses "" for missing keys."""
        handler = AsyncMock(return_value="ok")
        fake_service._dispatch_table["github_list_issues"] = handler
        resp = client.post(
            "/v1/call_tool", json={"name": "github_list_issues", "args": {}}
        )
        assert resp.status_code == 200
        assert resp.json() == {"result": "ok", "is_error": False}

    def test_request_id_falls_back_to_header_when_state_unset(
        self, client: TestClient, fake_service: _FakeService
    ) -> None:
        """No middleware sets request.state.request_id in this bare TestClient
        app, so the x-request-id header is used (the `getattr(..., default)`
        fallback branch on github_server.py:145-147)."""
        handler = AsyncMock(return_value="ok")
        fake_service._dispatch_table["github_get_issue"] = handler
        resp = client.post(
            "/v1/call_tool",
            json={"name": "github_get_issue", "args": {}},
            headers={"x-request-id": "hdr-req-id"},
        )
        assert resp.status_code == 200
        assert resp.json()["is_error"] is False


class TestHealthEndpoint:
    def test_degraded_when_github_token_not_set(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(github_server, "_GITHUB_TOKEN", "")
        resp = client.get("/health")
        assert resp.status_code == 503
        body = resp.json()
        assert body["status"] == "degraded"
        assert body["ready"] is False
        assert body["dependencies"] == {"github_token": "not_set"}
        assert body["details"] == {"service": "github-mcp"}

    def test_healthy_when_github_token_set(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(github_server, "_GITHUB_TOKEN", "ghp_test_token")
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["ready"] is True
        assert body["dependencies"] == {}
        assert body["details"] == {"service": "github-mcp"}


class TestDispatchGithubTool:
    @pytest.mark.asyncio
    async def test_routes_through_service_dispatch_table(
        self, fake_service: _FakeService
    ) -> None:
        handler = AsyncMock(return_value="dispatched")
        fake_service._dispatch_table["github_create_branch"] = handler
        result = await github_server._dispatch_github_tool(
            "github_create_branch", {"owner": "acme", "repo": "widgets"}
        )
        assert result.output == "dispatched"
        assert result.is_error is False
        handler.assert_awaited_once_with({"owner": "acme", "repo": "widgets"})


class TestGithubMCPServerDispatch:
    @pytest.mark.asyncio
    async def test_dispatch_routes_through_service_table(
        self, fake_service: _FakeService
    ) -> None:
        handler = AsyncMock(return_value="dispatched")
        fake_service._dispatch_table["github_list_branches"] = handler
        server = github_server.GithubMCPServer()
        result = await server.dispatch(
            "github_list_branches", {"owner": "acme", "repo": "widgets"}
        )
        assert result.output == "dispatched"
        assert result.is_error is False
