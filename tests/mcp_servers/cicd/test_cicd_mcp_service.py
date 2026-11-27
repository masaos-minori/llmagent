"""tests/test_cicd_mcp_service.py
Unit tests for mcp/cicd/service.py: CiCdService guards and GitHubActionsBackend.

The guard tests compare canonical values, and the handler tests pin that each handler
canonicalizes at entry so the guard and the backend receive the same value (REQ-005, AC-4).
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import orjson
import pytest
from mcp_servers.bounded_fetch import TRUNCATED_BY_RAW, BoundedFetchResult
from mcp_servers.cicd import cicd_service_github_actions as backend_module
from mcp_servers.cicd import cicd_service_github_actions_job as job_module
from mcp_servers.cicd.cicd_models import (
    CicdAuthorizationError,
    CicdConfig,
    CicdNotFoundError,
    CicdUpstreamError,
    CicdValidationError,
    DispatchOutcome,
    LogFetchResult,
    LogJobResult,
    LogTotals,
)
from mcp_servers.cicd.cicd_service import CiCdService, GitHubActionsBackend
from mcp_servers.cicd.cicd_service_github_actions_job import GitHubActionsJobBackend
from pydantic import ValidationError

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _no_runs_found(http: AsyncMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the bounded polling fast: the run lookup finds nothing inside the window."""
    monkeypatch.setattr(backend_module, "POLL_TIMEOUT_S", 0.05)
    monkeypatch.setattr(backend_module, "POLL_INTERVAL_S", 0.01)
    http.get.return_value = _make_http_response(200, {"workflow_runs": []})


