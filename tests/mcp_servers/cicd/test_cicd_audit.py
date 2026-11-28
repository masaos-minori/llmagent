"""tests/mcp_servers/cicd/test_cicd_audit.py

Exactly-once audit emission for `call_tool()` in scripts/mcp_servers/cicd/cicd_server.py.

Every authenticated call emits exactly one record through `AuditEmission` from the
handler's `finally` block (REQ-005, AC-4): success, disabled tool, unknown tool,
validation, authorization, upstream, dedup, and unexpected outcomes. The record carries
the normalized `owner/repo` target and the stable CI/CD error code, and never a token or
a workflow input value (REQ-006, AC-5). An audit-write failure is logged and counted,
not raised (REQ-007, the policy decided by the owner on 20261127).

The shared helper's own exactly-once and redaction behavior is pinned by
`tests/mcp_servers/test_audit_redaction.py` lines 40-85 and is not re-implemented here;
this file pins only the CI/CD server's outcome classification, its target and error-code
fields, and the never-propagate policy.
"""

from __future__ import annotations

import json
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from mcp_servers import audit as audit_module
from mcp_servers.cicd import cicd_server
from mcp_servers.cicd.cicd_models import (
    CicdAuthorizationError,
    CicdConfig,
    CicdUpstreamError,
)

from tests.mcp_servers._auth_headers import MCP_TEST_AUTH_HEADERS


def _records(logger: MagicMock) -> list[dict[str, Any]]:
    """The JSON audit lines the mocked logger received.

    The same logger also emits the key=value `call_tool` line, which is not JSON, so
    only the JSON payload is parsed.
    """
    return [
        json.loads(call.args[0])
        for call in logger.info.call_args_list
        if str(call.args[0]).startswith("{")
    ]


@pytest.fixture
def fake_service(monkeypatch: pytest.MonkeyPatch) -> Any:
    """The same minimal stand-in `test_cicd_server_endpoints.py` uses for `CiCdService`."""

    class _FakeService:
        def __init__(self) -> None:
            self._dispatch_table: dict[str, Any] = {}

        def get_dispatch_table(self) -> dict[str, Any]:
            return self._dispatch_table

    svc = _FakeService()
    monkeypatch.setattr(cicd_server, "_service", svc)
    return svc


@pytest.fixture
def client() -> TestClient:
    return TestClient(cicd_server.app, headers=MCP_TEST_AUTH_HEADERS)


@pytest.fixture
def audit_logger(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    logger = MagicMock()
    monkeypatch.setattr(cicd_server, "logger", logger)
    return logger


@pytest.fixture
def allowlisted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        cicd_server,
        "_cfg",
        CicdConfig(repo_allowlist=["acme/widgets"], workflow_allowlist=["ci.yml"]),
    )


