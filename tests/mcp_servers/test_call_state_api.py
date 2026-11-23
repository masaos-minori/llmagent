"""tests/mcp_servers/test_call_state_api.py — Control API auth, shape, and reconcile flow.

The app is assembled in the production order: tool auth first, the control API
second, so the control middleware is outermost and control paths never reach tool
auth. Rows are seeded through the normal ledger entry points on a tmp_path store,
and the control module state is reset for every test.
"""

from __future__ import annotations

import sqlite3
import time
from collections.abc import Mapping
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from mcp_servers import control_api
from mcp_servers.models import CallStateResponse, ReconcileResponse
from mcp_servers.server import attach_auth_middleware
from pydantic import ValidationError
from shared.mcp_call_state_contract import RESULT_CLASSES, ReconcileEvidence
from shared.mcp_dedup import DedupStore, DedupStoreConfig, open_dedup_store

TOOL_TOKEN = "tool-secret"
CONTROL_TOKEN = "control-secret"
SERVER = "test-mcp"
TOOL_NAME = "shell"
ARGS_HASH = "abcdef1234567890"
SNAPSHOT = {"shell": "snapshot-value-not-in-any-response"}
OWNER = "owner-1"
_PAST = time.time() - 120.0


def _config(
    tmp_path: Path, *, lease_seconds: int, max_attempts: int
) -> DedupStoreConfig:
    """Store config for one test; the db file stays on tmp_path."""
    return DedupStoreConfig(
        db_path=str(tmp_path / "control_test.sqlite"),
        lease_seconds=lease_seconds,
        max_attempts=max_attempts,
    )


def _setup(
    tmp_path: Path, *, lease_seconds: int = 30, max_attempts: int = 3
) -> tuple[TestClient, DedupStore]:
    """Build the app and the store the control API reads, with state reset."""
    control_api.clear_reconcilers()
    config = _config(tmp_path, lease_seconds=lease_seconds, max_attempts=max_attempts)
    store = open_dedup_store(config)
    app = FastAPI()

    @app.get("/v1/tools/ping")
    def ping() -> dict[str, bool]:
        """Tool path, used to confirm tool-path auth is unchanged."""
        return {"ok": True}

    # Production order: tool auth first, then the control API.
    attach_auth_middleware(app, TOOL_TOKEN)
    control_api.configure_control(CONTROL_TOKEN, config, SERVER)
    control_api.attach_control_api(app)
    return TestClient(app), store


def _headers(token: str = CONTROL_TOKEN) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _seed(store: DedupStore, key: str, *, now_epoch: float | None = None) -> int:
    """Acquire one row through the normal entry point; returns the attempt number."""
    result = store.try_acquire_execution(
        key, TOOL_NAME, ARGS_HASH, SNAPSHOT, OWNER, now_epoch=now_epoch
    )
    return result.attempt_number


def _reconcile_history(
    store: DedupStore, key: str
) -> list[tuple[int, str, str | None]]:
    """Reconcile decisions only: call_attempt_history also records the other stages."""
    conn = sqlite3.connect(store.db_path)
    try:
        return [
            tuple(row)
            for row in conn.execute(
                "SELECT attempt_number, outcome, detail FROM call_attempt_history"
                " WHERE key=? AND outcome='reconcile_decision' ORDER BY rowid",
                (key,),
            )
        ]
    finally:
        conn.close()


class _StubReconciler:
    """Fixed-outcome reconciler registered through the registry seam."""

    def __init__(self, outcome: str) -> None:
        self._outcome = outcome

    def reconcile(
        self, tool_name: str, call_key: str, snapshot: Mapping[str, str]
    ) -> ReconcileEvidence:
        return ReconcileEvidence(outcome=self._outcome, digest="stub-digest")


class _RaisingReconciler:
    """Reconciler that fails; the control API must not turn it into a 500."""

    def reconcile(
        self, tool_name: str, call_key: str, snapshot: Mapping[str, str]
    ) -> ReconcileEvidence:
        raise RuntimeError("reconciler failed")


