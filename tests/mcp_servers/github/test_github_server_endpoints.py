"""tests/mcp_servers/github/test_github_server_endpoints.py

Characterization tests for scripts/mcp_servers/github/github_server.py's own
FastAPI wiring (not the included domain routers, which have their own test
files):
  - GET  /v1/tools
  - POST /v1/call_tool (success and unknown-tool paths, with audit logging,
    including the audit record's session_id/request_id field order and the
    request_id `request.state` vs. header fallback)
  - GET  /health (healthy and degraded-by-missing-token paths)
  - _dispatch_github_tool(), including the applied-audit-failure conversion and
    the call-identity binding around the handler
  - GithubMCPServer.dispatch()

These tests lock the current, observed behavior of the thin FastAPI wiring
layer before refactoring (mirrors
tests/mcp_servers/cicd/test_cicd_server_endpoints.py's approach for
cicd_server.py). They monkeypatch the module-level `_service` singleton (and,
for the health endpoint, the module-level `_GITHUB_TOKEN` constant) so no real
GitHub/network access occurs. Business logic (GitHubService, GitHubConfig) is
already covered by tests/mcp_servers/github/test_service_*.py and friends;
this file exists solely to close the coverage gap on github_server.py's own
route/dispatch code (verified via `coverage report
--include=".../github_server.py"` showing 74% before this file was added,
with lines 107-112, 122, 133, 144-158, 178 uncovered).
"""

from __future__ import annotations

import json
import pathlib
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import mcp_servers.dispatch as dispatch
import pytest
from fastapi.testclient import TestClient
from mcp_servers.execution_context import (
    ExecutionContext,
    configure_tool_preview_capabilities,
)
from mcp_servers.github import github_server
from mcp_servers.github.github_models import GitHubConfig
from mcp_servers.github.github_models_base import IssueInfo, PullRequestInfo
from mcp_servers.github.github_models_config import GitHubAppliedAuditError
from mcp_servers.github.github_models_file import (
    CreateOrUpdateFileResponse,
    DeleteRepoFileResponse,
    GetFileContentsResponse,
    PushFilesResponse,
)
from mcp_servers.github.github_models_issues import (
    AddIssueCommentResponse,
    CreateIssueResponse,
    GetIssueResponse,
    ListIssuesResponse,
    SearchIssuesResponse,
)
from mcp_servers.github.github_models_pull_requests import (
    CreatePullRequestResponse,
    GetPullRequestResponse,
    ListPullRequestsResponse,
    MergePullRequestResponse,
    SearchPullRequestsResponse,
    UpdatePullRequestResponse,
)
from mcp_servers.github.github_models_repository import (
    CreateBranchResponse,
    GetCommitResponse,
    ListBranchesResponse,
    ListCommitsResponse,
    SearchCodeResponse,
    SearchRepositoriesResponse,
)
from mcp_servers.github.github_service_dispatch import GitHubService
from mcp_servers.github.github_service_security import _CALL_IDENTITY

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
    """Minimal stand-in for GitHubService, exposing only what github_server.py touches."""

    def __init__(self) -> None:
        self._dispatch_table: dict[str, Any] = {}
        self.audit_failure_count = 0

    def get_dispatch_table(self) -> dict[str, Any]:
        return self._dispatch_table


@pytest.fixture
def fake_service(monkeypatch: pytest.MonkeyPatch) -> _FakeService:
    svc = _FakeService()
    monkeypatch.setattr(github_server, "_service", svc)
    # /v1/call_tool's disabled-tool gate (_github_tool_availability) checks
    # github_server._GITHUB_TOKEN before ever reaching dispatch — set a fake
    # token so TestCallToolEndpoint's tests exercise the dispatch/audit path
    # rather than always hitting the "Tool disabled" short-circuit. Doesn't
    # affect TestToolsListEndpoint (deliberately token-less) or
    # TestDispatchGithubTool/TestGithubMCPServerDispatch (call the dispatch
    # functions directly, bypassing this gate).
    monkeypatch.setattr(github_server, "_GITHUB_TOKEN", "fake-token")
    return svc


