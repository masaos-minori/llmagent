"""tests/mcp_servers/cicd/test_cicd_server_endpoints.py

Characterization tests for scripts/mcp_servers/cicd/cicd_server.py's FastAPI wiring:
  - GET  /v1/tools
  - POST /v1/call_tool (success and unknown-tool paths, with audit logging,
    including the audit record's session_id/request_id field order)
  - GET  /health (healthy path; the effective-credential and failed-probe degraded paths are
    covered by tests/mcp_servers/cicd/test_mcp_server_health_status.py and
    tests/mcp_servers/cicd/test_cicd_health_posture.py)
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
import pathlib
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import mcp_servers.dispatch as dispatch
import pytest
from fastapi.testclient import TestClient
from mcp_servers.cicd import cicd_server
from mcp_servers.cicd.cicd_models import CicdConfig
from mcp_servers.cicd.cicd_service_guards import ProbeOutcome
from shared.security.result_dto import (
    REASON_DEPENDENCY_UNREACHABLE,
    REASON_NOT_APPLICABLE,
)

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

    def test_disabled_tool_writes_exactly_one_rejected_record(
        self,
        client: TestClient,
        fake_service: _FakeService,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The disabled path now writes a record, which the Plan's corrected documentation states.

        Per-category emission is pinned in `tests/mcp_servers/cicd/test_cicd_audit.py`;
        this test only closes the gap this file had on the disabled path.
        """
        monkeypatch.setattr(
            cicd_server, "_cfg", CicdConfig(repo_allowlist=[], workflow_allowlist=[])
        )
        logger = MagicMock()
        monkeypatch.setattr(cicd_server, "logger", logger)
        handler = AsyncMock(return_value="run triggered")
        fake_service._dispatch_table["trigger_workflow"] = handler
        resp = client.post(
            "/v1/call_tool",
            json={"name": "trigger_workflow", "args": {"repo": "acme/widgets"}},
            headers={"x-idempotency-key": str(uuid.uuid4())},
        )
        assert resp.status_code == 200
        records = [
            json.loads(call.args[0])
            for call in logger.info.call_args_list
            if str(call.args[0]).startswith("{")
        ]
        assert len(records) == 1
        assert records[0]["outcome"] == "rejected"
        assert records[0]["error_type"] == "tool_disabled"
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
        assert body == {
            "result": "run triggered",
            "is_error": False,
            "dedup_state": "",
            "execution_mode": "applied",
            "side_effect_applied": True,
        }
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

    def test_validation_error_writes_exactly_one_rejected_record(
        self,
        client: TestClient,
        fake_service: _FakeService,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The `ExecutionContextError` path now writes a record before returning.

        A claimed mode that disagrees with the resolver raises the error, so the call is
        refused before the handler runs and the outcome is a rejection.
        """
        monkeypatch.setattr(
            cicd_server,
            "_cfg",
            CicdConfig(repo_allowlist=["acme/widgets"], workflow_allowlist=["ci.yml"]),
        )
        logger = MagicMock()
        monkeypatch.setattr(cicd_server, "logger", logger)
        handler = AsyncMock(return_value="run triggered")
        fake_service._dispatch_table["trigger_workflow"] = handler
        resp = client.post(
            "/v1/call_tool",
            json={"name": "trigger_workflow", "args": {"repo": "acme/widgets"}},
            headers={
                "x-idempotency-key": str(uuid.uuid4()),
                "x-execution-mode": "preview",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["is_error"] is True
        records = [
            json.loads(call.args[0])
            for call in logger.info.call_args_list
            if str(call.args[0]).startswith("{")
        ]
        assert len(records) == 1
        assert records[0]["outcome"] == "rejected"
        assert records[0]["error_type"] == "validation_error"
        handler.assert_not_awaited()


class TestHealthEndpoint:
    def test_healthy_when_github_token_set(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The no-store case: with no store wired the details dict is what it was before this row.
        monkeypatch.setattr(dispatch, "_dedup_store", None)
        monkeypatch.setattr(dispatch, "_dedup_config", None)
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token")
        # The posture is built from the effective credential, so it is rebuilt here with one
        # present; the module-level posture was built at import with none. The lifespan does not
        # run for a TestClient that is not entered, so the probe outcome stays unset.
        monkeypatch.setattr(
            cicd_server, "_security_posture", cicd_server._build_security_posture()
        )
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["ready"] is True
        assert body["dependencies"] == {}
        # The `service` key stays as it is; `audit_failure_count` is the counter the
        # never-propagate policy maintains (UNK-02), and `dedup` is the block REQ-004
        # publishes. The value is process-global, so only the key and its type are pinned.
        assert body["details"]["service"] == "cicd-mcp"
        assert isinstance(body["details"]["audit_failure_count"], int)
        assert set(body["details"]) == {"service", "audit_failure_count"}

    def test_health_reports_a_failed_probe_as_a_dependency(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The probe outcome reaches health through the shared ready rule (REQ-003, AC-7)."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token")
        monkeypatch.setattr(
            cicd_server, "_security_posture", cicd_server._build_security_posture()
        )
        monkeypatch.setattr(
            cicd_server,
            "_probe_outcome",
            ProbeOutcome(
                REASON_DEPENDENCY_UNREACHABLE,
                REASON_DEPENDENCY_UNREACHABLE,
                REASON_NOT_APPLICABLE,
            ),
        )
        resp = client.get("/health")
        assert resp.status_code == 503
        body = resp.json()
        assert body["ready"] is False
        assert body["dependencies"] == {
            "credential_probe": REASON_DEPENDENCY_UNREACHABLE
        }

    def test_health_details_publish_the_dedup_block_when_a_store_is_wired(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
        isolated_dedup: pathlib.Path,
    ) -> None:
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token")
        monkeypatch.setattr(
            cicd_server, "_security_posture", cicd_server._build_security_posture()
        )
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()

        # The `service` key stays as it is; `audit_failure_count` is the counter the
        # never-propagate policy maintains (UNK-02); `dedup` is the single new key (REQ-004).
        assert body["details"]["service"] == "cicd-mcp"
        assert set(body["details"]) == {"service", "audit_failure_count", "dedup"}
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
