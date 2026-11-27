"""tests/mcp_servers/cicd/test_service_github_actions_error_edges.py

Characterization tests locking the branches of
scripts/mcp_servers/cicd/cicd_service_github_actions.py that are not exercised by
tests/mcp_servers/cicd/test_cicd_mcp_service.py, plus the structured-state contract
tests written before the code change (Plan Phase 1, mcpci002):

- GitHubActionsBackend._parse_error_message: the `except (ValueError,
  UnicodeDecodeError)` fallback to `default` when the response body cannot be
  parsed as JSON (parse_http_json raises ValueError on malformed JSON).
- GitHubActionsBackend.trigger_workflow: the non-204 success path, expressed as the
  structured outcome — a 2xx with no matched run is accepted_unconfirmed, never
  confirmed (REQ-001).
- URL path-segment encoding added by REQ-005 (AC-4): the workflow value is quoted as
  one segment, so a separator or a percent-encoded segment cannot alter the dispatch
  path.
- Bounded polling states (REQ-003): response loss -> outcome_unknown, no run after
  the bounded window -> accepted_unconfirmed, delayed unique match -> confirmed with
  the run fields, multiple candidates -> reconciliation_required.
- Pre-dispatch run search for a repeat logical call (REQ-004, AC-3).
- Reconcile outcome mapping from the recorded correlation, without I/O (REQ-007).

Mocked HTTP, no live GitHub call. The polling constants are patched per test so the
bounded window stays fast.
"""

from __future__ import annotations

import datetime
import re
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import orjson
import pytest
from mcp_servers.cicd import cicd_service_github_actions as backend_module
from mcp_servers.cicd.cicd_models import (
    CicdAuthorizationError,
    CicdValidationError,
    DispatchOutcome,
)
from mcp_servers.cicd.cicd_service_defs import _GITHUB_API_BASE
from mcp_servers.cicd.cicd_service_github_actions import (
    GitHubActionsBackend,
    bind_call_identity,
    dispatch_reconciler,
)
from shared.write_outcome import OUTCOME_UNKNOWN


@pytest.fixture(autouse=True)
def _clear_correlation() -> None:
    """The correlation record is module-level in-process state; isolate each test."""
    backend_module._CORRELATION.clear()
    yield
    backend_module._CORRELATION.clear()


def _make_malformed_body_response(status_code: int) -> MagicMock:
    """Build a mock httpx.Response with a non-JSON body (triggers the ValueError fallback)."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.is_success = 200 <= status_code < 300
    resp.content = b"not valid json"
    resp.headers = {}
    return resp


def _iso_now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


def _future_iso() -> str:
    """A created_at after the dispatch time, so the run matches the correlation."""
    return (
        datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=1)
    ).isoformat()


def _run(run_id: int, created_at: str, head_branch: str = "main") -> dict[str, Any]:
    return {
        "id": run_id,
        "name": "ci.yml",
        "status": "completed",
        "conclusion": "success",
        "created_at": created_at,
        "updated_at": created_at,
        "html_url": f"https://github.com/owner/repo/actions/runs/{run_id}",
        "head_branch": head_branch,
        "head_sha": "abcdef1234567890",
    }


def _runs_response(runs: list[dict[str, Any]]) -> MagicMock:
    """Mock the run-list GET response the polling path reads."""
    resp = MagicMock()
    resp.status_code = 200
    resp.is_success = True
    resp.headers = {}
    resp.content = orjson.dumps({"workflow_runs": runs, "total_count": len(runs)})
    return resp


def _post_response(status_code: int = 204) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.is_success = 200 <= status_code < 300
    resp.headers = {}
    return resp


def _fast_polling(monkeypatch: pytest.MonkeyPatch) -> None:
    """Shrink the bounded polling window so the contract tests stay fast."""
    monkeypatch.setattr(backend_module, "POLL_TIMEOUT_S", 0.05)
    monkeypatch.setattr(backend_module, "POLL_INTERVAL_S", 0.01)


class TestParseErrorMessageMalformedBody:
    """_parse_error_message must fall back to `default` when the body isn't JSON."""

    def test_422_with_malformed_body_uses_default_message(self) -> None:
        backend = GitHubActionsBackend("token", MagicMock())
        resp = _make_malformed_body_response(422)
        with pytest.raises(CicdValidationError) as exc_info:
            backend._check_response(resp, "test context")
        assert "Unprocessable Entity" in str(exc_info.value)

    def test_403_with_malformed_body_uses_default_message(self) -> None:
        backend = GitHubActionsBackend("token", MagicMock())
        resp = _make_malformed_body_response(403)
        with pytest.raises(CicdAuthorizationError) as exc_info:
            backend._check_response(resp, "test context")
        assert "Access denied" in str(exc_info.value)


