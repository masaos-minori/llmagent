"""tests/mcp_servers/cicd/test_cicd_server_endpoints.py

Characterization tests for scripts/mcp_servers/cicd/cicd_server.py's FastAPI wiring:
  - GET  /v1/tools
  - POST /v1/call_tool (success and unknown-tool paths, with audit logging,
    including the audit record's session_id/request_id field order)
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

import json
import os
import pathlib
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import mcp_servers.dispatch as dispatch
import pytest
from fastapi.testclient import TestClient
from mcp_servers.cicd import cicd_server
from mcp_servers.cicd.cicd_models import CicdConfig

from tests.mcp_servers._auth_headers import MCP_TEST_AUTH_HEADERS

# The REQ-004 metric fields the health `details.dedup` block publishes (mcpdl005).
# A per-metric status block appears only when that metric's threshold key is configured.
DEDUP_FIELDS = {
    "schema_version",
    "db_path",
    "generated_epoch",
    "row_states",
    "pending_overdue",
    "growth_rows_per_hour",
    "wal_size_bytes",
    "legal_hold_states",
    "held_past_retention",
    "lock_wait_ms",
}


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
    return TestClient(cicd_server.app, headers=MCP_TEST_AUTH_HEADERS)


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
            headers={"x-idempotency-key": str(uuid.uuid4())},
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
        isolated_dedup,
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
            headers={
                "x-session-id": "sess-1",
                "x-request-id": "req-1",
                "x-idempotency-key": "cicd-test-1",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body == {"result": "run triggered", "is_error": False, "dedup_state": ""}
        handler.assert_awaited_once_with({"repo": "acme/widgets", "workflow": "ci.yml"})

    def test_audit_record_keeps_session_and_request_context_in_order(
        self,
        client: TestClient,
        fake_service: _FakeService,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The record's `session_id` / `request_id` must match the order documented by
        `extract_request_context` (session_id, request_id, idempotency_key).

        The agent-side `tool_exec` record correlates to this record through
        `mcp_request_id`, so swapping the two fields breaks correlation. `session_id`
        comes from the x-session-id header; `request_id` is generated by the auth
        middleware and echoed in the X-Request-Id response header, because
        `request.state` wins over the header fallback in `extract_request_context`.
        Only the JSON audit payload is parsed: this endpoint also emits a key=value
        `call_tool` line through the same logger.
        """
        monkeypatch.setattr(
            cicd_server,
            "_cfg",
            CicdConfig(repo_allowlist=["acme/widgets"], workflow_allowlist=["ci.yml"]),
        )
        logger = MagicMock()
        monkeypatch.setattr(cicd_server, "logger", logger)
        fake_service._dispatch_table["trigger_workflow"] = AsyncMock(
            return_value="run triggered"
        )
        resp = client.post(
            "/v1/call_tool",
            json={
                "name": "trigger_workflow",
                "args": {"repo": "acme/widgets", "workflow": "ci.yml"},
            },
            headers={
                "x-session-id": "sess-ctx",
                "x-request-id": "req-ctx",
                "x-idempotency-key": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 200
        records = [
            json.loads(call.args[0])
            for call in logger.info.call_args_list
            if call.args[0].startswith("{")
        ]
        assert len(records) == 1
        assert records[0]["session_id"] == "sess-ctx"
        assert records[0]["request_id"] == resp.headers["x-request-id"]

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
    def test_healthy_when_github_token_set(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The no-store case: with no store wired the details dict is what it was before this row.
        monkeypatch.setattr(dispatch, "_dedup_store", None)
        monkeypatch.setattr(dispatch, "_dedup_config", None)
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

    def test_health_details_publish_the_dedup_block_when_a_store_is_wired(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
        isolated_dedup: pathlib.Path,
    ) -> None:
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token")
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()

        # The `service` key stays as it is; `dedup` is the single new key (REQ-004).
        assert body["details"]["service"] == "cicd-mcp"
        assert set(body["details"]) == {"service", "dedup"}
        block = body["details"]["dedup"]
        assert set(block) == DEDUP_FIELDS
        assert block["db_path"] == str(isolated_dedup)


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
