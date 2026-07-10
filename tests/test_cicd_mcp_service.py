"""tests/test_cicd_mcp_service.py
Unit tests for mcp/cicd/service.py: CiCdService guards and GitHubActionsBackend.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import orjson
import pytest
from mcp_servers.cicd.models import (
    CicdAuthorizationError,
    CicdConfig,
    CicdNotFoundError,
    CicdValidationError,
)
from mcp_servers.cicd.service import CiCdService, GitHubActionsBackend
from mcp_servers.cicd.service_github_actions_job import GitHubActionsJobBackend

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


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
        backend.trigger_workflow.return_value = "dispatched"
        svc = _make_service(repo_allowlist=["owner/repo"], backend=backend)

        result = await svc.handle_trigger_workflow(
            {"repo": "owner/repo", "workflow": "ci.yml", "ref": "main"}
        )
        assert result == "dispatched"
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
        backend.get_workflow_logs.return_value = "=== Job: build ==="
        svc = _make_service(repo_allowlist=["owner/repo"], backend=backend)

        result = await svc.handle_get_workflow_logs(
            {"repo": "owner/repo", "run_id": 456}
        )
        assert "build" in result
        backend.get_workflow_logs.assert_awaited_once_with("owner", "repo", 456)


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
    async def test_204_returns_dispatch_message(self) -> None:
        http = AsyncMock()
        http.post.return_value = _make_http_response(204)
        backend = GitHubActionsBackend("token", http)

        result = await backend.trigger_workflow("owner", "repo", "ci.yml", "main", {})
        assert "dispatched" in result.lower()
        assert "owner/repo" in result

    @pytest.mark.asyncio
    async def test_404_raises_not_found(self) -> None:
        http = AsyncMock()
        http.post.return_value = _make_http_response(404)
        backend = GitHubActionsBackend("token", http)

        with pytest.raises(CicdNotFoundError):
            await backend.trigger_workflow("owner", "repo", "ci.yml", "main", {})

    @pytest.mark.asyncio
    async def test_request_uses_correct_url(self) -> None:
        http = AsyncMock()
        http.post.return_value = _make_http_response(204)
        backend = GitHubActionsBackend("token", http)

        await backend.trigger_workflow("owner", "repo", "ci.yml", "main", {})
        call_url = http.post.call_args[0][0]
        assert "owner/repo/actions/workflows/ci.yml/dispatches" in call_url

    @pytest.mark.asyncio
    async def test_auth_header_is_set(self) -> None:
        http = AsyncMock()
        http.post.return_value = _make_http_response(204)
        backend = GitHubActionsBackend("my-secret-token", http)

        await backend.trigger_workflow("owner", "repo", "ci.yml", "main", {})
        call_kwargs = http.post.call_args[1]
        headers = call_kwargs.get("headers", {})
        assert headers.get("Authorization") == "Bearer my-secret-token"

    @pytest.mark.asyncio
    async def test_no_token_omits_auth_header(self) -> None:
        http = AsyncMock()
        http.post.return_value = _make_http_response(204)
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
    async def test_returns_job_header_and_log(self) -> None:
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
        http = AsyncMock()
        # First call: jobs list; second call: log content (follow redirect)
        jobs_resp = _make_http_response(200, body=jobs_body)
        log_resp = _make_http_response(200, text="2024-01-01T00:00:00.000Z Run tests\n")
        log_resp.is_success = True
        log_resp.text = "2024-01-01T00:00:00.000Z Run tests\n"
        http.get.side_effect = [jobs_resp, log_resp]
        backend = GitHubActionsJobBackend("token", http)

        result = await backend.get_workflow_logs("owner", "repo", 42)
        assert "build" in result
        assert "Set up job" in result
        assert "Run tests" in result

    @pytest.mark.asyncio
    async def test_truncates_at_max_log_size(self) -> None:
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
        jobs_resp = _make_http_response(200, body=jobs_body)
        log_resp = MagicMock()
        log_resp.is_success = True
        log_resp.text = large_log
        http.get.side_effect = [jobs_resp, log_resp]
        backend = GitHubActionsJobBackend("token", http, 1)

        result = await backend.get_workflow_logs("owner", "repo", 43)
        # Output must not exceed 1 KB (1024 bytes) significantly
        assert (
            len(result.encode()) <= 1024 + 100
        )  # allow small overhead for truncation message
        assert "TRUNCATED" in result

    @pytest.mark.asyncio
    async def test_no_jobs_returns_empty_message(self) -> None:
        http = AsyncMock()
        http.get.return_value = _make_http_response(200, body={"jobs": []})
        backend = GitHubActionsJobBackend("token", http)

        result = await backend.get_workflow_logs("owner", "repo", 99)
        assert "No jobs found" in result


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
    async def test_dry_run_includes_inputs_in_preview(self) -> None:
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
        assert "prod" in payload["preview"]

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
        from mcp_servers.cicd.tools import TOOL_LIST

        trigger = next(t for t in TOOL_LIST if t["name"] == "trigger_workflow")
        props = trigger["inputSchema"]["properties"]
        assert "dry_run" in props
        assert props["dry_run"]["type"] == "boolean"

    def test_trigger_workflow_dry_run_not_required(self) -> None:
        from mcp_servers.cicd.tools import TOOL_LIST

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