def _make_http_response(
    status_code: int, body: Any = None, text: str = ""
) -> MagicMock:
    """Build a mock httpx.Response with the given status code and JSON body."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.is_success = 200 <= status_code < 300
    if body is not None:
        resp.content = orjson.dumps(body)
        resp.json.return_value = body
    else:
        resp.content = b""
    resp.text = text
    resp.headers = {}
    return resp


def _fetch_result(body: bytes, truncated_by: str | None = None) -> BoundedFetchResult:
    """Build the bounded-helper result the job backend receives for one job log."""
    return BoundedFetchResult(
        final_url="https://api.github.com/repos/owner/repo/actions/jobs/1/logs",
        status_code=200,
        content_type="text/plain",
        charset=None,
        body=body,
        download_truncated=truncated_by is not None,
        truncated_by=truncated_by,
        declared_length=len(body),
        elapsed_sec=0.0,
    )


def _make_service(
    repo_allowlist: list[str] | None = None,
    workflow_allowlist: list[str] | None = None,
    backend: Any = None,
) -> CiCdService:
    cfg = CicdConfig(
        repo_allowlist=repo_allowlist if repo_allowlist is not None else [],
        # Default to ["ci.yml"] so tests that don't exercise workflow allowlist logic
        # still pass through the fail-closed guard. Pass workflow_allowlist=[] explicitly
        # to test the deny-all behavior.
        workflow_allowlist=workflow_allowlist
        if workflow_allowlist is not None
        else ["ci.yml"],
        max_log_size_kb=256,
    )
    if backend is None:
        backend = AsyncMock()
    return CiCdService(cfg=cfg, backend=backend)


# ──────────────────────────────────────────────────────────────────────────────
# CiCdService — repo_allowlist guard
# ──────────────────────────────────────────────────────────────────────────────


class TestAssertAllowedRepo:
    def test_empty_allowlist_denies_all(self) -> None:
        svc = _make_service(repo_allowlist=[])
        with pytest.raises(CicdAuthorizationError) as exc_info:
            svc._assert_allowed_repo("owner/repo")
        assert "fail-closed" in str(exc_info.value)

    def test_repo_in_allowlist_passes(self) -> None:
        svc = _make_service(repo_allowlist=["owner/repo"])
        svc._assert_allowed_repo("owner/repo")  # must not raise

    def test_repo_not_in_allowlist_denied(self) -> None:
        svc = _make_service(repo_allowlist=["owner/allowed"])
        with pytest.raises(CicdAuthorizationError) as exc_info:
            svc._assert_allowed_repo("owner/other")
        assert "repo_allowlist" in str(exc_info.value)

    def test_empty_string_repo_is_denied(self) -> None:
        svc = _make_service(repo_allowlist=["owner/repo"])
        with pytest.raises(CicdAuthorizationError):
            svc._assert_allowed_repo("")

    def test_wildcard_in_allowlist_is_not_expanded(self) -> None:
        svc = _make_service(repo_allowlist=["owner/*"])
        with pytest.raises(CicdAuthorizationError):
            svc._assert_allowed_repo("owner/repo")

    def test_extra_slash_suffix_is_denied(self) -> None:
        svc = _make_service(repo_allowlist=["owner/repo"])
        with pytest.raises(CicdAuthorizationError):
            svc._assert_allowed_repo("owner/repo/extra")

    def test_double_slash_is_denied(self) -> None:
        svc = _make_service(repo_allowlist=["owner/repo"])
        with pytest.raises(CicdAuthorizationError):
            svc._assert_allowed_repo("owner//repo")

    def test_global_wildcard_does_not_match_any_repo(self) -> None:
        svc = _make_service(repo_allowlist=["*"])
        with pytest.raises(CicdAuthorizationError):
            svc._assert_allowed_repo("owner/repo")

    def test_prefix_wildcard_does_not_match_partial_name(self) -> None:
        svc = _make_service(repo_allowlist=["owner/rep*"])
        with pytest.raises(CicdAuthorizationError):
            svc._assert_allowed_repo("owner/repo")

    def test_mixed_list_with_wildcard_allows_exact_match_only(self) -> None:
        svc = _make_service(repo_allowlist=["owner/*", "org/repo"])
        svc._assert_allowed_repo("org/repo")  # must not raise
        with pytest.raises(CicdAuthorizationError):
            svc._assert_allowed_repo("owner/repo")

    def test_case_only_difference_matches_canonical_entry(self) -> None:
        """The request value and the entry are compared as canonical keys (AC-4)."""
        svc = _make_service(repo_allowlist=["Owner/Repo"])
        svc._assert_allowed_repo("owner/repo")  # must not raise

    def test_non_canonical_slug_is_denied(self) -> None:
        svc = _make_service(repo_allowlist=["owner/repo"])
        with pytest.raises(CicdAuthorizationError):
            svc._assert_allowed_repo("nodash")


# ──────────────────────────────────────────────────────────────────────────────
# CiCdService — workflow_allowlist guard
# ──────────────────────────────────────────────────────────────────────────────


class TestAssertAllowedWorkflow:
    def test_empty_allowlist_denies_all(self) -> None:
        svc = _make_service(repo_allowlist=["o/r"], workflow_allowlist=[])
        with pytest.raises(CicdAuthorizationError, match="workflow_allowlist is empty"):
            svc._assert_allowed_workflow("any_workflow.yml")

    def test_workflow_in_allowlist_passes(self) -> None:
        svc = _make_service(repo_allowlist=["o/r"], workflow_allowlist=["ci.yml"])
        svc._assert_allowed_workflow("ci.yml")  # must not raise

    def test_workflow_not_in_allowlist_denied(self) -> None:
        svc = _make_service(repo_allowlist=["o/r"], workflow_allowlist=["ci.yml"])
        with pytest.raises(CicdAuthorizationError) as exc_info:
            svc._assert_allowed_workflow("deploy.yml")
        assert "workflow_allowlist" in str(exc_info.value)

    def test_path_separator_workflow_is_rejected(self) -> None:
        svc = _make_service(repo_allowlist=["o/r"], workflow_allowlist=["ci.yml"])
        with pytest.raises(CicdAuthorizationError):
            svc._assert_allowed_workflow("../ci.yml")

    def test_backslash_separator_workflow_is_rejected(self) -> None:
        svc = _make_service(repo_allowlist=["o/r"], workflow_allowlist=["ci.yml"])
        with pytest.raises(CicdAuthorizationError):
            svc._assert_allowed_workflow("..\\ci.yml")

    def test_percent_encoding_is_rejected(self) -> None:
        svc = _make_service(repo_allowlist=["o/r"], workflow_allowlist=["ci.yml"])
        with pytest.raises(CicdAuthorizationError):
            svc._assert_allowed_workflow("ci%2Eyml")

    def test_blank_workflow_is_denied(self) -> None:
        svc = _make_service(repo_allowlist=["o/r"], workflow_allowlist=["ci.yml"])
        with pytest.raises(CicdAuthorizationError):
            svc._assert_allowed_workflow("   ")

    def test_numeric_id_matches_the_same_canonical_form(self) -> None:
        """A numeric id and a file name go through the same canonicalizer (AC-4)."""
        svc = _make_service(repo_allowlist=["o/r"], workflow_allowlist=["42"])
        svc._assert_allowed_workflow("42")  # must not raise

    def test_case_only_difference_matches_canonical_entry(self) -> None:
        svc = _make_service(repo_allowlist=["o/r"], workflow_allowlist=["CI.YML"])
        svc._assert_allowed_workflow("ci.yml")  # must not raise

    def test_duplicate_entries_match_once(self) -> None:
        svc = _make_service(
            repo_allowlist=["o/r"], workflow_allowlist=["ci.yml", "ci.yml"]
        )
        svc._assert_allowed_workflow("ci.yml")  # must not raise


# ──────────────────────────────────────────────────────────────────────────────
# Startup integration: shipped config → guard
# ──────────────────────────────────────────────────────────────────────────────


class TestStartupConfigIntegration:
    """Verify the committed cicd_mcp_server.toml drives allowed behavior end-to-end.

    Loads the real config via CicdConfig.load() (same path the server uses at
    startup) and asserts the shipped workflow_allowlist permits ci.yml.
    """

    def test_shipped_config_allows_ci_yml(self) -> None:
        cfg = CicdConfig.load()
        assert cfg.workflow_allowlist, (
            "workflow_allowlist must be non-empty (fail-closed mode)"
        )
        assert "ci.yml" in cfg.workflow_allowlist
        svc = CiCdService(cfg=cfg, backend=AsyncMock())
        svc._assert_allowed_workflow("ci.yml")  # must not raise


# ──────────────────────────────────────────────────────────────────────────────
# CiCdService — _parse_repo
# ──────────────────────────────────────────────────────────────────────────────


class TestParseRepo:
    def test_valid_slug_returns_owner_repo(self) -> None:
        owner, repo = CiCdService._parse_repo("myorg/myrepo")
        assert owner == "myorg"
        assert repo == "myrepo"

    def test_invalid_slug_raises_validation_error(self) -> None:
        with pytest.raises(CicdValidationError):
            CiCdService._parse_repo("nodash")


# ──────────────────────────────────────────────────────────────────────────────
# CiCdService — dispatch handlers delegate to backend after guards
# ──────────────────────────────────────────────────────────────────────────────


class TestHandleTriggerWorkflow:
    @pytest.mark.asyncio
    async def test_calls_backend_when_allowed(self) -> None:
        backend = AsyncMock()
        # The structured-state contract: the handler JSON-serializes the outcome (AC-2).
        backend.trigger_workflow.return_value = DispatchOutcome(
            state="confirmed", run_id=42
        )
        svc = _make_service(repo_allowlist=["owner/repo"], backend=backend)

        result = await svc.handle_trigger_workflow(
            {"repo": "owner/repo", "workflow": "ci.yml", "ref": "main"}
        )
        parsed = orjson.loads(result)
        assert parsed["state"] == "confirmed"
        assert parsed["run_id"] == 42
        backend.trigger_workflow.assert_awaited_once_with(
            "owner", "repo", "ci.yml", "main", {}
        )

    @pytest.mark.asyncio
    async def test_denied_repo_does_not_call_backend(self) -> None:
        backend = AsyncMock()
        svc = _make_service(repo_allowlist=[], backend=backend)

        with pytest.raises(CicdAuthorizationError):
            await svc.handle_trigger_workflow(
                {"repo": "owner/repo", "workflow": "ci.yml"}
            )
        backend.trigger_workflow.assert_not_awaited()


class TestHandleGetWorkflowRuns:
    @pytest.mark.asyncio
    async def test_calls_backend_when_allowed(self) -> None:
        backend = AsyncMock()
        backend.get_workflow_runs.return_value = '{"runs": []}'
        svc = _make_service(repo_allowlist=["owner/repo"], backend=backend)

        result = await svc.handle_get_workflow_runs(
            {"repo": "owner/repo", "workflow": "ci.yml", "limit": 5}
        )
        assert result == '{"runs": []}'
        backend.get_workflow_runs.assert_awaited_once_with("owner", "repo", "ci.yml", 5)


class TestHandleGetWorkflowStatus:
    @pytest.mark.asyncio
    async def test_calls_backend_when_allowed(self) -> None:
        backend = AsyncMock()
        backend.get_workflow_status.return_value = '{"id": 123}'
        svc = _make_service(repo_allowlist=["owner/repo"], backend=backend)

        result = await svc.handle_get_workflow_status(
            {"repo": "owner/repo", "run_id": 123}
        )
        assert result == '{"id": 123}'
        backend.get_workflow_status.assert_awaited_once_with("owner", "repo", 123)


class TestHandleGetWorkflowLogs:
    @pytest.mark.asyncio
    async def test_calls_backend_when_allowed(self) -> None:
        backend = AsyncMock()
        pinned = LogFetchResult(
            jobs=(LogJobResult(job_id=1, status="included", included_bytes=19),),
            output="=== Job: build ===\n",
            partial_success=False,
            totals=LogTotals(
                jobs=1,
                included_jobs=1,
                failed_jobs=0,
                downloaded_bytes=19,
                visible_bytes=19,
            ),
        )
        backend.get_workflow_logs.return_value = pinned
        svc = _make_service(repo_allowlist=["owner/repo"], backend=backend)

        result = await svc.handle_get_workflow_logs(
            {"repo": "owner/repo", "run_id": 456}
        )
        # REQ-004: the handler serializes the structured result, not a raw string.
        parsed = orjson.loads(result)
        assert parsed["jobs"][0]["status"] == "included"
        assert parsed["output"] == "=== Job: build ===\n"
        backend.get_workflow_logs.assert_awaited_once_with("owner", "repo", 456)

    @pytest.mark.asyncio
    async def test_mixed_failure_is_a_successful_result(self) -> None:
        backend = AsyncMock()
        backend.get_workflow_logs.return_value = LogFetchResult(
            jobs=(
                LogJobResult(job_id=1, status="included", included_bytes=23),
                LogJobResult(
                    job_id=2,
                    status="failed",
                    included_bytes=0,
                    error_code="http_status",
                ),
            ),
            output="=== Job: build ===\nlog\n",
            partial_success=True,
            totals=LogTotals(
                jobs=2,
                included_jobs=1,
                failed_jobs=1,
                downloaded_bytes=4,
                visible_bytes=23,
            ),
        )
        svc = _make_service(repo_allowlist=["owner/repo"], backend=backend)

        result = await svc.handle_get_workflow_logs(
            {"repo": "owner/repo", "run_id": 456}
        )
        parsed = orjson.loads(result)
        assert parsed["partial_success"] is True
        assert parsed["totals"]["failed_jobs"] == 1

    @pytest.mark.asyncio
    async def test_all_failed_raises_a_tool_error(self) -> None:
        """AC-4: total failure is an error, not a successful result with empty output."""
        backend = AsyncMock()
        backend.get_workflow_logs.return_value = LogFetchResult(
            jobs=(
                LogJobResult(
                    job_id=1,
                    status="failed",
                    included_bytes=0,
                    error_code="http_status",
                ),
            ),
            output="",
            partial_success=False,
            totals=LogTotals(
                jobs=1,
                included_jobs=0,
                failed_jobs=1,
                downloaded_bytes=0,
                visible_bytes=0,
            ),
        )
        svc = _make_service(repo_allowlist=["owner/repo"], backend=backend)

        with pytest.raises(CicdUpstreamError):
            await svc.handle_get_workflow_logs({"repo": "owner/repo", "run_id": 456})

    @pytest.mark.asyncio
    async def test_result_carries_no_raw_upstream_text(self) -> None:
        """REQ-006: the serialized result contains codes, not transport exception text."""
        output = "=== Job: build ===\nlog\n"
        backend = AsyncMock()
        backend.get_workflow_logs.return_value = LogFetchResult(
            jobs=(
                LogJobResult(job_id=1, status="included", included_bytes=23),
                LogJobResult(
                    job_id=2,
                    status="failed",
                    included_bytes=0,
                    error_code="content_type",
                ),
            ),
            output=output,
            partial_success=True,
            totals=LogTotals(
                jobs=2,
                included_jobs=1,
                failed_jobs=1,
                downloaded_bytes=4,
                visible_bytes=len(output.encode()),
            ),
        )
        svc = _make_service(repo_allowlist=["owner/repo"], backend=backend)

        result = await svc.handle_get_workflow_logs({"repo": "owner/repo", "run_id": 1})
        assert "log fetch error" not in result
        assert "text/html" not in result
        assert orjson.loads(result)["jobs"][1]["error_code"] == "content_type"


class TestHandlerCanonicalization:
    """The handler canonicalizes at entry, so the guard and the backend see one value (AC-4)."""

    @pytest.mark.asyncio
    async def test_trigger_receives_canonical_values(self) -> None:
        backend = AsyncMock()
        backend.trigger_workflow.return_value = DispatchOutcome(state="accepted")
        svc = _make_service(
            repo_allowlist=["Owner/Repo"],
            workflow_allowlist=["ci.yml"],
            backend=backend,
        )

        await svc.handle_trigger_workflow(
            {"repo": "Owner/Repo", "workflow": "CI.YML", "ref": "main"}
        )
        backend.trigger_workflow.assert_awaited_once_with(
            "owner", "repo", "ci.yml", "main", {}
        )

    @pytest.mark.asyncio
    async def test_numeric_id_reaches_the_backend_unchanged(self) -> None:
        backend = AsyncMock()
        backend.trigger_workflow.return_value = DispatchOutcome(state="accepted")
        svc = _make_service(
            repo_allowlist=["owner/repo"],
            workflow_allowlist=["42"],
            backend=backend,
        )

        await svc.handle_trigger_workflow({"repo": "owner/repo", "workflow": "42"})
        backend.trigger_workflow.assert_awaited_once_with(
            "owner", "repo", "42", "main", {}
        )

    @pytest.mark.asyncio
    async def test_read_handler_receives_canonical_repo_parts(self) -> None:
        backend = AsyncMock()
        backend.get_workflow_runs.return_value = '{"runs": []}'
        svc = _make_service(
            repo_allowlist=["Owner/Repo"],
            workflow_allowlist=["ci.yml"],
            backend=backend,
        )

        await svc.handle_get_workflow_runs(
            {"repo": "Owner/Repo", "workflow": "ci.yml", "limit": 5}
        )
        backend.get_workflow_runs.assert_awaited_once_with("owner", "repo", "ci.yml", 5)

    @pytest.mark.asyncio
    async def test_dry_run_preview_shows_canonical_values(self) -> None:
        import orjson

        backend = AsyncMock()
        svc = _make_service(
            repo_allowlist=["Owner/Repo"],
            workflow_allowlist=["ci.yml"],
            backend=backend,
        )
        result = await svc.handle_trigger_workflow(
            {"repo": "Owner/Repo", "workflow": "CI.YML", "dry_run": True}
        )
        payload = orjson.loads(result)
        assert payload["preview"] == (
            "Would trigger workflow 'ci.yml' on ref 'main' in repo 'owner/repo'"
        )
        backend.trigger_workflow.assert_not_called()

    @pytest.mark.asyncio
    async def test_rejected_form_is_denied_before_the_backend_call(self) -> None:
        """A value the canonicalizer rejects stays an authorization denial, as the guard denies it."""
        backend = AsyncMock()
        svc = _make_service(
            repo_allowlist=["owner/repo"],
            workflow_allowlist=["ci.yml"],
            backend=backend,
        )

        for workflow in ("../ci.yml", "..\\ci.yml", "ci%2Eyml", "*"):
            with pytest.raises(CicdAuthorizationError):
                await svc.handle_trigger_workflow(
                    {"repo": "owner/repo", "workflow": workflow}
                )
        backend.trigger_workflow.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalid_repo_form_is_denied_before_the_backend_call(self) -> None:
        backend = AsyncMock()
        svc = _make_service(
            repo_allowlist=["owner/repo"],
            workflow_allowlist=["ci.yml"],
            backend=backend,
        )

        for repo in ("nodash", "owner//repo", "owner/repo/extra"):
            with pytest.raises(CicdAuthorizationError):
                await svc.handle_trigger_workflow({"repo": repo, "workflow": "ci.yml"})
        backend.trigger_workflow.assert_not_called()

    @pytest.mark.asyncio
    async def test_blank_workflow_is_rejected_at_the_model(self) -> None:
        """The strict model's non-empty constraint rejects it before the guard runs."""
        backend = AsyncMock()
        svc = _make_service(
            repo_allowlist=["owner/repo"],
            workflow_allowlist=["ci.yml"],
            backend=backend,
        )

        with pytest.raises(ValidationError):
            await svc.handle_trigger_workflow({"repo": "owner/repo", "workflow": ""})
        backend.trigger_workflow.assert_not_called()


