"""tests/mcp_servers/github/test_service_issues.py

Characterization tests closing coverage gaps in
`mcp_servers/github/service_issues.py` (IssuesOps) found before a refactor
pass (04_refactor.md sweep of the `scripts/mcp_servers/github/` subsystem).
These lock existing behavior only -- no source logic is asserted to be
"correct", only that it behaves the way it currently does.

Baseline coverage (before this file): 31% -- lines 42-51, 56-62, 66-86,
90-101, 108-125 were unexercised. The existing suite
(`test_github_mcp_service.py`) only exercises `create_issue` and
`add_issue_comment` with the service method itself patched via
`AsyncMock` (verified via `rg list_issues|get_issue|create_issue|
search_issues|add_issue_comment tests/mcp_servers/github/
test_github_mcp_service.py`), so the `_sync` closures that hold the
actual PyGithub call sequence, guard ordering, and response construction
never ran. `list_issues`, `get_issue`, and `search_issues` had no coverage
at all. These tests let `_run_github` execute for real
(`asyncio.to_thread`) against a mocked `self._gh` PyGithub client, so the
closures themselves are exercised:

  - list_issues: repo.get_issues(state=...) call, per_page slicing,
    issue_to_info conversion
  - get_issue: repo.get_issue(number=...) call, issue_to_info conversion
  - create_issue: _assert_allowed_repo guard runs before the API call,
    label/assignee defaulting, audit log written
  - search_issues: self._gh.search_issues(query=...) call, per_page
    slicing
  - add_issue_comment: _assert_allowed_repo guard runs before the API
    call, comment creation, audit log written
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from mcp_servers.github.models_config import GitHubAuthorizationError, GitHubConfig
from mcp_servers.github.models_issues import (
    AddIssueCommentRequest,
    CreateIssueRequest,
    GetIssueRequest,
    ListIssuesRequest,
    SearchIssuesRequest,
)
from mcp_servers.github.service_dispatch import GitHubService


def _make_service(cfg: dict | None = None) -> GitHubService:
    """GitHubService with a MagicMock GitHub client; no real API calls are made."""
    raw = cfg or {"allowed_repos": ["org/repo"]}
    return GitHubService(gh=MagicMock(), cfg=GitHubConfig.from_dict(raw))


def _make_mock_issue(**overrides: object) -> MagicMock:
    issue = MagicMock()
    issue.number = overrides.get("number", 1)
    issue.title = overrides.get("title", "Bug report")
    issue.state = overrides.get("state", "open")
    issue.html_url = overrides.get("html_url", "https://github.com/org/repo/issues/1")
    issue.body = overrides.get("body", "Something is broken")
    issue.created_at = overrides.get("created_at", datetime(2026, 1, 1))
    issue.updated_at = overrides.get("updated_at", datetime(2026, 1, 2))
    label = MagicMock()
    label.name = "bug"
    issue.labels = overrides.get("labels", [label])
    assignee = MagicMock()
    assignee.login = "octocat"
    issue.assignees = overrides.get("assignees", [assignee])
    return issue


# ── list_issues ──────────────────────────────────────────────────────────────


class TestListIssues:
    @pytest.mark.asyncio
    async def test_returns_converted_issues(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_repo.get_issues.return_value = [_make_mock_issue(number=42)]

        req = ListIssuesRequest(owner="org", repo="repo")
        resp = await svc.list_issues(req)

        assert len(resp.issues) == 1
        assert resp.issues[0].number == 42
        assert resp.issues[0].labels == ["bug"]
        assert resp.issues[0].assignees == ["octocat"]
        svc._gh.get_repo.assert_called_once_with("org/repo")
        mock_repo.get_issues.assert_called_once_with(state="open")

    @pytest.mark.asyncio
    async def test_passes_requested_state(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_repo.get_issues.return_value = []

        req = ListIssuesRequest(owner="org", repo="repo", state="closed")
        await svc.list_issues(req)

        mock_repo.get_issues.assert_called_once_with(state="closed")

    @pytest.mark.asyncio
    async def test_truncates_to_per_page(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_repo.get_issues.return_value = [
            _make_mock_issue(number=n) for n in range(5)
        ]

        req = ListIssuesRequest(owner="org", repo="repo", per_page=2)
        resp = await svc.list_issues(req)

        assert [i.number for i in resp.issues] == [0, 1]

    @pytest.mark.asyncio
    async def test_per_page_clamped_to_config_max(self) -> None:
        svc = _make_service({"allowed_repos": ["org/repo"], "max_per_page": 3})
        mock_repo = svc._gh.get_repo.return_value
        mock_repo.get_issues.return_value = [
            _make_mock_issue(number=n) for n in range(10)
        ]

        req = ListIssuesRequest(owner="org", repo="repo", per_page=999)
        resp = await svc.list_issues(req)

        assert len(resp.issues) == 3


# ── get_issue ────────────────────────────────────────────────────────────────


class TestGetIssue:
    @pytest.mark.asyncio
    async def test_returns_converted_issue(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_repo.get_issue.return_value = _make_mock_issue(number=7, title="Fix crash")

        req = GetIssueRequest(owner="org", repo="repo", issue_number=7)
        resp = await svc.get_issue(req)

        assert resp.issue.number == 7
        assert resp.issue.title == "Fix crash"
        mock_repo.get_issue.assert_called_once_with(number=7)


# ── create_issue ─────────────────────────────────────────────────────────────


class TestCreateIssue:
    @pytest.mark.asyncio
    async def test_creates_with_defaults_and_returns_response(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_repo.create_issue.return_value = _make_mock_issue(
            number=99, title="New bug", labels=[], assignees=[]
        )

        req = CreateIssueRequest(owner="org", repo="repo", title="New bug")
        resp = await svc.create_issue(req)

        assert resp.issue.number == 99
        mock_repo.create_issue.assert_called_once_with(
            title="New bug", body=None, labels=[], assignees=[]
        )

    @pytest.mark.asyncio
    async def test_passes_body_labels_and_assignees(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_repo.create_issue.return_value = _make_mock_issue()

        req = CreateIssueRequest(
            owner="org",
            repo="repo",
            title="New bug",
            body="Details here",
            labels=["bug", "urgent"],
            assignees=["octocat"],
        )
        await svc.create_issue(req)

        mock_repo.create_issue.assert_called_once_with(
            title="New bug",
            body="Details here",
            labels=["bug", "urgent"],
            assignees=["octocat"],
        )

    @pytest.mark.asyncio
    async def test_denies_repo_not_in_allowlist_before_api_call(self) -> None:
        svc = _make_service({"allowed_repos": ["org/other-repo"]})

        req = CreateIssueRequest(owner="org", repo="repo", title="New bug")
        with pytest.raises(GitHubAuthorizationError):
            await svc.create_issue(req)

        svc._gh.get_repo.assert_not_called()

    @pytest.mark.asyncio
    async def test_writes_audit_log_with_repo_number_and_title(
        self, tmp_path: Path
    ) -> None:
        log_file = tmp_path / "audit.log"
        svc = _make_service(
            {"allowed_repos": ["org/repo"], "audit_log_path": str(log_file)}
        )
        mock_repo = svc._gh.get_repo.return_value
        mock_repo.create_issue.return_value = _make_mock_issue(number=55)

        req = CreateIssueRequest(owner="org", repo="repo", title="New bug")
        await svc.create_issue(req)

        content = log_file.read_text()
        assert "op=create_issue" in content
        assert "repo='org/repo'" in content
        assert "number=55" in content
        assert "title='New bug'" in content


# ── search_issues ────────────────────────────────────────────────────────────


class TestSearchIssues:
    @pytest.mark.asyncio
    async def test_returns_query_and_converted_results(self) -> None:
        svc = _make_service()
        svc._gh.search_issues.return_value = [_make_mock_issue(number=3)]

        req = SearchIssuesRequest(query="repo:org/repo is:issue label:bug")
        resp = await svc.search_issues(req)

        assert resp.query == "repo:org/repo is:issue label:bug"
        assert len(resp.results) == 1
        assert resp.results[0].number == 3
        svc._gh.search_issues.assert_called_once_with(
            query="repo:org/repo is:issue label:bug"
        )

    @pytest.mark.asyncio
    async def test_truncates_to_per_page(self) -> None:
        svc = _make_service()
        svc._gh.search_issues.return_value = [
            _make_mock_issue(number=n) for n in range(5)
        ]

        req = SearchIssuesRequest(query="test", per_page=2)
        resp = await svc.search_issues(req)

        assert len(resp.results) == 2


# ── add_issue_comment ────────────────────────────────────────────────────────


class TestAddIssueComment:
    @pytest.mark.asyncio
    async def test_posts_comment_and_returns_response(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_comment = MagicMock()
        mock_comment.html_url = "https://github.com/org/repo/issues/5#comment-1"
        mock_repo.get_issue.return_value.create_comment.return_value = mock_comment

        req = AddIssueCommentRequest(
            owner="org", repo="repo", issue_number=5, body="hi"
        )
        resp = await svc.add_issue_comment(req)

        assert resp.issue_number == 5
        assert resp.comment_url == "https://github.com/org/repo/issues/5#comment-1"
        mock_repo.get_issue.assert_called_once_with(number=5)
        mock_repo.get_issue.return_value.create_comment.assert_called_once_with("hi")

    @pytest.mark.asyncio
    async def test_denies_repo_not_in_allowlist_before_api_call(self) -> None:
        svc = _make_service({"allowed_repos": ["org/other-repo"]})

        req = AddIssueCommentRequest(
            owner="org", repo="repo", issue_number=5, body="hi"
        )
        with pytest.raises(GitHubAuthorizationError):
            await svc.add_issue_comment(req)

        svc._gh.get_repo.assert_not_called()

    @pytest.mark.asyncio
    async def test_writes_audit_log_with_repo_and_issue_number(
        self, tmp_path: Path
    ) -> None:
        log_file = tmp_path / "audit.log"
        svc = _make_service(
            {"allowed_repos": ["org/repo"], "audit_log_path": str(log_file)}
        )
        mock_repo = svc._gh.get_repo.return_value
        mock_repo.get_issue.return_value.create_comment.return_value = MagicMock(
            html_url="https://github.com/org/repo/issues/5#comment-1"
        )

        req = AddIssueCommentRequest(
            owner="org", repo="repo", issue_number=5, body="hi"
        )
        await svc.add_issue_comment(req)

        content = log_file.read_text()
        assert "op=add_issue_comment" in content
        assert "repo='org/repo'" in content
        assert "issue=5" in content
