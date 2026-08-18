"""tests/mcp_servers/github/test_service_dispatch.py

Characterization tests for scripts/mcp_servers/github/service_dispatch.py.

Baseline coverage for this file was 67% (verified during the 04_refactor.md
sweep of this subsystem): the `fmt_*` wrapper methods that only format an
already-mocked business-layer response were largely untested, and
`get_dispatch_table()` had zero direct test invocations anywhere in the
suite (line covering its `return {` was never executed).

These tests lock:
- the exact, verbatim string output of each previously-uncovered `fmt_*`
  method, in both the "has results" and "empty results" branches where both
  exist
- the exact key set and key -> bound-method mapping of `get_dispatch_table()`,
  so a future refactor of the dispatch-table builder can be verified
  byte-for-byte against this recorded shape

Each `fmt_*` method under test delegates I/O to a business-layer method
(e.g. `list_branches`, `get_commit`) that is monkeypatched directly on the
instance with a canned response; this isolates the formatting responsibility
that lives in this file from the GitHub-API-calling responsibility that
lives in service_business.py / service_*.py mixins (already covered by
their own test files).
"""

from __future__ import annotations

import types
from unittest.mock import AsyncMock, MagicMock

from mcp_servers.github.github_models import GitHubConfig
from mcp_servers.github.models_base import IssueInfo, PullRequestInfo
from mcp_servers.github.models_file import (
    CreateOrUpdateFileResponse,
    DeleteRepoFileResponse,
    PushFilesResponse,
)
from mcp_servers.github.models_issues import (
    GetIssueResponse,
    ListIssuesResponse,
    SearchIssuesResponse,
)
from mcp_servers.github.models_pull_requests import (
    GetPullRequestResponse,
    ListPullRequestsResponse,
    SearchPullRequestsResponse,
    UpdatePullRequestResponse,
)
from mcp_servers.github.models_repository import (
    BranchInfo,
    CodeSearchResult,
    CommitDetail,
    CommitInfo,
    GetCommitResponse,
    ListBranchesResponse,
    ListCommitsResponse,
    RepositoryInfo,
    SearchCodeResponse,
    SearchRepositoriesResponse,
)
from mcp_servers.github.service_dispatch import GitHubService


def _make_service() -> GitHubService:
    """Minimal GitHubService instance; the underlying GitHub client is never called."""
    return GitHubService(
        gh=MagicMock(), cfg=GitHubConfig.from_dict({"allowed_repos": ["org/repo"]})
    )


def _make_issue(**overrides: object) -> IssueInfo:
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


def _make_pr(**overrides: object) -> PullRequestInfo:
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


class TestFmtSearchRepositories:
    async def test_results_render_as_markdown_links_with_stars(self) -> None:
        svc = _make_service()
        repo = RepositoryInfo(
            full_name="org/repo",
            description="A repo",
            url="https://github.com/org/repo",
            stars=42,
            forks=3,
            language="Python",
            updated_at="2026-01-01T00:00:00Z",
        )
        svc.search_repositories = AsyncMock(  # type: ignore[method-assign]  — instance-level stub replaces the business-layer call; only fmt_* formatting is under test here
            return_value=SearchRepositoriesResponse(query="q", results=[repo])
        )

        result = await svc.fmt_search_repositories({"query": "q"})

        assert result == "[org/repo](https://github.com/org/repo) ★42\nA repo"

    async def test_no_results_returns_placeholder(self) -> None:
        svc = _make_service()
        svc.search_repositories = AsyncMock(  # type: ignore[method-assign]  — instance-level stub replaces the business-layer call; only fmt_* formatting is under test here
            return_value=SearchRepositoriesResponse(query="q", results=[])
        )

        result = await svc.fmt_search_repositories({"query": "q"})

        assert result == "No results found."


class TestFmtListBranches:
    async def test_branches_render_with_protected_marker(self) -> None:
        svc = _make_service()
        branches = [
            BranchInfo(name="main", sha="abcdef1234567890", protected=True),
            BranchInfo(name="dev", sha="0123456789abcdef", protected=False),
        ]
        svc.list_branches = AsyncMock(  # type: ignore[method-assign]  — instance-level stub replaces the business-layer call; only fmt_* formatting is under test here
            return_value=ListBranchesResponse(branches=branches)
        )

        result = await svc.fmt_list_branches({"owner": "org", "repo": "repo"})

        assert result == "main (abcdef12) [protected]\ndev (01234567)"

    async def test_no_branches_returns_placeholder(self) -> None:
        svc = _make_service()
        svc.list_branches = AsyncMock(  # type: ignore[method-assign]  — instance-level stub replaces the business-layer call; only fmt_* formatting is under test here
            return_value=ListBranchesResponse(branches=[])
        )

        result = await svc.fmt_list_branches({"owner": "org", "repo": "repo"})

        assert result == "No branches found."