class TestControlAuthorization:
    def test_control_token_is_accepted(self, tmp_path: Path) -> None:
        client, store = _setup(tmp_path)
        _seed(store, "call-auth")
        response = client.get("/v1/call_state/call-auth", headers=_headers())
        assert response.status_code == 200
        assert response.json()["key"] == "call-auth"

    def test_tool_token_is_rejected_on_control_paths(self, tmp_path: Path) -> None:
        client, store = _setup(tmp_path)
        _seed(store, "call-tool-token")
        response = client.get(
            "/v1/call_state/call-tool-token", headers=_headers(TOOL_TOKEN)
        )
        assert response.status_code == 401

    def test_missing_header_is_rejected(self, tmp_path: Path) -> None:
        client, store = _setup(tmp_path)
        _seed(store, "call-no-header")
        assert client.get("/v1/call_state/call-no-header").status_code == 401

    def test_empty_configured_token_fails_closed(self, tmp_path: Path) -> None:
        client, store = _setup(tmp_path)
        _seed(store, "call-empty-token")
        control_api.configure_control(
            "", _config(tmp_path, lease_seconds=30, max_attempts=3), SERVER
        )
        response = client.get(
            "/v1/call_state/call-empty-token", headers={"Authorization": "Bearer "}
        )
        assert response.status_code == 401

    def test_tool_paths_still_require_the_tool_token(self, tmp_path: Path) -> None:
        client, _store = _setup(tmp_path)
        assert (
            client.get("/v1/tools/ping", headers=_headers(TOOL_TOKEN)).status_code
            == 200
        )
        assert client.get("/v1/tools/ping", headers=_headers()).status_code == 401
        assert client.get("/v1/tools/ping").status_code == 401


class TestCallStateShape:
    def test_completed_row_reports_the_closed_fields(self, tmp_path: Path) -> None:
        client, store = _setup(tmp_path)
        _seed(store, "call-shape")
        store.record_completed("call-shape", SNAPSHOT, {"stdout": "ok"}, OWNER)
        response = client.get("/v1/call_state/call-shape", headers=_headers())
        assert response.status_code == 200
        body = response.json()
        assert set(body) == set(CallStateResponse.model_fields)
        assert body["ledger_status"] == "completed"
        assert body["agent_state"] == "completed"
        assert body["result_class"] in RESULT_CLASSES
        assert body["error_code"] == "none"
        assert body["reconciliation_required"] is False
        assert response.headers["X-Request-Id"]

    def test_response_carries_no_arguments_paths_or_tokens(
        self, tmp_path: Path
    ) -> None:
        client, store = _setup(tmp_path)
        _seed(store, "call-private")
        store.record_completed("call-private", SNAPSHOT, {"stdout": "ok"}, OWNER)
        text = client.get("/v1/call_state/call-private", headers=_headers()).text
        for forbidden in (
            SNAPSHOT["shell"],
            ARGS_HASH,
            "/home",
            "/opt",
            TOOL_TOKEN,
            CONTROL_TOKEN,
            OWNER,
        ):
            assert forbidden not in text

    def test_models_reject_fields_outside_the_closed_shape(
        self, tmp_path: Path
    ) -> None:
        client, store = _setup(tmp_path)
        _seed(store, "call-extra")
        store.record_completed("call-extra", SNAPSHOT, {"stdout": "ok"}, OWNER)
        body = client.get("/v1/call_state/call-extra", headers=_headers()).json()
        with pytest.raises(ValidationError):
            CallStateResponse(**{**body, "snapshot_json": "extra"})
        reconcile = client.post(
            "/v1/call_state/call-extra/reconcile", headers=_headers()
        ).json()
        with pytest.raises(ValidationError):
            ReconcileResponse(**{**reconcile, "request_body": "extra"})

    def test_failed_row_reports_handler_failed(self, tmp_path: Path) -> None:
        client, store = _setup(tmp_path)
        _seed(store, "call-failed")
        store.record_failed("call-failed", "TimeoutError", OWNER)
        body = client.get("/v1/call_state/call-failed", headers=_headers()).json()
        assert body["ledger_status"] == "failed"
        assert body["agent_state"] == "failed"
        assert body["result_class"] == "replay_unavailable"
        assert body["result_code"] == "TimeoutError"
        assert body["error_code"] == "handler_failed"