# ──────────────────────────────────────────────────────────────────────────────
# GitHubActionsBackend — _check_response
# ──────────────────────────────────────────────────────────────────────────────


class TestCheckResponse:
    def test_404_raises_not_found(self) -> None:
        backend = GitHubActionsBackend("token", MagicMock())
        resp = _make_http_response(404)
        with pytest.raises(CicdNotFoundError) as exc_info:
            backend._check_response(resp, "test context")
        assert "Not found" in str(exc_info.value)

    def test_403_rate_limit_includes_reset_time(self) -> None:
        backend = GitHubActionsBackend("token", MagicMock())
        resp = _make_http_response(
            403,
            body={"message": "API rate limit exceeded for ..."},
        )
        resp.headers = {"X-RateLimit-Reset": "1714000000"}
        with pytest.raises(CicdAuthorizationError) as exc_info:
            backend._check_response(resp, "test context")
        assert "rate limit" in str(exc_info.value).lower()
        assert "1714000000" in str(exc_info.value)

    def test_403_non_rate_limit_raises_auth_error(self) -> None:
        backend = GitHubActionsBackend("token", MagicMock())
        resp = _make_http_response(403, body={"message": "Forbidden"})
        resp.headers = {}
        with pytest.raises(CicdAuthorizationError) as exc_info:
            backend._check_response(resp, "test context")
        assert "Access denied" in str(exc_info.value)

    def test_422_raises_validation_error(self) -> None:
        backend = GitHubActionsBackend("token", MagicMock())
        resp = _make_http_response(422, body={"message": "No ref found for 'bad-ref'"})
        with pytest.raises(CicdValidationError) as exc_info:
            backend._check_response(resp, "test context")
        assert "Validation failed" in str(exc_info.value)

    def test_500_raises_not_found_error(self) -> None:
        backend = GitHubActionsBackend("token", MagicMock())
        resp = _make_http_response(500)
        with pytest.raises(CicdNotFoundError) as exc_info:
            backend._check_response(resp, "test context")
        assert "GitHub API error" in str(exc_info.value)

    def test_200_does_not_raise(self) -> None:
        backend = GitHubActionsBackend("token", MagicMock())
        resp = _make_http_response(200, body={"id": 1})
        backend._check_response(resp, "test context")  # must not raise