class TestFmtListCommits:
    async def test_commits_render_sha_message_author(self) -> None:
        svc = _make_service()
        commits = [
            CommitInfo(
                sha="deadbeef00112233",
                message="Fix bug",
                author="alice",
                authored_at="2026-01-01T00:00:00Z",
                url="https://github.com/org/repo/commit/deadbeef",
            )
        ]
        svc.list_commits = AsyncMock(  # type: ignore[method-assign]  — instance-level stub replaces the business-layer call; only fmt_* formatting is under test here
            return_value=ListCommitsResponse(commits=commits)
        )

        result = await svc.fmt_list_commits({"owner": "org", "repo": "repo"})

        assert result == "deadbeef Fix bug (alice)"

    async def test_no_commits_returns_placeholder(self) -> None:
        svc = _make_service()
        svc.list_commits = AsyncMock(  # type: ignore[method-assign]  — instance-level stub replaces the business-layer call; only fmt_* formatting is under test here
            return_value=ListCommitsResponse(commits=[])
        )

        result = await svc.fmt_list_commits({"owner": "org", "repo": "repo"})

        assert result == "No commits found."


class TestFmtGetCommit:
    async def test_commit_details_render_all_fields(self) -> None:
        svc = _make_service()
        detail = CommitDetail(
            sha="cafebabe00112233",
            message="Add feature",
            author="bob",
            authored_at="2026-01-01T00:00:00Z",
            url="https://github.com/org/repo/commit/cafebabe",
            files_changed=3,
        )
        svc.get_commit = AsyncMock(  # type: ignore[method-assign]  — instance-level stub replaces the business-layer call; only fmt_* formatting is under test here
            return_value=GetCommitResponse(commit=detail)
        )

        result = await svc.fmt_get_commit(
            {"owner": "org", "repo": "repo", "sha": "cafebabe"}
        )

        assert result == (
            "cafebabe Add feature\n"
            "Author: bob (2026-01-01T00:00:00Z)\n"
            "Files changed: 3\nURL: https://github.com/org/repo/commit/cafebabe"
        )


class TestFmtSearchCode:
    async def test_results_render_as_path_links(self) -> None:
        svc = _make_service()
        results = [
            CodeSearchResult(
                repository="org/repo",
                path="src/main.py",
                url="https://github.com/org/repo/blob/main/src/main.py",
                score=1.0,
            )
        ]
        svc.search_code = AsyncMock(  # type: ignore[method-assign]  — instance-level stub replaces the business-layer call; only fmt_* formatting is under test here
            return_value=SearchCodeResponse(query="q", results=results)
        )

        result = await svc.fmt_search_code({"query": "q"})

        assert (
            result
            == "[org/repo/src/main.py](https://github.com/org/repo/blob/main/src/main.py)"
        )

    async def test_no_results_returns_placeholder(self) -> None:
        svc = _make_service()
        svc.search_code = AsyncMock(  # type: ignore[method-assign]  — instance-level stub replaces the business-layer call; only fmt_* formatting is under test here
            return_value=SearchCodeResponse(query="q", results=[])
        )

        result = await svc.fmt_search_code({"query": "q"})

        assert result == "No results found."


class TestFmtGetFileContents:
    async def test_returns_raw_content_unmodified(self) -> None:
        from mcp_servers.github.models_file import GetFileContentsResponse

        svc = _make_service()
        svc.get_file_contents = AsyncMock(  # type: ignore[method-assign]  — instance-level stub replaces the business-layer call; only fmt_* formatting is under test here
            return_value=GetFileContentsResponse(
                path="a.txt",
                content="hello world",
                sha="abc",
                size=11,
                encoding="utf-8",
            )
        )

        result = await svc.fmt_get_file_contents(
            {"owner": "org", "repo": "repo", "path": "a.txt"}
        )

        assert result == "hello world"