@pytest.fixture
def client() -> TestClient:
    return TestClient(github_server.app, headers=MCP_TEST_AUTH_HEADERS)


# Every business-layer method the dispatch table's fmt_* wrappers call after the
# request model validates. Patching all of them makes "the call never reached the
# GitHub layer" observable for any tool.
_DOMAIN_METHODS: tuple[str, ...] = (
    "search_repositories",
    "list_branches",
    "list_commits",
    "get_commit",
    "search_code",
    "get_file_contents",
    "list_issues",
    "get_issue",
    "search_issues",
    "list_pull_requests",
    "get_pull_request",
    "search_pull_requests",
    "create_branch",
    "create_or_update_file",
    "push_files",
    "delete_repo_file",
    "create_issue",
    "add_issue_comment",
    "create_pull_request",
    "update_pull_request",
    "merge_pull_request",
)


def _issue_info(**overrides: object) -> IssueInfo:
    defaults: dict[str, object] = {
        "number": 1,
        "title": "Issue title",
        "state": "open",
        "url": "https://github.com/org/repo/issues/1",
        "body": None,
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-02T00:00:00Z",
        "labels": [],
        "assignees": [],
    }
    defaults.update(overrides)
    return IssueInfo(**defaults)  # type: ignore[arg-type]  # — dict values widened for **overrides; fields are valid at runtime


def _pull_request_info(**overrides: object) -> PullRequestInfo:
    defaults: dict[str, object] = {
        "number": 9,
        "title": "PR title",
        "state": "open",
        "url": "https://github.com/org/repo/pull/9",
        "body": None,
        "head_ref": "feature",
        "base_ref": "main",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-02T00:00:00Z",
        "draft": False,
    }
    defaults.update(overrides)
    return PullRequestInfo(**defaults)  # type: ignore[arg-type]  # — dict values widened for **overrides; fields are valid at runtime


def _stub_response(method_name: str) -> Any:
    """One canned business-layer response per domain method, so a reached call formats."""
    responses: dict[str, Any] = {
        "search_repositories": SearchRepositoriesResponse(query="q", results=[]),
        "list_branches": ListBranchesResponse(branches=[]),
        "list_commits": ListCommitsResponse(commits=[]),
        "get_commit": GetCommitResponse(
            commit={
                "sha": "abc12345def",
                "message": "commit message",
                "author": "author",
                "authored_at": "2026-01-01T00:00:00Z",
                "url": "https://github.com/org/repo/commit/abc12345def",
                "files_changed": 1,
            }
        ),
        "search_code": SearchCodeResponse(query="q", results=[]),
        "get_file_contents": GetFileContentsResponse(
            path="f.txt", content="body", sha="abc12345def", size=4, encoding="utf-8"
        ),
        "list_issues": ListIssuesResponse(issues=[]),
        "get_issue": GetIssueResponse(issue=_issue_info()),
        "search_issues": SearchIssuesResponse(query="q", results=[]),
        "list_pull_requests": ListPullRequestsResponse(pull_requests=[]),
        "get_pull_request": GetPullRequestResponse(pull_request=_pull_request_info()),
        "search_pull_requests": SearchPullRequestsResponse(query="q", results=[]),
        "create_branch": CreateBranchResponse(
            branch_name="new-branch", sha="abc12345def"
        ),
        "create_or_update_file": CreateOrUpdateFileResponse(
            path="f.txt", commit_sha="abc12345def", operation="created"
        ),
        "push_files": PushFilesResponse(
            branch="main", commit_sha="abc12345def", files_pushed=1
        ),
        "delete_repo_file": DeleteRepoFileResponse(
            path="f.txt", commit_sha="abc12345def"
        ),
        "create_issue": CreateIssueResponse(issue=_issue_info()),
        "add_issue_comment": AddIssueCommentResponse(
            issue_number=1, comment_url="https://github.com/org/repo/issues/1#comment"
        ),
        "create_pull_request": CreatePullRequestResponse(
            pull_request=_pull_request_info()
        ),
        "update_pull_request": UpdatePullRequestResponse(
            pull_request=_pull_request_info()
        ),
        "merge_pull_request": MergePullRequestResponse(
            pr_number=9, merged=True, sha="abc12345def", message="merged"
        ),
    }
    return responses[method_name]