# ──────────────────────────────────────────────────────────────────────────────
# GitHubActionsBackend — trigger_workflow
# ──────────────────────────────────────────────────────────────────────────────


class TestGitHubActionsBackendTriggerWorkflow:
    @pytest.mark.asyncio
    async def test_204_returns_structured_outcome(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        http = AsyncMock()
        http.post.return_value = _make_http_response(204)
        # No run is found inside the bounded window, so the state stays unconfirmed.
        _no_runs_found(http, monkeypatch)
        backend = GitHubActionsBackend("token", http)

        result = await backend.trigger_workflow("owner", "repo", "ci.yml", "main", {})
        assert result.state == "accepted_unconfirmed"
        assert result.workflow == "ci.yml"
        assert result.ref == "main"

    @pytest.mark.asyncio
    async def test_404_raises_not_found(self) -> None:
        http = AsyncMock()
        http.post.return_value = _make_http_response(404)
        backend = GitHubActionsBackend("token", http)

        with pytest.raises(CicdNotFoundError):
            await backend.trigger_workflow("owner", "repo", "ci.yml", "main", {})

    @pytest.mark.asyncio
    async def test_request_uses_correct_url(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        http = AsyncMock()
        http.post.return_value = _make_http_response(204)
        # The bounded polling path reads the run list; no run is found.
        _no_runs_found(http, monkeypatch)
        backend = GitHubActionsBackend("token", http)

        await backend.trigger_workflow("owner", "repo", "ci.yml", "main", {})
        call_url = http.post.call_args[0][0]
        assert "owner/repo/actions/workflows/ci.yml/dispatches" in call_url

    @pytest.mark.asyncio
    async def test_auth_header_is_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        http = AsyncMock()
        http.post.return_value = _make_http_response(204)
        _no_runs_found(http, monkeypatch)
        backend = GitHubActionsBackend("my-secret-token", http)

        await backend.trigger_workflow("owner", "repo", "ci.yml", "main", {})
        call_kwargs = http.post.call_args[1]
        headers = call_kwargs.get("headers", {})
        assert headers.get("Authorization") == "Bearer my-secret-token"

    @pytest.mark.asyncio
    async def test_no_token_omits_auth_header(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        http = AsyncMock()
        http.post.return_value = _make_http_response(204)
        _no_runs_found(http, monkeypatch)
        backend = GitHubActionsBackend("", http)

        await backend.trigger_workflow("owner", "repo", "ci.yml", "main", {})
        call_kwargs = http.post.call_args[1]
        headers = call_kwargs.get("headers", {})
        assert "Authorization" not in headers


# ──────────────────────────────────────────────────────────────────────────────
# GitHubActionsBackend — get_workflow_runs
# ──────────────────────────────────────────────────────────────────────────────


class TestGitHubActionsBackendGetWorkflowRuns:
    @pytest.mark.asyncio
    async def test_returns_formatted_runs(self) -> None:
        runs_body = {
            "total_count": 1,
            "workflow_runs": [
                {
                    "id": 12345,
                    "name": "CI",
                    "status": "completed",
                    "conclusion": "success",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:05:00Z",
                    "html_url": "https://github.com/owner/repo/actions/runs/12345",
                    "head_branch": "main",
                    "head_sha": "abc12345def",
                }
            ],
        }
        http = AsyncMock()
        http.get.return_value = _make_http_response(200, body=runs_body)
        backend = GitHubActionsBackend("token", http)

        result = await backend.get_workflow_runs("owner", "repo", "ci.yml", 10)
        data = orjson.loads(result)
        assert data["repo"] == "owner/repo"
        assert len(data["runs"]) == 1
        assert data["runs"][0]["id"] == 12345
        assert data["runs"][0]["head_sha"] == "abc12345"  # truncated to 8 chars

    @pytest.mark.asyncio
    async def test_limit_passed_as_per_page(self) -> None:
        http = AsyncMock()
        http.get.return_value = _make_http_response(
            200, body={"total_count": 0, "workflow_runs": []}
        )
        backend = GitHubActionsBackend("token", http)

        await backend.get_workflow_runs("owner", "repo", "ci.yml", 7)
        call_kwargs = http.get.call_args[1]
        assert call_kwargs["params"]["per_page"] == 7


# ──────────────────────────────────────────────────────────────────────────────
# GitHubActionsBackend — get_workflow_status
# ──────────────────────────────────────────────────────────────────────────────


class TestGitHubActionsBackendGetWorkflowStatus:
    @pytest.mark.asyncio
    async def test_returns_run_details(self) -> None:
        run_body = {
            "id": 99999,
            "name": "CI",
            "status": "completed",
            "conclusion": "failure",
            "workflow_id": 42,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:10:00Z",
            "run_started_at": "2024-01-01T00:00:05Z",
            "html_url": "https://github.com/owner/repo/actions/runs/99999",
            "head_branch": "feature",
            "head_sha": "deadbeefcafe",
            "event": "push",
            "run_attempt": 1,
        }
        http = AsyncMock()
        http.get.return_value = _make_http_response(200, body=run_body)
        backend = GitHubActionsBackend("token", http)

        result = await backend.get_workflow_status("owner", "repo", 99999)
        data = orjson.loads(result)
        assert data["id"] == 99999
        assert data["conclusion"] == "failure"
        assert data["head_sha"] == "deadbeef"  # truncated to 8


# ──────────────────────────────────────────────────────────────────────────────
# GitHubActionsBackend — get_workflow_logs (truncation)
# ──────────────────────────────────────────────────────────────────────────────


class TestGitHubActionsJobBackendGetWorkflowLogs:
    @pytest.mark.asyncio
    async def test_returns_job_header_and_log(self, monkeypatch) -> None:
        jobs_body = {
            "jobs": [
                {
                    "id": 111,
                    "name": "build",
                    "status": "completed",
                    "conclusion": "success",
                    "steps": [
                        {
                            "number": 1,
                            "name": "Set up job",
                            "status": "completed",
                            "conclusion": "success",
                        }
                    ],
                }
            ]
        }
        # Only the jobs API call uses the injected client; the log download goes
        # through the shared bounded helper.
        http = AsyncMock()
        http.get.return_value = _make_http_response(200, body=jobs_body)
        backend = GitHubActionsJobBackend("token", http)
        monkeypatch.setattr(
            job_module,
            "fetch_bounded",
            AsyncMock(
                return_value=_fetch_result(b"2024-01-01T00:00:00.000Z Run tests\n")
            ),
        )

        result = await backend.get_workflow_logs("owner", "repo", 42)
        assert "build" in result.output
        assert "Set up job" in result.output
        assert "Run tests" in result.output
        assert result.jobs[0].status == "included"

    @pytest.mark.asyncio
    async def test_truncates_at_max_log_size(self, monkeypatch) -> None:
        jobs_body = {
            "jobs": [
                {
                    "id": 222,
                    "name": "big-job",
                    "status": "completed",
                    "conclusion": "success",
                    "steps": [],
                }
            ]
        }
        # 1 KB limit, generate 2 KB of log text
        large_log = "x" * 2048
        http = AsyncMock()
        http.get.return_value = _make_http_response(200, body=jobs_body)
        backend = GitHubActionsJobBackend("token", http, 1)
        monkeypatch.setattr(
            job_module,
            "fetch_bounded",
            AsyncMock(return_value=_fetch_result(large_log.encode(), TRUNCATED_BY_RAW)),
        )

        result = await backend.get_workflow_logs("owner", "repo", 43)
        # REQ-003: the exact final-output budget, header and marker included.
        assert len(result.output.encode()) <= 1024
        assert "TRUNCATED" in result.output
        assert result.totals.visible_bytes == len(result.output.encode())
        assert result.jobs[0].truncated is True

    @pytest.mark.asyncio
    async def test_no_jobs_returns_empty_message(self) -> None:
        http = AsyncMock()
        http.get.return_value = _make_http_response(200, body={"jobs": []})
        backend = GitHubActionsJobBackend("token", http)

        result = await backend.get_workflow_logs("owner", "repo", 99)
        assert "No jobs found" in result.output
        assert result.totals.jobs == 0


# ──────────────────────────────────────────────────────────────────────────────
# GitHubActionsBackend — __repr__ token masking (R-4)
# ──────────────────────────────────────────────────────────────────────────────


class TestTriggerWorkflowDryRun:
    @pytest.mark.asyncio
    async def test_dry_run_returns_preview_without_calling_backend(self) -> None:
        import orjson

        mock_backend = AsyncMock()
        svc = _make_service(repo_allowlist=["owner/repo"], backend=mock_backend)
        result = await svc.handle_trigger_workflow(
            {"repo": "owner/repo", "workflow": "ci.yml", "dry_run": True}
        )
        payload = orjson.loads(result)
        assert payload["dry_run"] is True
        assert "Would trigger" in payload["preview"]
        assert "ci.yml" in payload["preview"]
        mock_backend.trigger_workflow.assert_not_called()

    @pytest.mark.asyncio
    async def test_dry_run_preview_redacts_input_values(self) -> None:
        """REQ-006, AC-4: the preview lists input keys and the count, never a value."""
        import orjson

        svc = _make_service(
            repo_allowlist=["owner/repo"], workflow_allowlist=["deploy.yml"]
        )
        result = await svc.handle_trigger_workflow(
            {
                "repo": "owner/repo",
                "workflow": "deploy.yml",
                "dry_run": True,
                "inputs": {"env": "prod"},
            }
        )
        payload = orjson.loads(result)
        assert "prod" not in payload["preview"]
        assert "env" in payload["preview"]
        assert "[1]" in payload["preview"]

    @pytest.mark.asyncio
    async def test_dry_run_preview_lists_multiple_keys_and_count(self) -> None:
        import orjson

        svc = _make_service(
            repo_allowlist=["owner/repo"], workflow_allowlist=["deploy.yml"]
        )
        result = await svc.handle_trigger_workflow(
            {
                "repo": "owner/repo",
                "workflow": "deploy.yml",
                "dry_run": True,
                "inputs": {"env": "prod", "tag": "v1"},
            }
        )
        payload = orjson.loads(result)
        assert "prod" not in payload["preview"]
        assert "v1" not in payload["preview"]
        assert "inputs [2]: env, tag" in payload["preview"]

    @pytest.mark.asyncio
    async def test_dry_run_denied_by_repo_allowlist(self) -> None:
        svc = _make_service(repo_allowlist=[])
        with pytest.raises(CicdAuthorizationError):
            await svc.handle_trigger_workflow(
                {"repo": "owner/repo", "workflow": "ci.yml", "dry_run": True}
            )

    @pytest.mark.asyncio
    async def test_dry_run_denied_by_empty_workflow_allowlist(self) -> None:
        """Empty workflow_allowlist denies dry_run (fail-closed)."""
        svc = _make_service(repo_allowlist=["owner/repo"], workflow_allowlist=[])
        with pytest.raises(CicdAuthorizationError):
            await svc.handle_trigger_workflow(
                {"repo": "owner/repo", "workflow": "ci.yml", "dry_run": True}
            )

    @pytest.mark.asyncio
    async def test_dry_run_denied_by_disallowed_workflow(self) -> None:
        """Disallowed workflow in allowlist denies dry_run."""
        svc = _make_service(
            repo_allowlist=["owner/repo"], workflow_allowlist=["ci.yml"]
        )
        with pytest.raises(CicdAuthorizationError):
            await svc.handle_trigger_workflow(
                {"repo": "owner/repo", "workflow": "deploy.yml", "dry_run": True}
            )


class TestCicdToolSchema:
    def test_trigger_workflow_schema_declares_dry_run(self) -> None:
        from mcp_servers.cicd.cicd_tools import TOOL_LIST

        trigger = next(t for t in TOOL_LIST if t["name"] == "trigger_workflow")
        props = trigger["inputSchema"]["properties"]
        assert "dry_run" in props
        assert props["dry_run"]["type"] == "boolean"

    def test_trigger_workflow_dry_run_not_required(self) -> None:
        from mcp_servers.cicd.cicd_tools import TOOL_LIST

        trigger = next(t for t in TOOL_LIST if t["name"] == "trigger_workflow")
        assert "dry_run" not in trigger["inputSchema"].get("required", [])


class TestGitHubActionsBackendRepr:
    def test_repr_does_not_contain_token_value(self) -> None:
        backend = GitHubActionsBackend("super-secret-token", MagicMock())
        r = repr(backend)
        assert "super-secret-token" not in r
        assert "set" in r

    def test_repr_shows_not_set_when_empty(self) -> None:
        backend = GitHubActionsBackend("", MagicMock())
        r = repr(backend)
        assert "not set" in r