class TestFmtCreateOrUpdateFileNonDryRun:
    async def test_execute_path_calls_service_and_formats_result(self) -> None:
        svc = _make_service()
        svc.create_or_update_file = AsyncMock(  # type: ignore[method-assign]  — instance-level stub replaces the business-layer call; only fmt_* formatting is under test here
            return_value=CreateOrUpdateFileResponse(
                path="a.txt", commit_sha="1234567890abcdef", operation="created"
            )
        )

        result = await svc.fmt_create_or_update_file(
            {
                "owner": "org",
                "repo": "repo",
                "path": "a.txt",
                "content": "x",
                "message": "add a.txt",
                "dry_run": False,
            }
        )

        assert result == "created: a.txt (commit: 12345678)"
        svc.create_or_update_file.assert_awaited_once()


class TestFmtPushFilesNonDryRun:
    async def test_execute_path_calls_service_and_formats_result(self) -> None:
        svc = _make_service()
        svc.push_files = AsyncMock(  # type: ignore[method-assign]  — instance-level stub replaces the business-layer call; only fmt_* formatting is under test here
            return_value=PushFilesResponse(
                branch="main", commit_sha="fedcba0987654321", files_pushed=2
            )
        )

        result = await svc.fmt_push_files(
            {
                "owner": "org",
                "repo": "repo",
                "branch": "main",
                "files": [
                    {"path": "a.txt", "content": "x"},
                    {"path": "b.txt", "content": "y"},
                ],
                "message": "push",
                "dry_run": False,
            }
        )

        assert result == "Pushed: branch=main files=2 commit=fedcba09"
        svc.push_files.assert_awaited_once()


class TestFmtDeleteFileNonDryRun:
    async def test_execute_path_calls_service_and_formats_result(self) -> None:
        svc = _make_service()
        svc.delete_repo_file = AsyncMock(  # type: ignore[method-assign]  — instance-level stub replaces the business-layer call; only fmt_* formatting is under test here
            return_value=DeleteRepoFileResponse(
                path="a.txt", commit_sha="1122334455667788"
            )
        )

        result = await svc.fmt_delete_file(
            {
                "owner": "org",
                "repo": "repo",
                "path": "a.txt",
                "message": "rm",
                "sha": "abc",
            }
        )

        assert result == "Deleted: a.txt (commit: 11223344)"
        svc.delete_repo_file.assert_awaited_once()


class TestFmtListIssues:
    async def test_issues_render_via_shared_issue_line_formatter(self) -> None:
        svc = _make_service()
        issue = _make_issue(number=5, state="open", title="Bug", labels=[])
        svc.list_issues = AsyncMock(  # type: ignore[method-assign]  — instance-level stub replaces the business-layer call; only fmt_* formatting is under test here
            return_value=ListIssuesResponse(issues=[issue])
        )

        result = await svc.fmt_list_issues({"owner": "org", "repo": "repo"})

        assert result == f"#5 [open] Bug\n{issue.url}"

    async def test_no_issues_returns_placeholder(self) -> None:
        svc = _make_service()
        svc.list_issues = AsyncMock(  # type: ignore[method-assign]  — instance-level stub replaces the business-layer call; only fmt_* formatting is under test here
            return_value=ListIssuesResponse(issues=[])
        )

        result = await svc.fmt_list_issues({"owner": "org", "repo": "repo"})

        assert result == "No issues found."


class TestFmtGetIssue:
    async def test_issue_details_render_number_state_title_body_url(self) -> None:
        svc = _make_service()
        issue = _make_issue(
            number=7, state="closed", title="Fixed", body="Details here"
        )
        svc.get_issue = AsyncMock(  # type: ignore[method-assign]  — instance-level stub replaces the business-layer call; only fmt_* formatting is under test here
            return_value=GetIssueResponse(issue=issue)
        )

        result = await svc.fmt_get_issue(
            {"owner": "org", "repo": "repo", "issue_number": 7}
        )

        assert result == f"#7 [closed] Fixed\nDetails here\nURL: {issue.url}"


