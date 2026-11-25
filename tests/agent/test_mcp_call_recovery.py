#!/usr/bin/env python3
"""tests/agent/test_mcp_call_recovery.py

Agent recovery after a lost tool-call response (mcpdl004 REQ-005).

Rows are seeded through the real workflow store and classified through
`tool_call_state_ops.classify_stale_pending` with the recovery service as the resolver, so
the assertions cover the whole decision point rather than the service in isolation. A fake
control plane answers control paths from a dict of payloads and counts any request that
reaches a tool path: a handler must never run during recovery.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import httpx
import pytest
import respx
from agent.mcp_call_recovery import McpCallRecoveryService, RecoveryResolution
from agent.tool_preparation import _canonical_args_hash
from agent.workflow import tool_call_state_ops
from agent.workflow.state_store import StateStore
from db.config import DbConfig
from db.create_schema import create_workflow_schema
from shared.mcp_call_state_contract import resolve_control_token
from shared.mcp_config import McpServerConfig, TransportType

_BASE = "http://control.test"
_PREFIX = "/v1/call_state/"
_TOOL_TOKEN = "dummy-tool-token"
_CONTROL_TOKEN = "dummy-control-token"
_TOOL = "git__remote_update"
_SERVER = "git"
_TIMEOUT_SEC = 300.0


def _make_cfg(key: str = _SERVER, token: str = _CONTROL_TOKEN) -> McpServerConfig:
    return McpServerConfig(
        transport=TransportType.HTTP,
        url=_BASE,
        key=key,
        auth_token=_TOOL_TOKEN,
        control_auth_token=token,
    )


class FakeControlPlane:
    """Answers control paths from a dict of payloads and counts tool-path requests."""

    def __init__(self, payloads: dict[str, dict[str, object]]) -> None:
        self.payloads = payloads
        self.control_calls = 0
        self.tool_calls = 0

    def handle(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if not path.startswith(_PREFIX):
            # Recovery is read-only: a request here would mean a handler ran.
            self.tool_calls += 1
            return httpx.Response(500, json={"error": "handler executed"})
        self.control_calls += 1
        key = path[len(_PREFIX) :].removesuffix("/reconcile")
        body = self.payloads.get(key)
        if body is None:
            return httpx.Response(404, json={"error_code": "unknown_key"})
        return httpx.Response(200, json=body)


@dataclass
class Env:
    store: StateStore
    task_id: str


@pytest.fixture()
def env(tmp_path: Path) -> Iterator[Env]:
    cfg = DbConfig(
        rag_db_path=str(tmp_path / "rag.sqlite"),
        session_db_path=str(tmp_path / "session.sqlite"),
        workflow_db_path=str(tmp_path / "workflow.sqlite"),
    )
    create_workflow_schema(db_config=cfg)
    store = StateStore(db_config=cfg)
    task = store.create_task("sess1", 1, "1.0.0", "wf-test")
    try:
        yield Env(store=store, task_id=task.task_id)
    finally:
        store.close()


def _seed_row(env: Env, key: str, state: str = "dispatched") -> None:
    """Seed one stale row through the store's own helpers.

    `created_at` is moved back so the row is past the caller's timeout window: recovery
    must never have to wait for a row to look stale.
    """
    env.store.record_tool_call(
        env.task_id, key, _TOOL, "retryable", _canonical_args_hash({"path": "/seed"})
    )
    env.store._db.execute(
        "UPDATE tool_call_state SET created_at=? WHERE idempotency_key=?",
        (time.time() - 600.0, key),
    )
    env.store.finalize_tool_call(key, state)
    env.store._db.commit()


def _row(env: Env, key: str) -> tool_call_state_ops.ToolCallState:
    row = tool_call_state_ops.get_tool_call_state(env.store._db, key)
    assert row is not None
    return row


def _service(plane: FakeControlPlane, max_lookups: int = 8) -> McpCallRecoveryService:
    return McpCallRecoveryService(
        {_SERVER: _make_cfg()},
        lambda tool: _SERVER if tool == _TOOL else None,
        max_lookups=max_lookups,
    )


def _control_route(plane: FakeControlPlane) -> None:
    respx.get(url__regex=_PREFIX + ".*").mock(side_effect=plane.handle)
    respx.post(url__regex=_PREFIX + ".*").mock(side_effect=plane.handle)


def _payload(key: str, **overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "key": key,
        "ledger_status": "completed",
        "agent_state": "completed",
        "attempt_number": 1,
        "lease_live": False,
        "result_class": "complete",
        "error_code": "none",
        "reconciliation_required": False,
    }
    body.update(overrides)
    return body


class TestStateMapping:
    """The shared mapping table applied at the stale-classification decision point."""

    def test_completed_call_finalizes_the_row(self, env: Env) -> None:
        key = "call-completed"
        plane = FakeControlPlane({key: _payload(key)})
        _seed_row(env, key)
        with respx.mock:
            _control_route(plane)
            classified = tool_call_state_ops.classify_stale_pending(
                env.store._db, env.task_id, _TIMEOUT_SEC, resolver=_service(plane)
            )
        assert [c.state for c in classified] == ["completed"]
        row = tool_call_state_ops.get_tool_call_state(env.store._db, key)
        assert row is not None and row.state == "completed"

    def test_failed_call_finalizes_the_row(self, env: Env) -> None:
        key = "call-failed"
        plane = FakeControlPlane(
            {
                key: _payload(
                    key,
                    ledger_status="failed",
                    agent_state="failed",
                    result_class="replay_unavailable",
                    error_code="handler_failed",
                )
            }
        )
        _seed_row(env, key)
        with respx.mock:
            _control_route(plane)
            classified = tool_call_state_ops.classify_stale_pending(
                env.store._db, env.task_id, _TIMEOUT_SEC, resolver=_service(plane)
            )
        assert [c.state for c in classified] == ["failed"]

    def test_expired_lease_and_interrupted_rows_need_reconciliation(
        self, env: Env
    ) -> None:
        payloads = {
            "call-expired": _payload(
                "call-expired",
                ledger_status="pending",
                agent_state="reconciliation_required",
                lease_live=False,
                reconciliation_required=True,
            ),
            "call-interrupted": _payload(
                "call-interrupted",
                ledger_status="interrupted",
                agent_state="reconciliation_required",
                reconciliation_required=True,
            ),
        }
        plane = FakeControlPlane(payloads)
        for key in payloads:
            _seed_row(env, key)
        with respx.mock:
            _control_route(plane)
            classified = tool_call_state_ops.classify_stale_pending(
                env.store._db, env.task_id, _TIMEOUT_SEC, resolver=_service(plane)
            )
        assert [c.state for c in classified] == [
            "reconciliation_required",
            "reconciliation_required",
        ]

    def test_in_progress_leaves_the_row_and_is_not_listed(self, env: Env) -> None:
        key = "call-live-lease"
        plane = FakeControlPlane(
            {
                key: _payload(
                    key,
                    ledger_status="pending",
                    agent_state="in_progress",
                    lease_live=True,
                )
            }
        )
        _seed_row(env, key)
        service = _service(plane)
        with respx.mock:
            _control_route(plane)
            assert service.resolve_state(_row(env, key)) == "in_progress"
            classified = tool_call_state_ops.classify_stale_pending(
                env.store._db, env.task_id, _TIMEOUT_SEC, resolver=service
            )
        assert classified == []
        row = tool_call_state_ops.get_tool_call_state(env.store._db, key)
        assert row is not None and row.state == "dispatched"

    def test_without_a_resolver_behavior_is_unchanged(self, env: Env) -> None:
        key = "call-plain"
        plane = FakeControlPlane({key: _payload(key)})
        _seed_row(env, key)
        with respx.mock:
            _control_route(plane)
            classified = tool_call_state_ops.classify_stale_pending(
                env.store._db, env.task_id, _TIMEOUT_SEC
            )
        assert [c.state for c in classified] == ["outcome_unknown"]
        assert plane.control_calls == 0

    def test_never_dispatched_rows_still_become_interrupted(self, env: Env) -> None:
        key = "call-never-dispatched"
        plane = FakeControlPlane({key: _payload(key)})
        _seed_row(env, key, state="pending")
        with respx.mock:
            _control_route(plane)
            classified = tool_call_state_ops.classify_stale_pending(
                env.store._db, env.task_id, _TIMEOUT_SEC, resolver=_service(plane)
            )
        assert [c.state for c in classified] == ["interrupted"]
        assert plane.control_calls == 0


class TestNoReexecution:
    """Recovery reads; it never runs a handler (mcpdl001 AC-6, REQ-005)."""

    def test_completed_call_is_reported_without_running_anything(
        self, env: Env
    ) -> None:
        key = "call-completed"
        plane = FakeControlPlane({key: _payload(key)})
        _seed_row(env, key)
        with respx.mock:
            _control_route(plane)
            resolution = _service(plane).resolve(_row(env, key))
        assert resolution == RecoveryResolution(
            agent_state="completed",
            result_class="complete",
            external_ref="",
            error_code="none",
        )
        assert plane.control_calls == 1
        assert plane.tool_calls == 0

    def test_replay_unavailable_is_reported_as_is(self, env: Env) -> None:
        key = "call-redacted"
        plane = FakeControlPlane({key: _payload(key, result_class="redacted_preview")})
        _seed_row(env, key)
        with respx.mock:
            _control_route(plane)
            resolution = _service(plane).resolve(_row(env, key))
        assert resolution is not None and resolution.result_class == "redacted_preview"
        assert plane.tool_calls == 0

    def test_control_request_uses_the_control_token_only(self, env: Env) -> None:
        key = "call-token"
        plane = FakeControlPlane({key: _payload(key)})
        _seed_row(env, key)
        with respx.mock:
            route = respx.get(url__regex=_PREFIX + ".*").mock(side_effect=plane.handle)
            _service(plane).resolve(_row(env, key))
        headers = route.calls[0].request.headers
        assert headers["authorization"] == f"Bearer {_CONTROL_TOKEN}"
        assert _TOOL_TOKEN not in headers["authorization"]

    def test_reconcile_is_called_only_when_asked(self, env: Env) -> None:
        key = "call-reconcile"
        plane = FakeControlPlane(
            {
                key: {
                    "key": key,
                    "decision": "reconciled",
                    "outcome": "evidence_found",
                    "ledger_status": "interrupted",
                    "agent_state": "reconciliation_required",
                    "operator_review": True,
                    "evidence_digest": "sha256:abc",
                    "error_code": "none",
                    "lease_live": False,
                }
            }
        )
        _seed_row(env, key)
        with respx.mock:
            route = respx.post(url__regex=_PREFIX + ".*reconcile").mock(
                side_effect=plane.handle
            )
            resolution = _service(plane).reconcile(_row(env, key))
        assert route.call_count == 1
        assert resolution is not None
        assert resolution.agent_state == "reconciliation_required"
        assert resolution.result_class == ""
        assert plane.tool_calls == 0


class TestDegradation:
    """Every control problem leaves the row at the outcome it would have had anyway."""

    @pytest.mark.parametrize(
        "case",
        [
            "empty-token",
            "unknown-server",
            "timeout",
            "http-401",
            "malformed-payload",
            "unknown-key",
            "out-of-vocabulary",
        ],
    )
    def test_control_problem_keeps_the_row_unknown(self, env: Env, case: str) -> None:
        key = f"call-{case}"
        # A control problem is reported as the fixed refusal, not as a guessed state: the
        # row keeps the outcome it would have had without a resolver.
        if case == "malformed-payload":
            body: dict[str, object] = {"agent_state": None}
        elif case == "unknown-key":
            body = {"agent_state": "outcome_unknown", "error_code": "unknown_key"}
        elif case == "out-of-vocabulary":
            body = _payload(key, agent_state="done")
        else:
            body = _payload(key)
        plane = FakeControlPlane({key: body})
        _seed_row(env, key)
        if case == "empty-token":
            service = McpCallRecoveryService(
                {_SERVER: _make_cfg(token="")}, lambda tool: _SERVER
            )
        elif case == "unknown-server":
            service = McpCallRecoveryService({}, lambda tool: None)
        else:
            service = _service(plane)
        with respx.mock:
            route = respx.get(url__regex=_PREFIX + ".*")
            if case == "timeout":
                route.mock(side_effect=httpx.ConnectTimeout("timed out"))
            elif case == "http-401":
                route.mock(return_value=httpx.Response(401, json={}))
            else:
                route.mock(side_effect=plane.handle)
            classified = tool_call_state_ops.classify_stale_pending(
                env.store._db, env.task_id, _TIMEOUT_SEC, resolver=service
            )
        assert [c.state for c in classified] == ["outcome_unknown"]
        # Only the cases answered by the fake plane reach it: a transport failure or a
        # missing credential is decided before any request is made.
        answered = {"malformed-payload", "unknown-key", "out-of-vocabulary"}
        assert plane.control_calls == (1 if case in answered else 0)

    def test_lookup_bound_limits_control_calls(self, env: Env) -> None:
        keys = ["call-bound-1", "call-bound-2", "call-bound-3", "call-bound-4"]
        plane = FakeControlPlane({key: _payload(key) for key in keys})
        for key in keys:
            _seed_row(env, key)
        service = _service(plane, max_lookups=2)
        with respx.mock:
            _control_route(plane)
            classified = tool_call_state_ops.classify_stale_pending(
                env.store._db, env.task_id, _TIMEOUT_SEC, resolver=service
            )
        assert plane.control_calls == 2
        # The two established rows are reported; the bounded ones keep the fallback.
        assert sorted(c.state for c in classified) == [
            "completed",
            "completed",
            "outcome_unknown",
            "outcome_unknown",
        ]

    def test_no_token_value_reaches_a_log_line(self, env: Env, caplog) -> None:
        key = "call-log-check"
        _seed_row(env, key)
        service = McpCallRecoveryService({}, lambda tool: None)
        with caplog.at_level(logging.WARNING):
            with respx.mock:
                _control_route(FakeControlPlane({}))
                service.resolve(_row(env, key))
        assert _CONTROL_TOKEN not in caplog.text
        assert key not in caplog.text  # the call id is logged as a prefix only


class TestScenarios:
    """The scenarios the plan names for response-loss recovery."""

    def test_dispatch_accepted_response_lost(self, env: Env) -> None:
        key = "call-lost-response"
        plane = FakeControlPlane(
            {
                key: _payload(
                    key,
                    result_class="secure_reference",
                    external_ref="ref-7",
                )
            }
        )
        _seed_row(env, key)
        with respx.mock:
            _control_route(plane)
            resolution = _service(plane).resolve(_row(env, key))
            classified = tool_call_state_ops.classify_stale_pending(
                env.store._db, env.task_id, _TIMEOUT_SEC, resolver=_service(plane)
            )
        assert resolution is not None and resolution.external_ref == "ref-7"
        assert [c.state for c in classified] == ["completed"]
        assert plane.tool_calls == 0

    def test_git_remote_update_evidence_reuse_does_not_push_again(
        self, env: Env
    ) -> None:
        key = "call-remote-update"
        plane = FakeControlPlane(
            {
                key: {
                    "key": key,
                    "decision": "reconciled",
                    "outcome": "evidence_found",
                    "ledger_status": "interrupted",
                    "agent_state": "reconciliation_required",
                    "operator_review": False,
                    "evidence_digest": "sha256:remote-ref",
                    "error_code": "none",
                    "lease_live": False,
                }
            }
        )
        _seed_row(env, key)
        with respx.mock:
            _control_route(plane)
            resolution = _service(plane).reconcile(_row(env, key))
        assert resolution is not None
        assert resolution.agent_state == "reconciliation_required"
        # Evidence reuse is a read: the duplicated push the plan names never happens.
        assert plane.tool_calls == 0

    def test_deletion_already_completed_is_reported_without_replaying(
        self, env: Env
    ) -> None:
        key = "call-deletion"
        plane = FakeControlPlane({key: _payload(key, result_class="secure_reference")})
        _seed_row(env, key)
        with respx.mock:
            _control_route(plane)
            resolution = _service(plane).resolve(_row(env, key))
        assert resolution is not None and resolution.agent_state == "completed"
        assert plane.tool_calls == 0

    def test_ambiguous_result_needs_operator_review(self, env: Env) -> None:
        key = "call-ambiguous-result"
        plane = FakeControlPlane(
            {
                key: _payload(
                    key,
                    # An ambiguous answer is still an answer: the mapping table is what
                    # names the state, and the error code says why it needs a person.
                    ledger_status="interrupted",
                    agent_state="reconciliation_required",
                    error_code="reconciler_failed",
                )
            }
        )
        _seed_row(env, key)
        with respx.mock:
            _control_route(plane)
            classified = tool_call_state_ops.classify_stale_pending(
                env.store._db, env.task_id, _TIMEOUT_SEC, resolver=_service(plane)
            )
        assert [c.state for c in classified] == ["reconciliation_required"]


class TestConfigField:
    """The Agent-side control credential itself."""

    def test_env_reference_resolves_and_unset_is_tolerated(self, monkeypatch) -> None:
        monkeypatch.setenv("MCP_GIT_CONTROL_TOKEN", "resolved-token")
        assert resolve_control_token("${ENV:MCP_GIT_CONTROL_TOKEN}") == "resolved-token"
        # An unset variable closes the control paths rather than stopping the Agent.
        monkeypatch.delenv("MCP_GIT_UNSET_CONTROL_TOKEN", raising=False)
        assert resolve_control_token("${ENV:MCP_GIT_UNSET_CONTROL_TOKEN}") == ""

    def test_service_performs_no_io_at_construction(self) -> None:
        # Clients are built on first use, so building the service for a configured
        # server is not a request.
        service = McpCallRecoveryService({_SERVER: _make_cfg()}, lambda tool: _SERVER)
        assert service._clients == {}
        assert service._lookups_used == 0
