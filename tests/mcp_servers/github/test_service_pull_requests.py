"""tests/mcp_servers/github/test_service_pull_requests.py

Characterization tests closing coverage gaps in
`mcp_servers/github/service_pull_requests.py` (PullRequestOps) found before a
refactor pass (04_refactor.md sweep of the `scripts/mcp_servers/github/`
subsystem). These lock existing behavior only -- no source logic is asserted
to be "correct", only that it behaves the way it currently does.

Baseline coverage (before this file): 21% -- lines 49-58, 66-72, 79-101,
108-120, 127-150, 157-196 were unexercised. The existing suite
(`test_github_mcp_service.py`) only exercises `create_pull_request`,
`update_pull_request`, and `merge_pull_request` with the service method
itself patched via `AsyncMock` (verified via `rg
list_pull_requests|get_pull_request|search_pull_requests
tests/mcp_servers/github/test_github_mcp_service.py` returning no hits, and
`create_pull_request|update_pull_request|merge_pull_request` hits all using
`new=AsyncMock(...)` patches), so the `_sync` closures that hold the actual
PyGithub call sequence, guard ordering, and response construction never ran.
`list_pull_requests`, `get_pull_request`, and `search_pull_requests` had no
coverage at all. These tests let `_run_github` execute for real
(`asyncio.to_thread`) against a mocked `self._gh` PyGithub client, so the
closures themselves are exercised:

  - list_pull_requests: repo.get_pulls(state=...) call, per_page slicing,
    pr_to_info conversion
  - get_pull_request: repo.get_pull(number=...) call, pr_to_info conversion
  - create_pull_request: _assert_allowed_repo guard runs before the API
    call, field passthrough, audit log written
  - search_pull_requests: "is:pr" appended only when absent from the query,
    self._gh.search_issues(query=...) call, per_page slicing
  - update_pull_request: _assert_allowed_repo guard runs before the API
    call, only-set fields are passed to pr.edit(), pr.edit() is skipped
    entirely when no fields are set, audit log written
  - merge_pull_request: _assert_allowed_repo guard runs before the API
    call, allow_force_push gate on merge_method="rebase" runs before the
    API call, _assert_allowed_branch guard runs against the PR's actual
    base ref (fetched from the API) before the review check,
    require_pr_review gate requires at least one APPROVED review,
    commit_title/commit_message are only forwarded when truthy, audit log
    written with sha truncated to 8 characters
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from mcp_servers.github.github_models_config import (
    GitHubAuthorizationError,
    GitHubConfig,
)
from mcp_servers.github.github_models_pull_requests import (
    CreatePullRequestRequest,
    GetPullRequestRequest,
    ListPullRequestsRequest,
    MergePullRequestRequest,
    SearchPullRequestsRequest,
    UpdatePullRequestRequest,
)
from mcp_servers.github.github_service_dispatch import GitHubService


def _make_service(cfg: dict | None = None) -> GitHubService:
    """GitHubService with a MagicMock GitHub client; no real API calls are made."""
    raw = cfg or {"allowed_repos": ["org/repo"]}
    return GitHubService(gh=MagicMock(), cfg=GitHubConfig.from_dict(raw))


def _make_mock_pr(**overrides: object) -> MagicMock:
    from datetime import datetime

    pr = MagicMock()
    pr.number = overrides.get("number", 1)
    pr.title = overrides.get("title", "Add feature")
    pr.state = overrides.get("state", "open")
    pr.html_url = overrides.get("html_url", "https://github.com/org/repo/pull/1")
    pr.body = overrides.get("body", "Description")
    pr.created_at = overrides.get("created_at", datetime(2026, 1, 1))
    pr.updated_at = overrides.get("updated_at", datetime(2026, 1, 2))
    pr.draft = overrides.get("draft", False)
    head = MagicMock()
    head.ref = overrides.get("head_ref", "feature-branch")
    pr.head = head
    base = MagicMock()
    base.ref = overrides.get("base_ref", "main")
    pr.base = base
    return pr


# ── list_pull_requests ────────────────────────────────────────────────────────


class TestListPullRequests:
    @pytest.mark.asyncio
    async def test_returns_converted_prs(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_repo.get_pulls.return_value = [_make_mock_pr(number=42)]

        req = ListPullRequestsRequest(owner="org", repo="repo")
        resp = await svc.list_pull_requests(req)

        assert len(resp.pull_requests) == 1
        assert resp.pull_requests[0].number == 42
        svc._gh.get_repo.assert_called_once_with("org/repo")
        mock_repo.get_pulls.assert_called_once_with(state="open")

    @pytest.mark.asyncio
    async def test_passes_requested_state(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_repo.get_pulls.return_value = []

        req = ListPullRequestsRequest(owner="org", repo="repo", state="closed")
        await svc.list_pull_requests(req)

        mock_repo.get_pulls.assert_called_once_with(state="closed")

    @pytest.mark.asyncio
    async def test_truncates_to_per_page(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_repo.get_pulls.return_value = [_make_mock_pr(number=n) for n in range(5)]

        req = ListPullRequestsRequest(owner="org", repo="repo", per_page=2)
        resp = await svc.list_pull_requests(req)

        assert [pr.number for pr in resp.pull_requests] == [0, 1]

    @pytest.mark.asyncio
    async def test_per_page_clamped_to_config_max(self) -> None:
        svc = _make_service({"allowed_repos": ["org/repo"], "max_per_page": 3})
        mock_repo = svc._gh.get_repo.return_value
        mock_repo.get_pulls.return_value = [_make_mock_pr(number=n) for n in range(10)]

        req = ListPullRequestsRequest(owner="org", repo="repo", per_page=999)
        resp = await svc.list_pull_requests(req)

        assert len(resp.pull_requests) == 3


# ── get_pull_request ──────────────────────────────────────────────────────────


class TestGetPullRequest:
    @pytest.mark.asyncio
    async def test_returns_converted_pr(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_repo.get_pull.return_value = _make_mock_pr(number=7, title="Fix crash")

        req = GetPullRequestRequest(owner="org", repo="repo", pr_number=7)
        resp = await svc.get_pull_request(req)

        assert resp.pull_request.number == 7
        assert resp.pull_request.title == "Fix crash"
        mock_repo.get_pull.assert_called_once_with(number=7)


# ── create_pull_request ───────────────────────────────────────────────────────


class TestCreatePullRequest:
    @pytest.mark.asyncio
    async def test_creates_and_returns_response(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_repo.create_pull.return_value = _make_mock_pr(number=99, title="New PR")

        req = CreatePullRequestRequest(
            owner="org",
            repo="repo",
            title="New PR",
            body="Details",
            head="feature",
            base="main",
        )
        resp = await svc.create_pull_request(req)

        assert resp.pull_request.number == 99
        mock_repo.create_pull.assert_called_once_with(
            title="New PR", body="Details", head="feature", base="main"
        )

    @pytest.mark.asyncio
    async def test_denies_repo_not_in_allowlist_before_api_call(self) -> None:
        svc = _make_service({"allowed_repos": ["org/other-repo"]})

        req = CreatePullRequestRequest(
            owner="org", repo="repo", title="New PR", head="feature", base="main"
        )
        with pytest.raises(GitHubAuthorizationError):
            await svc.create_pull_request(req)

        svc._gh.get_repo.assert_not_called()

    @pytest.mark.asyncio
    async def test_writes_audit_log_with_repo_pr_head_base_title(
        self, tmp_path: Path
    ) -> None:
        log_file = tmp_path / "audit.log"
        svc = _make_service(
            {"allowed_repos": ["org/repo"], "audit_log_path": str(log_file)}
        )
        mock_repo = svc._gh.get_repo.return_value
        mock_repo.create_pull.return_value = _make_mock_pr(number=55)

        req = CreatePullRequestRequest(
            owner="org", repo="repo", title="New PR", head="feature", base="main"
        )
        await svc.create_pull_request(req)

        content = log_file.read_text()
        assert "op=create_pull_request" in content
        assert "repo='org/repo'" in content
        assert "pr=55" in content
        assert "head='feature'" in content
        assert "base='main'" in content
        assert "title='New PR'" in content


# ── search_pull_requests ──────────────────────────────────────────────────────


class TestSearchPullRequests:
    @pytest.mark.asyncio
    async def test_appends_is_pr_when_absent(self) -> None:
        svc = _make_service()
        svc._gh.search_issues.return_value = []

        req = SearchPullRequestsRequest(query="repo:org/repo author:octocat")
        await svc.search_pull_requests(req)

        svc._gh.search_issues.assert_called_once_with(
            query="repo:org/repo author:octocat is:pr"
        )

    @pytest.mark.asyncio
    async def test_does_not_duplicate_is_pr_when_present(self) -> None:
        svc = _make_service()
        svc._gh.search_issues.return_value = []

        req = SearchPullRequestsRequest(query="repo:org/repo is:pr label:bug")
        await svc.search_pull_requests(req)

        svc._gh.search_issues.assert_called_once_with(
            query="repo:org/repo is:pr label:bug"
        )

    @pytest.mark.asyncio
    async def test_returns_query_and_converted_results(self) -> None:
        from tests.mcp_servers.github.test_service_issues import _make_mock_issue

        svc = _make_service()
        svc._gh.search_issues.return_value = [_make_mock_issue(number=3)]

        req = SearchPullRequestsRequest(query="test is:pr")
        resp = await svc.search_pull_requests(req)

        assert resp.query == "test is:pr"
        assert len(resp.results) == 1
        assert resp.results[0].number == 3

    @pytest.mark.asyncio
    async def test_truncates_to_per_page(self) -> None:
        from tests.mcp_servers.github.test_service_issues import _make_mock_issue

        svc = _make_service()
        svc._gh.search_issues.return_value = [
            _make_mock_issue(number=n) for n in range(5)
        ]

        req = SearchPullRequestsRequest(query="test", per_page=2)
        resp = await svc.search_pull_requests(req)

        assert len(resp.results) == 2


# ── update_pull_request ───────────────────────────────────────────────────────


class TestUpdatePullRequest:
    @pytest.mark.asyncio
    async def test_updates_only_provided_fields(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_pr = _make_mock_pr(number=5)
        mock_repo.get_pull.return_value = mock_pr

        req = UpdatePullRequestRequest(
            owner="org", repo="repo", pr_number=5, title="Renamed"
        )
        await svc.update_pull_request(req)

        mock_pr.edit.assert_called_once_with(title="Renamed")

    @pytest.mark.asyncio
    async def test_passes_body_and_state(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_pr = _make_mock_pr(number=5)
        mock_repo.get_pull.return_value = mock_pr

        req = UpdatePullRequestRequest(
            owner="org",
            repo="repo",
            pr_number=5,
            body="New body",
            state="closed",
        )
        await svc.update_pull_request(req)

        mock_pr.edit.assert_called_once_with(body="New body", state="closed")

    @pytest.mark.asyncio
    async def test_skips_edit_call_when_no_fields_set(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_pr = _make_mock_pr(number=5)
        mock_repo.get_pull.return_value = mock_pr

        req = UpdatePullRequestRequest(owner="org", repo="repo", pr_number=5)
        resp = await svc.update_pull_request(req)

        mock_pr.edit.assert_not_called()
        assert resp.pull_request.number == 5

    @pytest.mark.asyncio
    async def test_denies_repo_not_in_allowlist_before_api_call(self) -> None:
        svc = _make_service({"allowed_repos": ["org/other-repo"]})

        req = UpdatePullRequestRequest(
            owner="org", repo="repo", pr_number=5, title="Renamed"
        )
        with pytest.raises(GitHubAuthorizationError):
            await svc.update_pull_request(req)

        svc._gh.get_repo.assert_not_called()

    @pytest.mark.asyncio
    async def test_writes_audit_log_with_repo_and_pr_number(
        self, tmp_path: Path
    ) -> None:
        log_file = tmp_path / "audit.log"
        svc = _make_service(
            {"allowed_repos": ["org/repo"], "audit_log_path": str(log_file)}
        )
        mock_repo = svc._gh.get_repo.return_value
        mock_repo.get_pull.return_value = _make_mock_pr(number=5)

        req = UpdatePullRequestRequest(
            owner="org", repo="repo", pr_number=5, title="Renamed"
        )
        await svc.update_pull_request(req)

        content = log_file.read_text()
        assert "op=update_pull_request" in content
        assert "repo='org/repo'" in content
        assert "pr=5" in content


# ── merge_pull_request ────────────────────────────────────────────────────────


def _make_mock_review(state: str) -> MagicMock:
    review = MagicMock()
    review.state = state
    return review


class TestMergePullRequest:
    @pytest.mark.asyncio
    async def test_merges_with_approved_review(self) -> None:
        svc = _make_service({"allowed_repos": ["org/repo"], "require_pr_review": True})
        mock_repo = svc._gh.get_repo.return_value
        mock_pr = _make_mock_pr(number=5, base_ref="main")
        mock_repo.get_pull.return_value = mock_pr
        mock_pr.get_reviews.return_value = [_make_mock_review("APPROVED")]
        status = MagicMock()
        status.merged = True
        status.sha = "abcdef1234567890"
        status.message = "Merged"
        mock_pr.merge.return_value = status

        req = MergePullRequestRequest(owner="org", repo="repo", pr_number=5)
        resp = await svc.merge_pull_request(req)

        assert resp.merged is True
        assert resp.sha == "abcdef1234567890"
        assert resp.pr_number == 5
        mock_pr.merge.assert_called_once_with(merge_method="merge")

    @pytest.mark.asyncio
    async def test_raises_when_review_required_but_not_approved(self) -> None:
        svc = _make_service({"allowed_repos": ["org/repo"], "require_pr_review": True})
        mock_repo = svc._gh.get_repo.return_value
        mock_pr = _make_mock_pr(number=5, base_ref="main")
        mock_repo.get_pull.return_value = mock_pr
        mock_pr.get_reviews.return_value = [_make_mock_review("COMMENTED")]

        req = MergePullRequestRequest(owner="org", repo="repo", pr_number=5)
        with pytest.raises(GitHubAuthorizationError, match="no approved review"):
            await svc.merge_pull_request(req)

        mock_pr.merge.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_review_check_when_not_required(self) -> None:
        svc = _make_service({"allowed_repos": ["org/repo"], "require_pr_review": False})
        mock_repo = svc._gh.get_repo.return_value
        mock_pr = _make_mock_pr(number=5, base_ref="main")
        mock_repo.get_pull.return_value = mock_pr
        status = MagicMock()
        status.merged = True
        status.sha = "abc123"
        status.message = "Merged"
        mock_pr.merge.return_value = status

        req = MergePullRequestRequest(owner="org", repo="repo", pr_number=5)
        await svc.merge_pull_request(req)

        mock_pr.get_reviews.assert_not_called()

    @pytest.mark.asyncio
    async def test_denies_repo_not_in_allowlist_before_api_call(self) -> None:
        svc = _make_service({"allowed_repos": ["org/other-repo"]})

        req = MergePullRequestRequest(owner="org", repo="repo", pr_number=5)
        with pytest.raises(GitHubAuthorizationError):
            await svc.merge_pull_request(req)

        svc._gh.get_repo.assert_not_called()

    @pytest.mark.asyncio
    async def test_denies_rebase_when_allow_force_push_false_before_api_call(
        self,
    ) -> None:
        svc = _make_service({"allowed_repos": ["org/repo"], "allow_force_push": False})

        req = MergePullRequestRequest(
            owner="org", repo="repo", pr_number=5, merge_method="rebase"
        )
        with pytest.raises(GitHubAuthorizationError, match="Rebase merge is disabled"):
            await svc.merge_pull_request(req)

        svc._gh.get_repo.assert_not_called()

    @pytest.mark.asyncio
    async def test_allows_rebase_when_allow_force_push_true(self) -> None:
        svc = _make_service(
            {
                "allowed_repos": ["org/repo"],
                "allow_force_push": True,
                "require_pr_review": False,
            }
        )
        mock_repo = svc._gh.get_repo.return_value
        mock_pr = _make_mock_pr(number=5, base_ref="main")
        mock_repo.get_pull.return_value = mock_pr
        status = MagicMock()
        status.merged = True
        status.sha = "abc123"
        status.message = "Merged"
        mock_pr.merge.return_value = status

        req = MergePullRequestRequest(
            owner="org", repo="repo", pr_number=5, merge_method="rebase"
        )
        await svc.merge_pull_request(req)

        mock_pr.merge.assert_called_once_with(merge_method="rebase")

    @pytest.mark.asyncio
    async def test_denies_protected_base_branch_before_review_check(self) -> None:
        svc = _make_service(
            {
                "allowed_repos": ["org/repo"],
                "protected_branches": ["main"],
                "require_pr_review": True,
            }
        )
        mock_repo = svc._gh.get_repo.return_value
        mock_pr = _make_mock_pr(number=5, base_ref="main")
        mock_repo.get_pull.return_value = mock_pr

        req = MergePullRequestRequest(owner="org", repo="repo", pr_number=5)
        with pytest.raises(GitHubAuthorizationError):
            await svc.merge_pull_request(req)

        mock_pr.get_reviews.assert_not_called()
        mock_pr.merge.assert_not_called()

    @pytest.mark.asyncio
    async def test_passes_commit_title_and_message_when_set(self) -> None:
        svc = _make_service({"allowed_repos": ["org/repo"], "require_pr_review": False})
        mock_repo = svc._gh.get_repo.return_value
        mock_pr = _make_mock_pr(number=5, base_ref="main")
        mock_repo.get_pull.return_value = mock_pr
        status = MagicMock()
        status.merged = True
        status.sha = "abc123"
        status.message = "Merged"
        mock_pr.merge.return_value = status

        req = MergePullRequestRequest(
            owner="org",
            repo="repo",
            pr_number=5,
            commit_title="Custom title",
            commit_message="Custom message",
        )
        await svc.merge_pull_request(req)

        mock_pr.merge.assert_called_once_with(
            merge_method="merge",
            commit_title="Custom title",
            commit_message="Custom message",
        )

    @pytest.mark.asyncio
    async def test_handles_missing_sha_and_message_on_status(self) -> None:
        svc = _make_service({"allowed_repos": ["org/repo"], "require_pr_review": False})
        mock_repo = svc._gh.get_repo.return_value
        mock_pr = _make_mock_pr(number=5, base_ref="main")
        mock_repo.get_pull.return_value = mock_pr
        status = MagicMock()
        status.merged = False
        status.sha = None
        status.message = None
        mock_pr.merge.return_value = status

        req = MergePullRequestRequest(owner="org", repo="repo", pr_number=5)
        resp = await svc.merge_pull_request(req)

        assert resp.merged is False
        assert resp.sha == ""
        assert resp.message == ""

    @pytest.mark.asyncio
    async def test_writes_audit_log_with_truncated_sha(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.log"
        svc = _make_service(
            {
                "allowed_repos": ["org/repo"],
                "require_pr_review": False,
                "audit_log_path": str(log_file),
            }
        )
        mock_repo = svc._gh.get_repo.return_value
        mock_pr = _make_mock_pr(number=5, base_ref="main")
        mock_repo.get_pull.return_value = mock_pr
        status = MagicMock()
        status.merged = True
        status.sha = "abcdef1234567890"
        status.message = "Merged"
        mock_pr.merge.return_value = status

        req = MergePullRequestRequest(
            owner="org", repo="repo", pr_number=5, merge_method="squash"
        )
        await svc.merge_pull_request(req)

        content = log_file.read_text()
        assert "op=merge_pull_request" in content
        assert "repo='org/repo'" in content
        assert "pr=5" in content
        assert "method='squash'" in content
        assert "merged=True" in content
        assert "sha='abcdef12'" in content