class TestFmtSearchIssues:
    async def test_results_render_via_shared_issue_line_formatter(self) -> None:
        svc = _make_service()
        issue = _make_issue(number=3, state="open", title="Found", labels=["bug"])
        svc.search_issues = AsyncMock(  # type: ignore[method-assign]  — instance-level stub replaces the business-layer call; only fmt_* formatting is under test here
            return_value=SearchIssuesResponse(query="q", results=[issue])
        )

        result = await svc.fmt_search_issues({"query": "q"})

        assert result == f"#3 [open] labels=[bug] Found\n{issue.url}"

    async def test_no_results_returns_placeholder(self) -> None:
        svc = _make_service()
        svc.search_issues = AsyncMock(  # type: ignore[method-assign]  — instance-level stub replaces the business-layer call; only fmt_* formatting is under test here
            return_value=SearchIssuesResponse(query="q", results=[])
        )

        result = await svc.fmt_search_issues({"query": "q"})

        assert result == "No results found."


class TestFmtListPullRequests:
    async def test_prs_render_via_shared_pr_line_formatter(self) -> None:
        svc = _make_service()
        pr = _make_pr(
            number=2, state="open", title="Feature", head_ref="f", base_ref="main"
        )
        svc.list_pull_requests = AsyncMock(  # type: ignore[method-assign]  — instance-level stub replaces the business-layer call; only fmt_* formatting is under test here
            return_value=ListPullRequestsResponse(pull_requests=[pr])
        )

        result = await svc.fmt_list_pull_requests({"owner": "org", "repo": "repo"})

        assert result == f"#2 [open] Feature (f->main)\n{pr.url}"

    async def test_no_prs_returns_placeholder(self) -> None:
        svc = _make_service()
        svc.list_pull_requests = AsyncMock(  # type: ignore[method-assign]  — instance-level stub replaces the business-layer call; only fmt_* formatting is under test here
            return_value=ListPullRequestsResponse(pull_requests=[])
        )

        result = await svc.fmt_list_pull_requests({"owner": "org", "repo": "repo"})

        assert result == "No pull requests found."


class TestFmtGetPullRequest:
    async def test_pr_details_render_number_state_title_refs_body_url(self) -> None:
        svc = _make_service()
        pr = _make_pr(
            number=11,
            state="open",
            title="Big change",
            head_ref="feat",
            base_ref="main",
            body="Why this matters",
        )
        svc.get_pull_request = AsyncMock(  # type: ignore[method-assign]  — instance-level stub replaces the business-layer call; only fmt_* formatting is under test here
            return_value=GetPullRequestResponse(pull_request=pr)
        )

        result = await svc.fmt_get_pull_request(
            {"owner": "org", "repo": "repo", "pr_number": 11}
        )

        assert result == (
            "#11 [open] Big change\n"
            "head: feat → base: main\n"
            f"Why this matters\nURL: {pr.url}"
        )


class TestFmtSearchPullRequests:
    async def test_results_render_via_shared_issue_line_formatter(self) -> None:
        svc = _make_service()
        # Search PR results reuse IssueInfo (GitHub search API returns Issue objects for PRs).
        issue = _make_issue(number=21, state="open", title="Search hit")
        svc.search_pull_requests = AsyncMock(  # type: ignore[method-assign]  — instance-level stub replaces the business-layer call; only fmt_* formatting is under test here
            return_value=SearchPullRequestsResponse(query="q", results=[issue])
        )

        result = await svc.fmt_search_pull_requests({"query": "q"})

        assert result == f"#21 [open] Search hit\n{issue.url}"

    async def test_no_results_returns_placeholder(self) -> None:
        svc = _make_service()
        svc.search_pull_requests = AsyncMock(  # type: ignore[method-assign]  — instance-level stub replaces the business-layer call; only fmt_* formatting is under test here
            return_value=SearchPullRequestsResponse(query="q", results=[])
        )

        result = await svc.fmt_search_pull_requests({"query": "q"})

        assert result == "No results found."


