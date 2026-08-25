"""tests/mcp_servers/cicd/test_cicd_server_endpoints.py

Characterization tests for scripts/mcp_servers/cicd/cicd_server.py's FastAPI wiring:
  - GET  /v1/tools
  - POST /v1/call_tool (success and unknown-tool paths, with audit logging)
  - GET  /health (healthy path; the GITHUB_TOKEN-unset degraded path is already
    covered by tests/mcp_servers/cicd/test_mcp_server_health_status.py)
  - CiCdMCPServer.dispatch()

These tests lock the current, observed behavior of the thin FastAPI wiring layer
before refactoring (mirrors tests/mcp_servers/shell/test_shell_server_endpoints.py's
approach for shell_server.py). They monkeypatch the module-level `_service`
singleton so no real GitHub Actions/network access occurs. Business logic
(CiCdService, CicdConfig, GitHubActionsBackend) is already covered by
tests/mcp_servers/cicd/test_cicd_mcp_service.py and friends; this file exists
solely to close the coverage gap on cicd_server.py's own route/dispatch code.
"""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from mcp_servers.cicd import cicd_server
from mcp_servers.cicd.cicd_models import CicdConfig


class _FakeService:
    """Minimal stand-in for CiCdService, exposing only what cicd_server.py touches."""

    def __init__(self) -> None:
        self._dispatch_table: dict[str, Any] = {}

    def get_dispatch_table(self) -> dict[str, Any]:
        return self._dispatch_table


@pytest.fixture
def fake_service(monkeypatch: pytest.MonkeyPatch) -> _FakeService:
    svc = _FakeService()
    monkeypatch.setattr(cicd_server, "_service", svc)
    return svc


@pytest.fixture
def client() -> TestClient:
    return TestClient(cicd_server.app)


class TestToolsListEndpoint:
    def test_lists_cicd_tools_with_server_key(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            cicd_server,
            "_cfg",
            CicdConfig(repo_allowlist=["acme/widgets"], workflow_allowlist=["ci.yml"]),
        )
        resp = client.get("/v1/tools")
        assert resp.status_code == 200
        body = resp.json()
        assert "schema_version" in body
        names = {t["name"]: t for t in body["tools"]}
        assert "trigger_workflow" in names
        assert names["trigger_workflow"]["server_key"] == "cicd"

    def test_empty_repo_allowlist_disables_all_tools(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            cicd_server, "_cfg", CicdConfig(repo_allowlist=[], workflow_allowlist=[])
        )
        resp = client.get("/v1/tools?include_disabled=true")
        names = {t["name"]: t for t in resp.json()["tools"]}
        for name in (
            "trigger_workflow",
            "get_workflow_runs",
            "get_workflow_status",
            "get_workflow_logs",
        ):
            assert names[name]["enabled"] is False
            assert names[name]["disabled_reason"] == "repo_allowlist is empty"

    def test_empty_workflow_allowlist_disables_only_trigger(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            cicd_server,
            "_cfg",
            CicdConfig(repo_allowlist=["acme/widgets"], workflow_allowlist=[]),
        )
        resp = client.get("/v1/tools?include_disabled=true")
        names = {t["name"]: t for t in resp.json()["tools"]}
        assert names["trigger_workflow"]["enabled"] is False
        assert (
            names["trigger_workflow"]["disabled_reason"]
            == "workflow_allowlist is empty"
        )
        assert names["get_workflow_runs"]["enabled"] is True
        assert names["get_workflow_status"]["enabled"] is True
        assert names["get_workflow_logs"]["enabled"] is True

    def test_include_disabled_false_omits_disabled_tool(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            cicd_server, "_cfg", CicdConfig(repo_allowlist=[], workflow_allowlist=[])
        )
        resp = client.get("/v1/tools?include_disabled=false")
        assert resp.json()["tools"] == []


class TestCallToolDisabledGate:
    def test_disabled_tool_returns_error_without_dispatch(
        self,
        client: TestClient,
        fake_service: _FakeService,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            cicd_server, "_cfg", CicdConfig(repo_allowlist=[], workflow_allowlist=[])
        )
        handler = AsyncMock(return_value="run triggered")
        fake_service._dispatch_table["trigger_workflow"] = handler
        resp = client.post(
            "/v1/call_tool",
            json={"name": "trigger_workflow", "args": {"repo": "a/b"}},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["is_error"] is True
        assert "repo_allowlist is empty" in body["result"]
        handler.assert_not_awaited()


class TestCallToolEndpoint:
    def test_dispatches_known_tool_and_audit_logs(
        self,
        client: TestClient,
        fake_service: _FakeService,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            cicd_server,
            "_cfg",
            CicdConfig(repo_allowlist=["acme/widgets"], workflow_allowlist=["ci.yml"]),
        )
        handler = AsyncMock(return_value="run triggered")
        fake_service._dispatch_table["trigger_workflow"] = handler
        resp = client.post(
            "/v1/call_tool",
            json={
                "name": "trigger_workflow",
                "args": {"repo": "acme/widgets", "workflow": "ci.yml"},
            },
            headers={"x-session-id": "sess-1", "x-request-id": "req-1"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body == {"result": "run triggered", "is_error": False}
        handler.assert_awaited_once_with({"repo": "acme/widgets", "workflow": "ci.yml"})

    def test_unknown_tool_returns_error_result(
        self,
        client: TestClient,
        fake_service: _FakeService,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            cicd_server,
            "_cfg",
            CicdConfig(repo_allowlist=["acme/widgets"], workflow_allowlist=["ci.yml"]),
        )
        resp = client.post("/v1/call_tool", json={"name": "not_a_tool", "args": {}})
        assert resp.status_code == 200
        body = resp.json()
        assert body["is_error"] is True
        assert "Unknown tool" in body["result"]


class TestHealthEndpoint:
    def test_healthy_when_github_token_set(self, client: TestClient) -> None:
        original_token = os.environ.get("GITHUB_TOKEN")
        try:
            os.environ["GITHUB_TOKEN"] = "ghp_test_token"
            resp = client.get("/health")
            assert resp.status_code == 200
            body = resp.json()
            assert body["status"] == "ok"
            assert body["ready"] is True
            assert body["dependencies"] == {}
            assert body["details"] == {"service": "cicd-mcp"}
        finally:
            if original_token is not None:
                os.environ["GITHUB_TOKEN"] = original_token
            else:
                os.environ.pop("GITHUB_TOKEN", None)


class TestCiCdMCPServerDispatch:
    @pytest.mark.asyncio
    async def test_dispatch_routes_through_service_table(
        self, fake_service: _FakeService
    ) -> None:
        handler = AsyncMock(return_value="dispatched")
        fake_service._dispatch_table["get_workflow_runs"] = handler
        server = cicd_server.CiCdMCPServer()
        result = await server.dispatch("get_workflow_runs", {"repo": "acme/widgets"})
        assert result.output == "dispatched"
        assert result.is_error is False