class TestTriggerWorkflowNonNoContentSuccess:
    """A plain 2xx that isn't 204 is accepted, never confirmed without a matched run."""

    @pytest.mark.asyncio
    async def test_200_success_returns_structured_outcome(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _fast_polling(monkeypatch)
        http = AsyncMock()
        http.post.return_value = _post_response(200)
        http.get.return_value = _runs_response([])
        backend = GitHubActionsBackend("token", http)

        with bind_call_identity("s1", "r1", "key-1"):
            outcome = await backend.trigger_workflow(
                "owner", "repo", "ci.yml", "main", {}
            )

        assert isinstance(outcome, DispatchOutcome)
        # REQ-001: a 2xx response never becomes confirmed without a matched run.
        assert outcome.state == "accepted_unconfirmed"
        assert outcome.workflow == "ci.yml"
        assert outcome.ref == "main"
        assert outcome.run_id is None


class TestTriggerWorkflowBoundedPolling:
    """The bounded polling window produces the distinct REQ-003 states."""

    @pytest.mark.asyncio
    async def test_response_loss_returns_outcome_unknown(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _fast_polling(monkeypatch)
        http = AsyncMock()
        http.post.side_effect = httpx.ConnectError("response lost")
        backend = GitHubActionsBackend("token", http)

        with bind_call_identity("s1", "r1", "key-loss"):
            outcome = await backend.trigger_workflow(
                "owner", "repo", "ci.yml", "main", {}
            )

        assert outcome.state == OUTCOME_UNKNOWN

    @pytest.mark.asyncio
    async def test_no_run_after_window_returns_accepted_unconfirmed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _fast_polling(monkeypatch)
        http = AsyncMock()
        http.post.return_value = _post_response(204)
        http.get.return_value = _runs_response([])
        backend = GitHubActionsBackend("token", http)

        with bind_call_identity("s1", "r1", "key-none"):
            outcome = await backend.trigger_workflow(
                "owner", "repo", "ci.yml", "main", {}
            )

        assert outcome.state == "accepted_unconfirmed"

    @pytest.mark.asyncio
    async def test_delayed_unique_match_returns_confirmed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _fast_polling(monkeypatch)
        created = _future_iso()
        http = AsyncMock()
        http.post.return_value = _post_response(204)
        http.get.side_effect = [
            _runs_response([]),
            _runs_response([_run(42, created)]),
        ]
        backend = GitHubActionsBackend("token", http)

        with bind_call_identity("s1", "r1", "key-delayed"):
            outcome = await backend.trigger_workflow(
                "owner", "repo", "ci.yml", "main", {}
            )

        assert outcome.state == "confirmed"
        assert outcome.run_id == 42
        assert outcome.run_url == "https://github.com/owner/repo/actions/runs/42"
        assert outcome.run_status == "completed"
        assert outcome.workflow == "ci.yml"
        assert outcome.ref == "main"

    @pytest.mark.asyncio
    async def test_multiple_candidates_returns_reconciliation_required(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _fast_polling(monkeypatch)
        created = _future_iso()
        http = AsyncMock()
        http.post.return_value = _post_response(204)
        http.get.return_value = _runs_response([_run(1, created), _run(2, created)])
        backend = GitHubActionsBackend("token", http)

        with bind_call_identity("s1", "r1", "key-multi"):
            outcome = await backend.trigger_workflow(
                "owner", "repo", "ci.yml", "main", {}
            )

        assert outcome.state == "reconciliation_required"


class TestPreDispatchSearch:
    """A repeat of the same logical call searches for the run before dispatching (AC-3)."""

    @pytest.mark.asyncio
    async def test_repeat_logical_call_searches_before_dispatch(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _fast_polling(monkeypatch)
        created = _future_iso()
        http = AsyncMock()
        http.post.return_value = _post_response(204)
        # Every GET for the first call sees no run yet; the repeat's pre-dispatch
        # search sees the run the first call created.
        repeat = {"on": False}
        http.get.side_effect = lambda *_a, **_kw: _runs_response(
            [_run(7, created)] if repeat["on"] else []
        )
        backend = GitHubActionsBackend("token", http)

        with bind_call_identity("s1", "r1", "key-a"):
            first = await backend.trigger_workflow(
                "owner", "repo", "ci.yml", "main", {}
            )
        assert first.state == "accepted_unconfirmed"
        repeat["on"] = True

        with bind_call_identity("s1", "r2", "key-b"):
            second = await backend.trigger_workflow(
                "owner", "repo", "ci.yml", "main", {}
            )

        assert second.state == "confirmed"
        assert second.run_id == 7
        # The repeat was not dispatched again: only the first call posted (REQ-004).
        assert http.post.call_count == 1


class TestReconcileOutcomeMapping:
    """reconcile answers from the recorded correlation without I/O (REQ-007)."""

    @pytest.mark.asyncio
    async def test_record_hit_returns_evidence_found(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _fast_polling(monkeypatch)
        http = AsyncMock()
        http.post.return_value = _post_response(204)
        http.get.return_value = _runs_response([])
        backend = GitHubActionsBackend("token", http)

        # Dispatch once so the record exists, then reconcile the same key.
        with bind_call_identity("s1", "r1", "key-hit"):
            await backend.trigger_workflow("owner", "repo", "ci.yml", "main", {})

        evidence = dispatch_reconciler.reconcile("trigger_workflow", "key-hit", {})
        assert evidence.outcome == "evidence_found"
        assert re.fullmatch(r"[0-9a-f]{64}", evidence.digest)

    def test_record_miss_returns_unverifiable(self) -> None:
        # No record for the key: the process restarted, so the lookup cannot answer.
        evidence = dispatch_reconciler.reconcile("trigger_workflow", "key-unknown", {})
        assert evidence.outcome == "unverifiable"

    def test_recorded_but_not_attempted_returns_no_evidence(self) -> None:
        # The record exists but the dispatch POST was never issued.
        record = backend_module.CorrelationRecord(
            workflow="ci.yml",
            ref="main",
            actor="s1",
            dispatch_time=_iso_now(),
            attempted=False,
        )
        backend_module._CORRELATION["key-not-attempted"] = record
        evidence = dispatch_reconciler.reconcile(
            "trigger_workflow", "key-not-attempted", {}
        )
        assert evidence.outcome == "no_evidence"

    @pytest.mark.asyncio
    async def test_multiple_candidates_recorded_returns_ambiguous(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _fast_polling(monkeypatch)
        created = _future_iso()
        http = AsyncMock()
        http.post.return_value = _post_response(204)
        # First call polls with no run yet; the repeat's pre-dispatch search finds two.
        repeat = {"on": False}
        http.get.side_effect = lambda *_a, **_kw: _runs_response(
            [_run(1, created), _run(2, created)] if repeat["on"] else []
        )
        backend = GitHubActionsBackend("token", http)

        with bind_call_identity("s1", "r1", "key-amb-a"):
            await backend.trigger_workflow("owner", "repo", "ci.yml", "main", {})
        repeat["on"] = True
        with bind_call_identity("s1", "r2", "key-amb-b"):
            outcome = await backend.trigger_workflow(
                "owner", "repo", "ci.yml", "main", {}
            )
        assert outcome.state == "reconciliation_required"

        evidence = dispatch_reconciler.reconcile("trigger_workflow", "key-amb-b", {})
        assert evidence.outcome == "ambiguous"


class TestTriggerWorkflowUrlPathSegment:
    """The workflow value is quoted as one path segment (REQ-005, AC-4)."""

    def _backend(self, monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
        _fast_polling(monkeypatch)
        http = AsyncMock()
        http.post.return_value = _post_response(204)
        http.get.return_value = _runs_response([])
        return http

    @staticmethod
    def _segment(http: AsyncMock) -> str:
        """Return the workflow segment of the URL the backend posted."""
        url = http.post.call_args.args[0]
        return url.rsplit("/dispatches", 1)[0].rsplit("/", 1)[1]

    @pytest.mark.asyncio
    async def test_canonical_name_encodes_unchanged(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        http = self._backend(monkeypatch)
        backend = GitHubActionsBackend("token", http)

        await backend.trigger_workflow("owner", "repo", "ci.yml", "main", {})

        assert self._segment(http) == "ci.yml"

    @pytest.mark.asyncio
    async def test_separator_cannot_add_a_path_segment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        http = self._backend(monkeypatch)
        backend = GitHubActionsBackend("token", http)

        await backend.trigger_workflow("owner", "repo", "../ci.yml", "main", {})

        assert self._segment(http) == "..%2Fci.yml"
        # The path keeps the seven segments the canonical value produces.
        url = http.post.call_args.args[0]
        assert url == (
            f"{_GITHUB_API_BASE}/repos/owner/repo/actions/workflows/..%2Fci.yml/dispatches"
        )

    @pytest.mark.asyncio
    async def test_percent_encoding_is_not_reinterpreted(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        http = self._backend(monkeypatch)
        backend = GitHubActionsBackend("token", http)

        await backend.trigger_workflow("owner", "repo", "ci%2Eyml", "main", {})

        assert self._segment(http) == "ci%252Eyml"