class TestFmtUpdatePullRequest:
    async def test_dry_run_preview_lists_title_and_state_changes(self) -> None:
        svc = _make_service()
        svc.update_pull_request = AsyncMock()  # type: ignore[method-assign]  — instance-level stub replaces the business-layer call; only fmt_* formatting is under test here

        result = await svc.fmt_update_pull_request(
            {
                "owner": "org",
                "repo": "repo",
                "pr_number": 4,
                "title": "New title",
                "state": "closed",
                "dry_run": True,
            }
        )

        assert result == (
            '{"dry_run":true,"preview":"Would update PR #4 in org/repo: '
            "title='New title', state=closed\"}"
        )
        svc.update_pull_request.assert_not_awaited()

    async def test_dry_run_preview_no_changes_placeholder(self) -> None:
        svc = _make_service()
        svc.update_pull_request = AsyncMock()  # type: ignore[method-assign]  — instance-level stub replaces the business-layer call; only fmt_* formatting is under test here

        result = await svc.fmt_update_pull_request(
            {"owner": "org", "repo": "repo", "pr_number": 4, "dry_run": True}
        )

        assert '"Would update PR #4 in org/repo: (no changes)"' in result

    async def test_non_dry_run_calls_service_and_formats_result(self) -> None:
        svc = _make_service()
        pr = _make_pr(number=4, state="closed", title="New title")
        svc.update_pull_request = AsyncMock(  # type: ignore[method-assign]  — instance-level stub replaces the business-layer call; only fmt_* formatting is under test here
            return_value=UpdatePullRequestResponse(pull_request=pr)
        )

        result = await svc.fmt_update_pull_request(
            {
                "owner": "org",
                "repo": "repo",
                "pr_number": 4,
                "title": "New title",
                "dry_run": False,
            }
        )

        assert result == f"Updated: #4 [closed] New title\n{pr.url}"
        svc.update_pull_request.assert_awaited_once()


class TestGetDispatchTable:
    """Lock the exact shape of the MCP tool-name -> handler dispatch table.

    Every key here is a public MCP tool name exposed by the github MCP
    server; renaming a key or repointing it to a different handler is a
    breaking change to the server's public API and must never happen as a
    side effect of refactoring this file.
    """

    EXPECTED_TOOL_TO_METHOD_NAME = {
        "github_search_repositories": "fmt_search_repositories",
        "github_get_file_contents": "fmt_get_file_contents",
        "github_list_issues": "fmt_list_issues",
        "github_search_code": "fmt_search_code",
        "github_get_issue": "fmt_get_issue",
        "github_create_issue": "fmt_create_issue",
        "github_list_pull_requests": "fmt_list_pull_requests",
        "github_get_pull_request": "fmt_get_pull_request",
        "github_list_commits": "fmt_list_commits",
        "github_create_pull_request": "fmt_create_pull_request",
        "github_create_branch": "fmt_create_branch",
        "github_create_or_update_file": "fmt_create_or_update_file",
        "github_add_issue_comment": "fmt_add_issue_comment",
        "github_push_files": "fmt_push_files",
        "github_delete_file": "fmt_delete_file",
        "github_list_branches": "fmt_list_branches",
        "github_get_commit": "fmt_get_commit",
        "github_search_issues": "fmt_search_issues",
        "github_search_pull_requests": "fmt_search_pull_requests",
        "github_update_pull_request": "fmt_update_pull_request",
        "github_merge_pull_request": "fmt_merge_pull_request",
    }

    def test_key_set_matches_exactly(self) -> None:
        svc = _make_service()

        table = svc.get_dispatch_table()

        assert set(table.keys()) == set(self.EXPECTED_TOOL_TO_METHOD_NAME.keys())

    def test_each_tool_name_maps_to_the_expected_bound_method(self) -> None:
        svc = _make_service()

        table = svc.get_dispatch_table()

        for tool_name, method_name in self.EXPECTED_TOOL_TO_METHOD_NAME.items():
            handler = table[tool_name]
            expected_bound_method = getattr(svc, method_name)
            assert isinstance(handler, types.MethodType)
            assert isinstance(expected_bound_method, types.MethodType)
            assert handler.__func__ is expected_bound_method.__func__, (
                f"{tool_name} must dispatch to {method_name}"
            )
            assert handler.__self__ is svc

    def test_table_size_matches_tool_count(self) -> None:
        svc = _make_service()

        table = svc.get_dispatch_table()

        assert len(table) == len(self.EXPECTED_TOOL_TO_METHOD_NAME) == 21

    def test_fresh_table_built_on_each_call(self) -> None:
        """get_dispatch_table() is called per-request in github_server.py; confirm
        it does not memoize/cache a single dict instance across calls."""
        svc = _make_service()

        first = svc.get_dispatch_table()
        second = svc.get_dispatch_table()

        assert first is not second
        assert first == {k: first[k] for k in first}  # sanity: still a plain dict