@pytest.fixture
def real_service(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[GitHubService, dict[str, AsyncMock]]:
    """The real GitHubService and its dispatch table, with the GitHub layer stubbed.

    Unlike `fake_service`, nothing here bypasses request-model validation: the
    `fmt_*` handlers are the real ones, so `/v1/call_tool` enforces exactly the
    schema `/v1/tools` publishes. Only the business-layer methods that run after
    validation are replaced, so a call that got through validation is harmless
    and a call that did not is detectable.
    """
    svc = GitHubService(
        gh=MagicMock(), cfg=GitHubConfig.from_dict({"allowed_repos": ["org/repo"]})
    )
    handlers = {
        name: AsyncMock(return_value=_stub_response(name)) for name in _DOMAIN_METHODS
    }
    for name, handler in handlers.items():
        monkeypatch.setattr(svc, name, handler)
    monkeypatch.setattr(github_server, "_service", svc)
    monkeypatch.setattr(github_server, "_GITHUB_TOKEN", "fake-token")
    return svc, handlers


class TestToolsListEndpoint:
    def test_lists_github_tools_with_server_key(self, client: TestClient) -> None:
        """include_disabled=true: this test environment has no GITHUB_TOKEN set,
        so REQ-005's default filtering would otherwise omit every tool and this
        assertion would pass vacuously against an empty list."""
        resp = client.get("/v1/tools?include_disabled=true")
        assert resp.status_code == 200
        body = resp.json()
        assert "schema_version" in body
        names = {t["name"]: t for t in body["tools"]}
        assert "github_search_repositories" in names
        assert names["github_search_repositories"]["server_key"] == "github"

    def test_include_disabled_false_omits_tools_without_token(
        self, client: TestClient
    ) -> None:
        resp = client.get("/v1/tools?include_disabled=false")
        assert resp.status_code == 200
        assert resp.json()["tools"] == []

    def test_disabled_code_matches_all_tools_without_token(
        self, client: TestClient
    ) -> None:
        resp = client.get(
            "/v1/tools?include_disabled=true&disabled_code=GITHUB_TOKEN+is+not+set"
        )
        tools = resp.json()["tools"]
        assert tools
        for tool in tools:
            assert tool["disabled_reason"] == "GITHUB_TOKEN is not set"

    def test_generated_input_schemas_are_published_on_the_wire(
        self, client: TestClient
    ) -> None:
        """REQ-002/REQ-003: the contract a client discovers is the generated model schema.

        Complements `test_github_tool_registry.py`'s in-process equality gate: this
        asserts the shape survives the HTTP payload, including the nested `PushFile`
        definition and the pagination bounds a client needs to build a valid call.
        """
        resp = client.get("/v1/tools?include_disabled=true")
        names = {t["name"]: t for t in resp.json()["tools"]}

        write_tools = [t for t in names.values() if t["is_write"]]
        assert len(write_tools) == 9, sorted(t["name"] for t in write_tools)
        for tool in write_tools:
            properties = tool["inputSchema"]["properties"]
            assert "dry_run" in properties, f"{tool['name']} publishes no dry_run"
            assert properties["dry_run"]["type"] == "boolean"
            assert properties["dry_run"]["default"] is False

        per_page = names["github_search_repositories"]["inputSchema"]["properties"][
            "per_page"
        ]
        assert per_page["minimum"] == 1
        assert per_page["maximum"] == 100
        assert per_page["default"] == 30

        push_schema = names["github_push_files"]["inputSchema"]
        assert "PushFile" in push_schema["$defs"]
        assert push_schema["properties"]["files"]["items"]["$ref"] == "#/$defs/PushFile"

        for tool in names.values():
            assert "title" not in tool["inputSchema"], (
                f"{tool['name']} carries title noise"
            )


class TestCallToolEndpoint:
    def test_dispatches_known_tool_and_audit_logs(
        self, client: TestClient, fake_service: _FakeService
    ) -> None:
        handler = AsyncMock(return_value="42 stars")
        fake_service._dispatch_table["github_search_repositories"] = handler
        resp = client.post(
            "/v1/call_tool",
            json={
                "name": "github_search_repositories",
                "args": {"owner": "acme", "repo": "widgets"},
            },
            headers={"x-session-id": "sess-1", "x-request-id": "req-1"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body == {
            "result": "42 stars",
            "is_error": False,
            "dedup_state": "",
            "execution_mode": "applied",
            "side_effect_applied": False,
        }
        handler.assert_awaited_once_with({"owner": "acme", "repo": "widgets"})

    def test_unknown_tool_returns_error_result(
        self, client: TestClient, fake_service: _FakeService
    ) -> None:
        resp = client.post("/v1/call_tool", json={"name": "not_a_tool", "args": {}})
        assert resp.status_code == 200
        body = resp.json()
        assert body["is_error"] is True
        assert "Unknown tool" in body["result"]

    def test_audit_target_falls_back_to_empty_owner_and_repo(
        self, client: TestClient, fake_service: _FakeService
    ) -> None:
        """req.args without 'owner'/'repo' keys still succeeds; audit target
        formatting (f"repo={{owner}}/{{repo}}") uses "" for missing keys."""
        handler = AsyncMock(return_value="ok")
        fake_service._dispatch_table["github_list_issues"] = handler
        resp = client.post(
            "/v1/call_tool", json={"name": "github_list_issues", "args": {}}
        )
        assert resp.status_code == 200
        assert resp.json() == {
            "result": "ok",
            "is_error": False,
            "dedup_state": "",
            "execution_mode": "applied",
            "side_effect_applied": False,
        }

    def test_call_tool_reports_the_structured_metadata(
        self, client: TestClient, fake_service: _FakeService
    ) -> None:
        """The response carries the resolved mode and the side-effect flag.

        The preview case declares the tool's capability explicitly because this
        test drives the endpoint without going through `run_http`.
        """
        handler = AsyncMock(return_value='{"dry_run": true}')
        fake_service._dispatch_table["github_create_branch"] = handler
        configure_tool_preview_capabilities(
            ({"name": "github_create_branch", "preview_capability": "dry_run"},)
        )
        preview = client.post(
            "/v1/call_tool",
            json={
                "name": "github_create_branch",
                "args": {"owner": "acme", "repo": "widgets", "dry_run": True},
            },
            headers={
                "x-idempotency-key": "key-meta-preview",
                "x-execution-mode": "preview",
            },
        )
        assert preview.status_code == 200
        body = preview.json()
        assert body["execution_mode"] == "preview"
        assert body["side_effect_applied"] is False

        applied = client.post(
            "/v1/call_tool",
            json={
                "name": "github_create_branch",
                "args": {"owner": "acme", "repo": "widgets"},
            },
            headers={"x-idempotency-key": "key-applied"},
        )
        assert applied.status_code == 200
        body = applied.json()
        assert body["execution_mode"] == "applied"
        assert body["side_effect_applied"] is True

    def test_audit_record_keeps_session_and_request_context_in_order(
        self,
        client: TestClient,
        fake_service: _FakeService,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The audit record's `session_id` / `request_id` must follow the order
        documented by `extract_request_context` (session_id, request_id,
        idempotency_key); swapping them breaks correlation with the agent-side
        `tool_exec` record's `mcp_request_id`.

        `attach_auth_middleware` (github_server.py:145) always sets
        `request.state.request_id`, and `extract_request_context` prefers state over
        the header fallback, so the record's `request_id` equals the X-Request-Id
        response header and never the sent `x-request-id` value.
        """
        logger = MagicMock()
        monkeypatch.setattr(github_server, "logger", logger)
        handler = AsyncMock(return_value="ok")
        fake_service._dispatch_table["github_get_issue"] = handler
        resp = client.post(
            "/v1/call_tool",
            json={"name": "github_get_issue", "args": {}},
            headers={"x-session-id": "sess-ctx", "x-request-id": "hdr-req-id"},
        )
        assert resp.status_code == 200
        assert resp.json()["is_error"] is False
        records = [json.loads(call.args[0]) for call in logger.info.call_args_list]
        assert len(records) == 1
        assert records[0]["session_id"] == "sess-ctx"
        assert records[0]["request_id"] == resp.headers["x-request-id"]
        assert records[0]["request_id"] != "hdr-req-id"


class TestHealthEndpoint:
    def test_degraded_when_github_token_not_set(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The no-store case: with no store wired the details dict is what it was before this row.
        monkeypatch.setattr(dispatch, "_dedup_store", None)
        monkeypatch.setattr(dispatch, "_dedup_config", None)
        monkeypatch.setattr(github_server, "_GITHUB_TOKEN", "")
        resp = client.get("/health")
        assert resp.status_code == 503
        body = resp.json()
        assert body["status"] == "degraded"
        assert body["ready"] is False
        assert body["dependencies"] == {"github_token": "not_set"}
        assert body["details"] == {
            "service": "github-mcp",
            "audit_failure_count": 0,
        }

    def test_healthy_when_github_token_set(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(dispatch, "_dedup_store", None)
        monkeypatch.setattr(dispatch, "_dedup_config", None)
        monkeypatch.setattr(github_server, "_GITHUB_TOKEN", "ghp_test_token")
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["ready"] is True
        assert body["dependencies"] == {}
        assert body["details"] == {
            "service": "github-mcp",
            "audit_failure_count": 0,
        }

    def test_health_details_publish_the_dedup_block_when_a_store_is_wired(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
        isolated_dedup: pathlib.Path,
    ) -> None:
        monkeypatch.setattr(github_server, "_GITHUB_TOKEN", "ghp_test_token")
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()

        # The `service` key stays as it is; `dedup` is the single new key (REQ-004),
        # and `audit_failure_count` reports the service's applied-audit failures (REQ-008).
        assert body["details"]["service"] == "github-mcp"
        assert set(body["details"]) == {"service", "dedup", "audit_failure_count"}
        block = body["details"]["dedup"]
        assert set(block) == DEDUP_FIELDS
        assert block["db_path"] == str(isolated_dedup)


class TestDispatchGithubTool:
    @pytest.mark.asyncio
    async def test_routes_through_service_dispatch_table(
        self, fake_service: _FakeService
    ) -> None:
        handler = AsyncMock(return_value="dispatched")
        fake_service._dispatch_table["github_create_branch"] = handler
        # A side-effecting call needs a keyed context: a keyless one is refused
        # before the handler runs.
        result = await github_server._dispatch_github_tool(
            "github_create_branch",
            {"owner": "acme", "repo": "widgets"},
            context=ExecutionContext.for_programmatic_call(
                "github_create_branch",
                {"owner": "acme", "repo": "widgets"},
                idempotency_key="key-1",
            ),
        )
        assert result.output == "dispatched"
        assert result.is_error is False
        handler.assert_awaited_once_with({"owner": "acme", "repo": "widgets"})


class TestDispatchGithubToolAppliedAuditAndIdentity:
    """The wrapper binds the call identity around the handler and converts an
    applied write whose completion audit failed into an explicit
    applied_audit_failed result that says the write must not be retried."""

    @pytest.mark.asyncio
    async def test_applied_audit_failure_returns_applied_audit_failed(
        self, fake_service: _FakeService
    ) -> None:
        handler = AsyncMock(
            side_effect=GitHubAppliedAuditError(
                "applied_audit_failed (create_issue): audit log write failed"
            )
        )
        fake_service._dispatch_table["github_create_issue"] = handler
        result = await github_server._dispatch_github_tool(
            "github_create_issue",
            {"owner": "acme", "repo": "widgets"},
            context=ExecutionContext.for_programmatic_call(
                "github_create_issue",
                {"owner": "acme", "repo": "widgets"},
                idempotency_key="key-applied-audit",
            ),
        )
        assert result.is_error is True
        assert result.error_type == "applied_audit_failed"
        assert "applied_audit_failed" in result.output
        assert "create_issue" in result.output
        assert "do not retry" in result.output
        # Arguments are never echoed into the result text.
        assert "widgets" not in result.output

    @pytest.mark.asyncio
    async def test_call_identity_is_bound_during_the_handler(
        self, fake_service: _FakeService
    ) -> None:
        seen: list[tuple[str, str, str]] = []

        def record(args: dict) -> str:
            seen.append(_CALL_IDENTITY.get())
            return "ok"

        handler = AsyncMock(side_effect=record)
        fake_service._dispatch_table["github_create_branch"] = handler
        result = await github_server._dispatch_github_tool(
            "github_create_branch",
            {"owner": "acme", "repo": "widgets"},
            context=ExecutionContext(
                request_id="req-identity",
                session_id="sess-identity",
                idempotency_key="key-identity",
            ),
        )
        assert result.is_error is False
        assert seen == [("sess-identity", "req-identity", "key-identity")]
        # The binding is reset on exit so a later call cannot inherit it.
        assert _CALL_IDENTITY.get() == ("", "", "")

    def test_call_tool_passes_the_request_identity_to_the_wrapper(
        self, client: TestClient, fake_service: _FakeService
    ) -> None:
        seen: list[tuple[str, str, str]] = []

        def record(args: dict) -> str:
            seen.append(_CALL_IDENTITY.get())
            return "ok"

        fake_service._dispatch_table["github_create_branch"] = AsyncMock(
            side_effect=record
        )
        resp = client.post(
            "/v1/call_tool",
            json={
                "name": "github_create_branch",
                "args": {"owner": "acme", "repo": "widgets"},
            },
            headers={
                "x-session-id": "sess-call",
                "x-idempotency-key": "key-call",
            },
        )
        assert resp.status_code == 200
        assert seen == [("sess-call", resp.headers["x-request-id"], "key-call")]

    @pytest.mark.asyncio
    async def test_programmatic_call_records_show_empty_identity(
        self, fake_service: _FakeService
    ) -> None:
        """The programmatic override passes no request ids, so its records show `-`."""
        seen: list[tuple[str, str, str]] = []

        def record(args: dict) -> str:
            seen.append(_CALL_IDENTITY.get())
            return "ok"

        fake_service._dispatch_table["github_create_branch"] = AsyncMock(
            side_effect=record
        )
        server = github_server.GithubMCPServer()
        result = await server.dispatch(
            "github_create_branch",
            {"owner": "acme", "repo": "widgets"},
            context=ExecutionContext.for_programmatic_call(
                "github_create_branch",
                {"owner": "acme", "repo": "widgets"},
                idempotency_key="key-prog",
            ),
        )
        assert result.is_error is False
        assert seen == [("", "", "key-prog")]


class TestGithubMCPServerDispatch:
    @pytest.mark.asyncio
    async def test_dispatch_routes_through_service_table(
        self, fake_service: _FakeService
    ) -> None:
        handler = AsyncMock(return_value="dispatched")
        fake_service._dispatch_table["github_list_branches"] = handler
        server = github_server.GithubMCPServer()
        result = await server.dispatch(
            "github_list_branches", {"owner": "acme", "repo": "widgets"}
        )
        assert result.output == "dispatched"
        assert result.is_error is False


class TestCallToolBoundary:
    """HTTP-level cases for the repository boundary (mcpai002 AC-1, AC-2)."""

    def test_read_outside_the_allowlist_returns_403(
        self,
        client: TestClient,
        fake_service: _FakeService,
    ) -> None:
        """The service-layer guard reaches the endpoint as an authorization error."""
        from mcp_servers.github.github_models import GitHubAuthorizationError

        async def _deny(args: dict[str, Any]) -> str:
            raise GitHubAuthorizationError(
                "Repository not in allowed_repos: other/repo"
            )

        fake_service._dispatch_table["github_get_file_contents"] = _deny
        resp = client.post(
            "/v1/call_tool",
            json={
                "name": "github_get_file_contents",
                "args": {"owner": "Other", "repo": "REPO", "path": "f.txt"},
            },
        )
        assert resp.status_code == 403

    def test_audit_target_names_the_canonical_repository_key(
        self,
        client: TestClient,
        fake_service: _FakeService,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The audit record shows the same lowercase key the guard compared (AC-2)."""
        logger = MagicMock()
        monkeypatch.setattr(github_server, "logger", logger)
        handler = AsyncMock(return_value="ok")
        fake_service._dispatch_table["github_get_issue"] = handler
        resp = client.post(
            "/v1/call_tool",
            json={"name": "github_get_issue", "args": {"owner": "Org", "repo": "REPO"}},
        )
        assert resp.status_code == 200
        records = [json.loads(call.args[0]) for call in logger.info.call_args_list]
        assert records[0]["target"] == "repo=org/repo"


class TestCallToolValidation:
    """T-05/REQ-008: `/v1/call_tool` rejects exactly what the published schema advertises.

    Reached through the real dispatch table (`real_service`), so the failure comes
    from the request models, not from a hand-built handler. The boundary values match
    `test_github_request_validation.py` so both layers pin the same numbers.
    """

    # Write tools also need X-Idempotency-Key: the REQ-004 boundary in
    # mcp_servers/server.py rejects a keyless side-effecting call with 422 before
    # the dispatcher runs, so those rows carry a key to reach validation.
    @pytest.mark.parametrize(
        ("tool_name", "args", "model_name", "headers"),
        [
            # unknown key (was silently dropped before mcpai003)
            (
                "github_search_repositories",
                {"query": "q", "bogus": 1},
                "SearchRepositoriesRequest",
                {},
            ),
            # per_page above the published maximum
            (
                "github_search_repositories",
                {"query": "q", "per_page": 101},
                "SearchRepositoriesRequest",
                {},
            ),
            # per_page below the published minimum
            (
                "github_list_issues",
                {"owner": "org", "repo": "repo", "per_page": 0},
                "ListIssuesRequest",
                {},
            ),
            # missing required key
            ("github_list_issues", {"owner": "org"}, "ListIssuesRequest", {}),
            # empty identifier
            (
                "github_get_file_contents",
                {"owner": "", "repo": "repo", "path": "f.txt"},
                "GetFileContentsRequest",
                {},
            ),
            # explicitly empty sentinel
            (
                "github_list_commits",
                {"owner": "org", "repo": "repo", "branch": ""},
                "ListCommitsRequest",
                {},
            ),
            # non-positive number
            (
                "github_get_issue",
                {"owner": "org", "repo": "repo", "issue_number": 0},
                "GetIssueRequest",
                {},
            ),
            # oversized content
            (
                "github_create_or_update_file",
                {
                    "owner": "org",
                    "repo": "repo",
                    "path": "f.txt",
                    "content": "x" * 1048577,
                    "message": "m",
                },
                "CreateOrUpdateFileRequest",
                {"x-idempotency-key": "key-validation-1"},
            ),
            # empty files list
            (
                "github_push_files",
                {
                    "owner": "org",
                    "repo": "repo",
                    "branch": "main",
                    "message": "m",
                    "files": [],
                },
                "PushFilesRequest",
                {"x-idempotency-key": "key-2"},
            ),
            # unknown key nested in one files entry
            (
                "github_push_files",
                {
                    "owner": "org",
                    "repo": "repo",
                    "branch": "main",
                    "message": "m",
                    "files": [{"path": "a", "content": "c", "bogus": 1}],
                },
                "PushFilesRequest",
                {"x-idempotency-key": "key-3"},
            ),
            # no-op pull request update
            (
                "github_update_pull_request",
                {"owner": "org", "repo": "repo", "pr_number": 1},
                "UpdatePullRequestRequest",
                {"x-idempotency-key": "key-4"},
            ),
        ],
    )
    def test_invalid_arguments_error_without_reaching_the_github_layer(
        self,
        client: TestClient,
        real_service: tuple[GitHubService, dict[str, AsyncMock]],
        tool_name: str,
        args: dict[str, Any],
        model_name: str,
        headers: dict[str, str],
    ) -> None:
        """AC-03/AC-04: a rejected payload never reaches the allowlist check or GitHub."""
        _, handlers = real_service
        resp = client.post(
            "/v1/call_tool", json={"name": tool_name, "args": args}, headers=headers
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["is_error"] is True
        assert model_name in body["result"], body["result"]
        assert "invalid field(s)" in body["result"], body["result"]
        for method_name, handler in handlers.items():
            handler.assert_not_awaited()

    @pytest.mark.parametrize(
        ("tool_name", "method_name", "args", "headers"),
        [
            (
                "github_search_repositories",
                "search_repositories",
                {"query": "topic:ml"},
                {},
            ),
            ("github_list_issues", "list_issues", {"owner": "org", "repo": "repo"}, {}),
            (
                "github_get_file_contents",
                "get_file_contents",
                {"owner": "org", "repo": "repo", "path": "f.txt"},
                {},
            ),
            (
                "github_list_commits",
                "list_commits",
                {"owner": "org", "repo": "repo", "branch": "feature"},
                {},
            ),
            (
                "github_create_or_update_file",
                "create_or_update_file",
                {
                    "owner": "org",
                    "repo": "repo",
                    "path": "f.txt",
                    "content": "c",
                    "message": "m",
                },
                {"x-idempotency-key": "key-5"},
            ),
            (
                "github_push_files",
                "push_files",
                {
                    "owner": "org",
                    "repo": "repo",
                    "branch": "main",
                    "message": "m",
                    "files": [{"path": "a", "content": "c"}],
                },
                {"x-idempotency-key": "key-6"},
            ),
            (
                "github_update_pull_request",
                "update_pull_request",
                {"owner": "org", "repo": "repo", "pr_number": 1, "state": "open"},
                {"x-idempotency-key": "key-7"},
            ),
        ],
    )
    def test_valid_arguments_reach_the_business_layer(
        self,
        client: TestClient,
        real_service: tuple[GitHubService, dict[str, AsyncMock]],
        tool_name: str,
        method_name: str,
        args: dict[str, Any],
        headers: dict[str, str],
    ) -> None:
        """The happy path still runs: strictness did not reject a valid call."""
        _, handlers = real_service
        resp = client.post(
            "/v1/call_tool", json={"name": tool_name, "args": args}, headers=headers
        )
        assert resp.status_code == 200
        assert resp.json()["is_error"] is False
        handlers[method_name].assert_awaited_once()

    def test_validation_failure_is_audited_as_an_error(
        self,
        client: TestClient,
        real_service: tuple[GitHubService, dict[str, AsyncMock]],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The audit record shows the rejected call as an errored tool execution.

        `github_server.call_tool` passes `outcome` but no `error_type` to `_audit_log`,
        so the dispatcher's `validation_error` taxonomy is not on this record today; the
        failure mode is visible in the result text instead. Locking `error_type` empty
        here makes that gap explicit rather than assuming it away.
        """
        logger = MagicMock()
        monkeypatch.setattr(github_server, "logger", logger)
        resp = client.post(
            "/v1/call_tool",
            json={
                "name": "github_search_repositories",
                "args": {"query": "q", "bogus": 1},
            },
            headers={"x-session-id": "sess-val", "x-request-id": "req-val"},
        )
        assert resp.status_code == 200
        assert resp.json()["is_error"] is True
        records = [json.loads(call.args[0]) for call in logger.info.call_args_list]
        assert len(records) == 1
        assert records[0]["tool"] == "github_search_repositories"
        assert records[0]["outcome"] == "error"
        assert records[0]["error_type"] == ""
        assert "SearchRepositoriesRequest" in resp.json()["result"]