class TestReconcileFlow:
    def test_completed_row_is_reused_without_mutation(self, tmp_path: Path) -> None:
        client, store = _setup(tmp_path)
        _seed(store, "call-completed")
        store.record_completed("call-completed", SNAPSHOT, {"stdout": "ok"}, OWNER)
        before = store.get_execution("call-completed")
        response = client.post(
            "/v1/call_state/call-completed/reconcile", headers=_headers()
        )
        assert response.status_code == 200
        body = response.json()
        assert set(body) == set(ReconcileResponse.model_fields)
        assert body["decision"] == "reused_completed"
        assert body["outcome"] == "none"
        assert body["operator_review"] is False
        assert store.get_execution("call-completed") == before
        assert _reconcile_history(store, "call-completed") == []

    def test_live_lease_is_refused(self, tmp_path: Path) -> None:
        client, store = _setup(tmp_path, lease_seconds=30)
        _seed(store, "call-live")
        response = client.post("/v1/call_state/call-live/reconcile", headers=_headers())
        assert response.status_code == 409
        body = response.json()
        assert body["decision"] == "refused"
        assert body["error_code"] == "lease_live"
        assert store.get_execution("call-live").status == "pending"

    def test_exhausted_attempts_are_refused_with_review(self, tmp_path: Path) -> None:
        client, store = _setup(tmp_path, lease_seconds=1, max_attempts=2)
        _seed(store, "call-exhausted", now_epoch=_PAST)
        # Reach the last allowed attempt the way recovery does: reconcile, reacquire.
        store.reconcile_execution("call-exhausted", now_epoch=_PAST + 20.0)
        store.try_acquire_execution(
            "call-exhausted",
            TOOL_NAME,
            ARGS_HASH,
            SNAPSHOT,
            "owner-2",
            now_epoch=_PAST + 21.0,
        )
        response = client.post(
            "/v1/call_state/call-exhausted/reconcile", headers=_headers()
        )
        assert response.status_code == 409
        body = response.json()
        assert body["decision"] == "refused"
        assert body["error_code"] == "attempts_exhausted"
        assert body["operator_review"] is True
        assert store.get_execution("call-exhausted").status == "pending"

    def test_expired_lease_without_reconciler_moves_the_row(
        self, tmp_path: Path
    ) -> None:
        client, store = _setup(tmp_path, lease_seconds=1)
        _seed(store, "call-expired", now_epoch=_PAST)
        body = client.post(
            "/v1/call_state/call-expired/reconcile", headers=_headers()
        ).json()
        assert body["decision"] == "operator_review"
        assert body["error_code"] == "not_reconcilable"
        assert body["agent_state"] == "reconciliation_required"
        assert store.get_execution("call-expired").status == "interrupted"

    def test_ambiguous_reconciler_leaves_the_row_unchanged(
        self, tmp_path: Path
    ) -> None:
        client, store = _setup(tmp_path, lease_seconds=1)
        _seed(store, "call-ambiguous", now_epoch=_PAST)
        control_api.register_reconciler(TOOL_NAME, _StubReconciler("ambiguous"))
        body = client.post(
            "/v1/call_state/call-ambiguous/reconcile", headers=_headers()
        ).json()
        assert body["decision"] == "operator_review"
        assert body["outcome"] == "ambiguous"
        assert body["operator_review"] is True
        assert store.get_execution("call-ambiguous").status == "pending"

    def test_evidence_found_moves_the_row_and_records_history(
        self, tmp_path: Path
    ) -> None:
        client, store = _setup(tmp_path, lease_seconds=1)
        _seed(store, "call-evidence", now_epoch=_PAST)
        control_api.register_reconciler(TOOL_NAME, _StubReconciler("evidence_found"))
        body = client.post(
            "/v1/call_state/call-evidence/reconcile", headers=_headers()
        ).json()
        assert body["decision"] == "reconciled"
        assert body["outcome"] == "evidence_found"
        assert body["evidence_digest"] == "stub-digest"
        assert store.get_execution("call-evidence").status == "interrupted"
        history = _reconcile_history(store, "call-evidence")
        assert history == [(1, "reconcile_decision", "evidence_found:stub-digest")]

    def test_reconciler_failure_reports_operator_review(self, tmp_path: Path) -> None:
        client, store = _setup(tmp_path, lease_seconds=1)
        _seed(store, "call-reconciler-error", now_epoch=_PAST)
        control_api.register_reconciler(TOOL_NAME, _RaisingReconciler())
        body = client.post(
            "/v1/call_state/call-reconciler-error/reconcile", headers=_headers()
        ).json()
        assert body["decision"] == "operator_review"
        assert body["error_code"] == "reconciler_failed"
        assert store.get_execution("call-reconciler-error").status == "pending"


class TestUnknownAndMalformedKey:
    def test_unknown_key_is_404(self, tmp_path: Path) -> None:
        client, _store = _setup(tmp_path)
        response = client.get("/v1/call_state/call-unknown", headers=_headers())
        assert response.status_code == 404
        assert response.json() == {"key": "call-unknown", "error_code": "unknown_key"}

    def test_malformed_key_is_422(self, tmp_path: Path) -> None:
        client, _store = _setup(tmp_path)
        response = client.get("/v1/call_state/bad.key;name", headers=_headers())
        assert response.status_code == 422
        assert response.json()["error_code"] == "invalid_key"

    def test_empty_key_is_422(self, tmp_path: Path) -> None:
        client, _store = _setup(tmp_path)
        response = client.get("/v1/call_state/", headers=_headers())
        assert response.status_code == 422
        assert response.json()["error_code"] == "invalid_key"
