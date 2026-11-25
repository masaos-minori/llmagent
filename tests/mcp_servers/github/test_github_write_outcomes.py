"""tests/mcp_servers/github/test_github_write_outcomes.py

Tests for the GitHub write outcomes (mcpai006 REQ-002..REQ-006, REQ-009):
the call-identity binding, the intent audit (fail closed before any API call),
the completion audit that reports applied_audit_failed after the write landed,
the ambiguous-transport-failure translation and its no-retry rule, the durable
store failure refusal, the audit-record identifier contract with no payload
text, and the no-retry client construction with the configured timeouts.
Reads keep their existing behavior.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import mcp_servers.dispatch as dispatch
import pytest
from fastapi.testclient import TestClient
from github import GithubException
from mcp_servers.dispatch import _duplicate_cache, dispatch_tool
from mcp_servers.execution_context import ExecutionContext
from mcp_servers.github import github_server, github_service_init
from mcp_servers.github.github_models_config import (
    GitHubAppliedAuditError,
    GitHubAuditError,
    GitHubConfig,
    GitHubOutcomeUnknownError,
    GitHubUpstreamError,
)
from mcp_servers.github.github_service_dispatch import GitHubService
from mcp_servers.github.github_service_security import bind_call_identity
from shared.mcp_dedup import DedupStore, DedupStoreConfig
from shared.tool_constants import GITHUB_DANGEROUS_TOOLS, GITHUB_WRITE_TOOLS

from tests.mcp_servers._auth_headers import MCP_TEST_AUTH_HEADERS


def _make_service(audit_log_path: str = "") -> GitHubService:
    """Minimal GitHubService instance; the GitHub API is never called."""
    return GitHubService(
        gh=MagicMock(),
        cfg=GitHubConfig.from_dict(
            {"allowed_repos": ["org/repo"], "audit_log_path": audit_log_path}
        ),
    )


def _ctx(key: str) -> ExecutionContext:
    """An applied context carrying the identifiers the audit records must name."""
    return ExecutionContext(
        request_id="r1",
        session_id="s1",
        idempotency_key=key,
        execution_mode="applied",
    )


def _fake_issue() -> SimpleNamespace:
    """A PyGithub-shaped issue the mapper can convert."""
    now = datetime(2026, 11, 25, tzinfo=UTC)
    return SimpleNamespace(
        number=1,
        title="t",
        state="open",
        html_url="https://example.invalid/issue",
        body=None,
        created_at=now,
        updated_at=now,
        labels=[],
        assignees=[],
    )


@pytest.fixture()
def durable_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[DedupStore]:
    """Inject a per-test durable dedup store through the dispatcher seam.

    Injection style copied locally from tests/mcp_servers/test_mcp_dispatch_concurrency.py.
    The declared retry policies come from the autouse bootstrap fixture, so every
    GitHub write is non-retryable ('never').
    """
    import mcp_servers.dispatch as dispatch_mod

    db_path = str(tmp_path / "mcp_dedup.sqlite")
    store = DedupStore(db_path)
    config = DedupStoreConfig(
        db_path=db_path,
        retention_days=14,
        pending_timeout_minutes=10,
    )
    _duplicate_cache.clear()
    monkeypatch.setattr(dispatch_mod, "_dedup_store", store)
    monkeypatch.setattr(dispatch_mod, "_dedup_config", config)
    monkeypatch.setattr(dispatch_mod, "_dedup_disabled", False)
    monkeypatch.setattr(dispatch_mod, "_dedup_start_state", None)
    monkeypatch.setattr(dispatch_mod, "_purge_done", False)
    yield store
    store.close()
    _duplicate_cache.clear()


class TestCallIdentity:
    def test_default_identity_is_empty(self) -> None:
        from mcp_servers.github.github_service_security import _CALL_IDENTITY

        assert _CALL_IDENTITY.get() == ("", "", "")

    def test_bind_sets_and_resets_the_identity(self) -> None:
        from mcp_servers.github.github_service_security import _CALL_IDENTITY

        with bind_call_identity("s1", "r1", "c1"):
            assert _CALL_IDENTITY.get() == ("s1", "r1", "c1")
        assert _CALL_IDENTITY.get() == ("", "", "")


class TestIntentAudit:
    def test_intent_record_carries_phase_and_identifiers(self, tmp_path: Path) -> None:
        audit_path = tmp_path / "audit.log"
        svc = _make_service(str(audit_path))
        with bind_call_identity("s1", "r1", "c1"):
            svc._write_intent_audit("create_issue", repo="org/repo")
        record = audit_path.read_text(encoding="utf-8")
        assert "op=create_issue phase=intent session=s1 request=r1 call=c1" in record
        assert "repo='org/repo'" in record

    def test_failure_propagates_before_anything_is_applied(
        self, tmp_path: Path
    ) -> None:
        bad_path = str(tmp_path / "nonexistent" / "audit.log")
        svc = _make_service(bad_path)
        with pytest.raises(GitHubAuditError):
            svc._write_intent_audit("create_issue", repo="org/repo")
        assert svc.audit_failure_count == 0

    def test_empty_audit_path_skips_both_phases(self, tmp_path: Path) -> None:
        svc = _make_service("")
        svc._write_intent_audit("create_issue", repo="org/repo")
        svc._complete_write_audit("create_issue", repo="org/repo")
        assert not (tmp_path / "audit.log").exists()
        assert svc.audit_failure_count == 0

    @pytest.mark.asyncio
    async def test_unwritable_audit_path_refuses_before_the_api_call(
        self, tmp_path: Path
    ) -> None:
        """A denied audit path fails the call before anything is applied."""
        svc = _make_service(str(tmp_path / "nonexistent" / "audit.log"))
        with pytest.raises(GitHubAuditError):
            await svc.fmt_create_issue(
                {"owner": "org", "repo": "repo", "title": "t", "body": "SECRET-BODY"}
            )
        svc._gh.get_repo.assert_not_called()


class TestCompletionAudit:
    def test_completion_record_carries_phase_and_identifiers(
        self, tmp_path: Path
    ) -> None:
        audit_path = tmp_path / "audit.log"
        svc = _make_service(str(audit_path))
        with bind_call_identity("s2", "r2", "c2"):
            svc._complete_write_audit("merge_pull_request", repo="org/repo")
        record = audit_path.read_text(encoding="utf-8")
        assert (
            "op=merge_pull_request phase=completion session=s2 request=r2 call=c2"
            in record
        )

    def test_failure_reports_applied_audit_failed_and_counts(
        self, tmp_path: Path
    ) -> None:
        bad_path = str(tmp_path / "nonexistent" / "audit.log")
        svc = _make_service(bad_path)
        with pytest.raises(
            GitHubAppliedAuditError, match="applied_audit_failed"
        ) as exc:
            svc._complete_write_audit("push_files", repo="org/repo")
        assert svc.audit_failure_count == 1
        assert exc.value.__cause__ is not None
        assert isinstance(exc.value.__cause__, GitHubAuditError)
        assert issubclass(GitHubAppliedAuditError, GitHubAuditError)


class TestWriteOutcomeTranslation:
    @pytest.mark.asyncio
    async def test_write_timeout_becomes_outcome_unknown(self) -> None:
        svc = _make_service()

        def boom() -> None:
            raise TimeoutError("read timeout")

        with pytest.raises(GitHubOutcomeUnknownError, match="outcome_unknown"):
            await svc._run_github(boom, write=True)

    @pytest.mark.asyncio
    async def test_write_connection_error_becomes_outcome_unknown(self) -> None:
        svc = _make_service()

        def boom() -> None:
            raise ConnectionError("connection reset after send")

        with pytest.raises(GitHubOutcomeUnknownError, match="outcome_unknown"):
            await svc._run_github(boom, write=True)

    @pytest.mark.asyncio
    async def test_write_5xx_github_exception_becomes_outcome_unknown(self) -> None:
        svc = _make_service()

        def boom() -> None:
            raise GithubException(502, {"message": "bad gateway"}, None)

        with pytest.raises(GitHubOutcomeUnknownError, match="outcome_unknown"):
            await svc._run_github(boom, write=True)

    @pytest.mark.asyncio
    async def test_write_definite_4xx_keeps_its_mapping(self) -> None:
        from mcp_servers.github.github_models_config import GitHubNotFoundError

        svc = _make_service()

        def boom() -> None:
            raise GithubException(404, {"message": "not found"}, None)

        with pytest.raises(GitHubNotFoundError):
            await svc._run_github(boom, write=True)

    @pytest.mark.asyncio
    async def test_read_timeout_is_not_translated(self) -> None:
        svc = _make_service()

        def boom() -> None:
            raise TimeoutError("read timeout")

        with pytest.raises(TimeoutError):
            await svc._run_github(boom)

    @pytest.mark.asyncio
    async def test_read_5xx_keeps_the_upstream_mapping(self) -> None:
        svc = _make_service()

        def boom() -> None:
            raise GithubException(500, {"message": "server error"}, None)

        with pytest.raises(GitHubUpstreamError):
            await svc._run_github(boom)

    @pytest.mark.asyncio
    async def test_write_success_path_is_unchanged(self) -> None:
        svc = _make_service()
        assert await svc._run_github(lambda: "ok", write=True) == "ok"


class TestStoreFailureRefusal:
    """With the durable store unavailable every GitHub write fails closed: the
    dispatcher refuses the call before the handler, so the API stub is never
    called (declared policy 'never' -> non-retryable)."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "tool_name", sorted(GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS)
    )
    async def test_store_failure_refuses_without_calling_the_api(
        self,
        tool_name: str,
        durable_store: DedupStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def _boom(*args: Any, **kwargs: Any) -> None:
            raise sqlite3.OperationalError("disk is locked")

        monkeypatch.setattr(durable_store, "try_acquire_execution", _boom)
        handler = AsyncMock(return_value="ok")
        result = await dispatch_tool(
            {tool_name: handler}, tool_name, {"p": "a"}, context=_ctx("k1")
        )
        assert result.is_error
        assert result.error_type == "dedup_store_error"
        handler.assert_not_awaited()


class TestNoRetryAfterAmbiguousOutcome:
    @pytest.mark.asyncio
    async def test_second_dispatch_with_the_same_key_does_not_call_the_api(
        self, durable_store: DedupStore
    ) -> None:
        """A timed-out write leaves a terminal failed row; the same logical call
        is refused for replay, so the API is called exactly once."""
        calls: list[int] = []

        async def handler(args: dict[str, Any]) -> str:
            calls.append(1)
            raise GitHubOutcomeUnknownError("read timeout: outcome_unknown")

        with pytest.raises(GitHubOutcomeUnknownError):
            await dispatch_tool(
                {"github_create_issue": handler},
                "github_create_issue",
                {"p": "a"},
                context=_ctx("k1"),
            )
        result = await dispatch_tool(
            {"github_create_issue": handler},
            "github_create_issue",
            {"p": "a"},
            context=_ctx("k1"),
        )
        assert result.is_error
        assert result.error_type == "dedup_unreplayable"
        assert result.dedup_state == "replay_unavailable"
        assert len(calls) == 1


class TestAppliedAuditFailureViaApi:
    """The API stub succeeds and the completion audit fails: the dispatch result
    is applied_audit_failed, says the write was applied, and the counter
    increments."""

    def _failing_completion_service(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> GitHubService:
        """Intent audit succeeds; the completion audit raises."""
        svc = _make_service("")

        def _audit(op: str, **kwargs: Any) -> None:
            if kwargs.get("phase") == "completion":
                raise GitHubAuditError("audit log write failed")

        monkeypatch.setattr(svc, "_write_github_audit_log", _audit)
        return svc

    async def _run_applied_case(
        self,
        monkeypatch: pytest.MonkeyPatch,
        svc: GitHubService,
        tool_name: str,
        args: dict[str, Any],
        applied_call: Any,
    ) -> None:
        monkeypatch.setattr(github_server, "_service", svc)
        result = await github_server._dispatch_github_tool(
            tool_name, args, context=_ctx(f"applied-{tool_name}")
        )
        assert result.is_error
        assert result.error_type == "applied_audit_failed"
        assert "The write was applied" in result.output
        assert "do not retry" in result.output
        assert svc.audit_failure_count == 1
        applied_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_issue(self, monkeypatch: pytest.MonkeyPatch) -> None:
        svc = self._failing_completion_service(monkeypatch)
        repo = svc._gh.get_repo.return_value
        repo.create_issue.return_value = _fake_issue()
        await self._run_applied_case(
            monkeypatch,
            svc,
            "github_create_issue",
            {"owner": "org", "repo": "repo", "title": "t"},
            repo.create_issue,
        )

    @pytest.mark.asyncio
    async def test_add_issue_comment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        svc = self._failing_completion_service(monkeypatch)
        repo = svc._gh.get_repo.return_value
        comment = SimpleNamespace(html_url="https://example.invalid/comment")
        repo.get_issue.return_value.create_comment.return_value = comment
        await self._run_applied_case(
            monkeypatch,
            svc,
            "github_add_issue_comment",
            {"owner": "org", "repo": "repo", "issue_number": 1, "body": "b"},
            repo.get_issue.return_value.create_comment,
        )

    @pytest.mark.asyncio
    async def test_merge_pull_request(self, monkeypatch: pytest.MonkeyPatch) -> None:
        svc = self._failing_completion_service(monkeypatch)
        repo = svc._gh.get_repo.return_value
        pr = repo.get_pull.return_value
        pr.base.ref = "dev"
        pr.get_reviews.return_value = [SimpleNamespace(state="APPROVED")]
        pr.merge.return_value = SimpleNamespace(
            merged=True, sha="0123456789abcdef", message="ok"
        )
        await self._run_applied_case(
            monkeypatch,
            svc,
            "github_merge_pull_request",
            {"owner": "org", "repo": "repo", "pr_number": 2},
            pr.merge,
        )

    @pytest.mark.asyncio
    async def test_create_or_update_file(self, monkeypatch: pytest.MonkeyPatch) -> None:
        svc = self._failing_completion_service(monkeypatch)
        repo = svc._gh.get_repo.return_value
        repo.create_file.return_value = {
            "commit": SimpleNamespace(sha="0123456789abcdef")
        }
        await self._run_applied_case(
            monkeypatch,
            svc,
            "github_create_or_update_file",
            {
                "owner": "org",
                "repo": "repo",
                "path": "f.txt",
                "content": "c",
                "message": "m",
            },
            repo.create_file,
        )


class TestAuditIdentifiersNoPayload:
    @pytest.mark.asyncio
    async def test_records_carry_the_ids_and_no_payload_text(
        self, tmp_path: Path
    ) -> None:
        audit_path = tmp_path / "audit.log"
        svc = _make_service(str(audit_path))
        repo = svc._gh.get_repo.return_value
        repo.create_issue.return_value = _fake_issue()
        repo.get_issue.return_value.create_comment.return_value = SimpleNamespace(
            html_url="https://example.invalid/comment"
        )
        with bind_call_identity("s9", "r9", "c9"):
            await svc.fmt_create_issue(
                {"owner": "org", "repo": "repo", "title": "t", "body": "SECRET-BODY"}
            )
            await svc.fmt_add_issue_comment(
                {
                    "owner": "org",
                    "repo": "repo",
                    "issue_number": 1,
                    "body": "SECRET-COMMENT",
                }
            )
        record = audit_path.read_text(encoding="utf-8")
        lines = record.splitlines()
        assert len(lines) == 4
        for line in lines:
            assert "session=s9 request=r9 call=c9" in line
        assert "SECRET-BODY" not in record
        assert "SECRET-COMMENT" not in record


class TestClientConstructionAndHealthCounter:
    def test_build_client_disables_retry_and_applies_the_timeout_tuple(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured: dict[str, Any] = {}

        def fake_github(*args: Any, **kwargs: Any) -> Any:
            captured.update(kwargs)
            return MagicMock()

        monkeypatch.setattr(github_service_init, "Github", fake_github)
        gh = github_service_init.build_client("tok", 5, 30)
        assert captured["retry"] is None
        # PyGithub asserts isinstance(timeout, int), so the (connect, read)
        # tuple is applied afterwards on the requester's private timeout.
        assert getattr(gh.requester, "_Requester__timeout") == (5, 30)

    def test_health_reports_the_audit_failure_count(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        svc = _make_service("")
        svc.audit_failure_count = 2
        monkeypatch.setattr(github_server, "_service", svc)
        monkeypatch.setattr(github_server, "_GITHUB_TOKEN", "fake-token")
        monkeypatch.setattr(dispatch, "_dedup_store", None)
        monkeypatch.setattr(dispatch, "_dedup_config", None)
        client = TestClient(github_server.app, headers=MCP_TEST_AUTH_HEADERS)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["details"]["audit_failure_count"] == 2