@pytest.fixture
def zero_counter(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate the module-level audit-failure counter for one test."""
    monkeypatch.setattr(cicd_server, "_audit_failure_count", 0)


class TestExactlyOneRecordPerCategory:
    """One record per call for every result category (REQ-005, AC-4)."""

    def test_success_emits_one_record(
        self,
        client: TestClient,
        fake_service: Any,
        audit_logger: MagicMock,
        allowlisted: None,
    ) -> None:
        fake_service._dispatch_table["trigger_workflow"] = AsyncMock(
            return_value="run triggered"
        )
        resp = client.post(
            "/v1/call_tool",
            json={"name": "trigger_workflow", "args": {"repo": "acme/widgets"}},
            headers={"x-idempotency-key": str(uuid.uuid4())},
        )
        assert resp.status_code == 200
        records = _records(audit_logger)
        assert len(records) == 1
        assert records[0]["outcome"] == "ok"
        assert records[0]["error_type"] == ""
        assert records[0]["tool"] == "trigger_workflow"
        assert records[0]["server_key"] == "cicd"

    def test_disabled_tool_emits_one_rejected_record(
        self,
        client: TestClient,
        fake_service: Any,
        audit_logger: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            cicd_server, "_cfg", CicdConfig(repo_allowlist=[], workflow_allowlist=[])
        )
        fake_service._dispatch_table["trigger_workflow"] = AsyncMock(
            return_value="run triggered"
        )
        resp = client.post(
            "/v1/call_tool",
            json={"name": "trigger_workflow", "args": {"repo": "acme/widgets"}},
            headers={"x-idempotency-key": str(uuid.uuid4())},
        )
        assert resp.status_code == 200
        assert resp.json()["is_error"] is True
        records = _records(audit_logger)
        assert len(records) == 1
        assert records[0]["outcome"] == "rejected"
        assert records[0]["error_type"] == "tool_disabled"

    def test_unknown_tool_emits_one_rejected_record(
        self,
        client: TestClient,
        fake_service: Any,
        audit_logger: MagicMock,
        allowlisted: None,
    ) -> None:
        resp = client.post("/v1/call_tool", json={"name": "not_a_tool", "args": {}})
        assert resp.status_code == 200
        records = _records(audit_logger)
        assert len(records) == 1
        assert records[0]["outcome"] == "rejected"
        assert records[0]["error_type"] == "unknown_tool"

    def test_validation_error_emits_one_rejected_record(
        self,
        client: TestClient,
        fake_service: Any,
        audit_logger: MagicMock,
        allowlisted: None,
    ) -> None:
        # A claimed mode that disagrees with the resolver raises
        # `ExecutionContextError` before dispatch.
        fake_service._dispatch_table["trigger_workflow"] = AsyncMock(
            return_value="run triggered"
        )
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
        records = _records(audit_logger)
        assert len(records) == 1
        assert records[0]["outcome"] == "rejected"
        assert records[0]["error_type"] == "validation_error"

    def test_allowlist_authorization_emits_one_rejected_record(
        self,
        client: TestClient,
        fake_service: Any,
        audit_logger: MagicMock,
        allowlisted: None,
    ) -> None:
        # The guard refuses the call before the backend is reached, so the category is
        # a rejection rather than a failure during the tool's work.
        fake_service._dispatch_table["get_workflow_runs"] = AsyncMock(
            side_effect=CicdAuthorizationError("Repo not in allowlist: acme/widgets")
        )
        resp = client.post(
            "/v1/call_tool",
            json={"name": "get_workflow_runs", "args": {"repo": "acme/widgets"}},
        )
        assert resp.status_code == 403
        records = _records(audit_logger)
        assert len(records) == 1
        assert records[0]["outcome"] == "rejected"
        assert records[0]["error_type"] == "authorization_error"

    def test_upstream_failure_emits_one_error_record(
        self,
        client: TestClient,
        fake_service: Any,
        audit_logger: MagicMock,
        allowlisted: None,
    ) -> None:
        fake_service._dispatch_table["get_workflow_runs"] = AsyncMock(
            side_effect=CicdUpstreamError("GitHub API error (status=500)")
        )
        resp = client.post(
            "/v1/call_tool",
            json={"name": "get_workflow_runs", "args": {"repo": "acme/widgets"}},
        )
        assert resp.status_code == 502
        records = _records(audit_logger)
        assert len(records) == 1
        assert records[0]["outcome"] == "error"
        assert records[0]["error_type"] == "upstream_error"

    def test_dedup_refusal_emits_one_rejected_record(
        self,
        client: TestClient,
        fake_service: Any,
        audit_logger: MagicMock,
        allowlisted: None,
        isolated_dedup: Any,
    ) -> None:
        fake_service._dispatch_table["trigger_workflow"] = AsyncMock(
            return_value="run triggered"
        )
        key = str(uuid.uuid4())
        body = {"name": "trigger_workflow", "args": {"repo": "acme/widgets"}}
        first = client.post(
            "/v1/call_tool", json=body, headers={"x-idempotency-key": key}
        )
        assert first.status_code == 200
        # The same key with different content is refused by the dedup gate.
        second = client.post(
            "/v1/call_tool",
            json={"name": "trigger_workflow", "args": {"repo": "other/widgets"}},
            headers={"x-idempotency-key": key},
        )
        assert second.status_code == 200
        assert second.json()["is_error"] is True
        records = _records(audit_logger)
        assert len(records) == 2
        assert records[0]["outcome"] == "ok"
        assert records[1]["outcome"] == "rejected"
        assert records[1]["error_type"] == "idempotency_key_reused"

    def test_unexpected_exception_emits_one_error_record(
        self,
        fake_service: Any,
        audit_logger: MagicMock,
        allowlisted: None,
    ) -> None:
        # `raise_server_exceptions=False` so the record written by `finally` is observed
        # before the exception reaches the transport handler.
        client = TestClient(
            cicd_server.app,
            headers=MCP_TEST_AUTH_HEADERS,
            raise_server_exceptions=False,
        )
        fake_service._dispatch_table["get_workflow_runs"] = AsyncMock(
            side_effect=RuntimeError("unexpected")
        )
        resp = client.post(
            "/v1/call_tool",
            json={"name": "get_workflow_runs", "args": {"repo": "acme/widgets"}},
        )
        assert resp.status_code == 500
        records = _records(audit_logger)
        assert len(records) == 1
        assert records[0]["outcome"] == "error"
        assert records[0]["error_type"] == "unexpected_error"


class TestRecordTargetAndRedaction:
    """The normalized target and the absence of credential and input values (REQ-006, AC-5)."""

    def test_target_is_the_normalized_repo_key(
        self,
        client: TestClient,
        fake_service: Any,
        audit_logger: MagicMock,
        allowlisted: None,
    ) -> None:
        fake_service._dispatch_table["get_workflow_runs"] = AsyncMock(
            return_value="no runs"
        )
        client.post(
            "/v1/call_tool",
            json={"name": "get_workflow_runs", "args": {"repo": "Acme/Widgets"}},
        )
        records = _records(audit_logger)
        assert len(records) == 1
        assert records[0]["target"] == "acme/widgets"

    def test_unnormalizable_slug_is_reported_as_requested(
        self,
        client: TestClient,
        fake_service: Any,
        audit_logger: MagicMock,
        allowlisted: None,
    ) -> None:
        # A slug the resolver cannot normalize is reported as the caller asked for, never
        # rewritten, so the record still identifies what was requested.
        fake_service._dispatch_table["get_workflow_runs"] = AsyncMock(
            return_value="no runs"
        )
        client.post(
            "/v1/call_tool",
            json={"name": "get_workflow_runs", "args": {"repo": "bad-slug"}},
        )
        records = _records(audit_logger)
        assert len(records) == 1
        assert records[0]["target"] == "bad-slug"

    def test_call_refused_before_the_args_are_read_has_no_target(
        self,
        client: TestClient,
        fake_service: Any,
        audit_logger: MagicMock,
        allowlisted: None,
    ) -> None:
        resp = client.post("/v1/call_tool", json={"name": "not_a_tool", "args": {}})
        assert resp.status_code == 200
        records = _records(audit_logger)
        assert len(records) == 1
        assert records[0]["target"] == "-"

    def test_record_carries_no_token_and_no_workflow_input_value(
        self,
        client: TestClient,
        fake_service: Any,
        audit_logger: MagicMock,
        allowlisted: None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_" + "A" * 36)
        fake_service._dispatch_table["get_workflow_runs"] = AsyncMock(
            return_value="no runs"
        )
        client.post(
            "/v1/call_tool",
            json={
                "name": "get_workflow_runs",
                "args": {"repo": "acme/widgets", "workflow": "secret-ci.yml"},
            },
        )
        payload = json.dumps(_records(audit_logger))
        assert "ghp_" not in payload
        assert "secret-ci.yml" not in payload


class TestAuditFailurePolicy:
    """An audit-write failure is logged and counted, never raised (REQ-007)."""

    def test_audit_write_failure_is_counted_and_not_raised(
        self,
        client: TestClient,
        fake_service: Any,
        audit_logger: MagicMock,
        allowlisted: None,
        zero_counter: None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def _failing_audit_log(*args: Any, **kwargs: Any) -> None:
            raise OSError("audit sink unavailable")

        # Only the audit write fails; the response path is untouched.
        monkeypatch.setattr(audit_module, "_audit_log", _failing_audit_log)
        fake_service._dispatch_table["get_workflow_runs"] = AsyncMock(
            return_value="no runs"
        )
        resp = client.post(
            "/v1/call_tool",
            json={"name": "get_workflow_runs", "args": {"repo": "acme/widgets"}},
        )
        # The response is the normal one: the audit failure does not mask it.
        assert resp.status_code == 200
        assert resp.json()["result"] == "no runs"
        assert cicd_server._audit_failure_count == 1
        audit_logger.error.assert_called_once()
