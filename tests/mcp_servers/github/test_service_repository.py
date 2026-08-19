"""tests/mcp_servers/github/test_service_repository.py

Characterization tests closing coverage gaps in
`mcp_servers/github/service_repository.py` (RepositoryOps) found before a
refactor pass (04_refactor.md sweep of the `scripts/mcp_servers/github/`
subsystem). These lock existing behavior only -- no source logic is asserted
to be "correct", only that it behaves the way it currently does.

Baseline coverage (before this file): 27% -- lines 50-69, 73-84, 88-113,
117-136, 141-156, 160-176 were unexercised. The existing suite
(`test_github_mcp_service.py`) only exercises `create_branch` via
`fmt_create_branch`, with the service method itself patched via
`AsyncMock` (verified via `rg
search_repositories|list_branches|list_commits|get_commit|search_code
tests/mcp_servers/github/test_github_mcp_service.py` returning no hits, and
`create_branch` hits all using `new=AsyncMock(...)` patches), so the
`_sync` closures that hold the actual PyGithub call sequence, guard
ordering, and response construction never ran. `search_repositories`,
`list_branches`, `list_commits`, `get_commit`, and `search_code` had no
coverage at all. These tests let `_run_github` execute for real
(`asyncio.to_thread`) against a mocked `self._gh` PyGithub client, so the
closures themselves are exercised:

  - search_repositories: self._gh.search_repositories(query=...) call,
    per_page slicing (via itertools.islice), RepositoryInfo conversion
    (including updated_at.isoformat())
  - list_branches: repo.get_branches() call, per_page slicing, BranchInfo
    conversion
  - create_branch: _assert_allowed_repo guard runs before the API call;
    from_branch omitted falls back to repo.default_branch; from_branch
    given is used as-is; repo.create_git_ref called with
    refs/heads/<branch_name> and the source commit sha; audit log written
    with sha truncated to 8 characters and from_branch defaulted to
    "(default)" when omitted
  - list_commits: no `sha` kwarg passed to repo.get_commits() when
    req.branch is empty, `sha=<branch>` passed when set; commit message
    truncated to its first line; per_page slicing; CommitInfo conversion
  - get_commit: repo.get_commit(sha) call, CommitDetail conversion
    including files_changed=len(commit.files) and message truncated to
    its first line
  - search_code: self._gh.search_code(query=...) call, per_page slicing,
    CodeSearchResult conversion
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from mcp_servers.github.github_models_config import (
    GitHubAuthorizationError,
    GitHubConfig,
)
from mcp_servers.github.github_models_repository import (
    CreateBranchRequest,
    GetCommitRequest,
    ListBranchesRequest,
    ListCommitsRequest,
    SearchCodeRequest,
    SearchRepositoriesRequest,
)
from mcp_servers.github.github_service_dispatch import GitHubService


def _make_service(cfg: dict | None = None) -> GitHubService:
    """GitHubService with a MagicMock GitHub client; no real API calls are made."""
    raw = cfg or {"allowed_repos": ["org/repo"]}
    return GitHubService(gh=MagicMock(), cfg=GitHubConfig.from_dict(raw))


def _make_mock_repo_result(**overrides: object) -> MagicMock:
    r = MagicMock()
    r.full_name = overrides.get("full_name", "org/repo")
    r.description = overrides.get("description", "A repo")
    r.html_url = overrides.get("html_url", "https://github.com/org/repo")
    r.stargazers_count = overrides.get("stargazers_count", 10)
    r.forks_count = overrides.get("forks_count", 2)
    r.language = overrides.get("language", "Python")
    r.updated_at = overrides.get("updated_at", datetime(2026, 1, 2))
    return r


def _make_mock_branch(**overrides: object) -> MagicMock:
    b = MagicMock()
    b.name = overrides.get("name", "main")
    b.commit.sha = overrides.get("sha", "abc123")
    b.protected = overrides.get("protected", False)
    return b


def _make_mock_commit(**overrides: object) -> MagicMock:
    c = MagicMock()
    c.sha = overrides.get("sha", "deadbeef")
    c.commit.message = overrides.get("message", "Fix bug\n\nLonger body text")
    c.commit.author.name = overrides.get("author", "octocat")
    c.commit.author.date = overrides.get("date", datetime(2026, 1, 3))
    c.html_url = overrides.get(
        "html_url", "https://github.com/org/repo/commit/deadbeef"
    )
    return c


def _make_mock_code_result(**overrides: object) -> MagicMock:
    r = MagicMock()
    r.repository.full_name = overrides.get("repository", "org/repo")
    r.path = overrides.get("path", "scripts/foo.py")
    r.html_url = overrides.get(
        "html_url", "https://github.com/org/repo/blob/main/scripts/foo.py"
    )
    r.score = overrides.get("score", 1.5)
    return r


# ── search_repositories ────────────────────────────────────────────────────


class TestSearchRepositories:
    @pytest.mark.asyncio
    async def test_returns_converted_results(self) -> None:
        svc = _make_service()
        svc._gh.search_repositories.return_value = [_make_mock_repo_result()]

        req = SearchRepositoriesRequest(query="lang:python stars:>100")
        resp = await svc.search_repositories(req)

        assert resp.query == "lang:python stars:>100"
        assert len(resp.results) == 1
        assert resp.results[0].full_name == "org/repo"
        assert resp.results[0].updated_at == "2026-01-02T00:00:00"
        svc._gh.search_repositories.assert_called_once_with(
            query="lang:python stars:>100"
        )

    @pytest.mark.asyncio
    async def test_truncates_to_per_page(self) -> None:
        svc = _make_service()
        svc._gh.search_repositories.return_value = [
            _make_mock_repo_result(full_name=f"org/repo{n}") for n in range(5)
        ]

        req = SearchRepositoriesRequest(query="q", per_page=2)
        resp = await svc.search_repositories(req)

        assert [r.full_name for r in resp.results] == ["org/repo0", "org/repo1"]

    @pytest.mark.asyncio
    async def test_per_page_clamped_to_config_max(self) -> None:
        svc = _make_service({"allowed_repos": ["org/repo"], "max_per_page": 3})
        svc._gh.search_repositories.return_value = [
            _make_mock_repo_result(full_name=f"org/repo{n}") for n in range(10)
        ]

        req = SearchRepositoriesRequest(query="q", per_page=999)
        resp = await svc.search_repositories(req)

        assert len(resp.results) == 3


# ── list_branches ────────────────────────────────────────────────────────────


class TestListBranches:
    @pytest.mark.asyncio
    async def test_returns_converted_branches(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_repo.get_branches.return_value = [
            _make_mock_branch(name="main", sha="abc123", protected=True)
        ]

        req = ListBranchesRequest(owner="org", repo="repo")
        resp = await svc.list_branches(req)

        assert len(resp.branches) == 1
        assert resp.branches[0].name == "main"
        assert resp.branches[0].sha == "abc123"
        assert resp.branches[0].protected is True
        svc._gh.get_repo.assert_called_once_with("org/repo")
        mock_repo.get_branches.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_truncates_to_per_page(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_repo.get_branches.return_value = [
            _make_mock_branch(name=f"branch{n}") for n in range(5)
        ]

        req = ListBranchesRequest(owner="org", repo="repo", per_page=2)
        resp = await svc.list_branches(req)

        assert [b.name for b in resp.branches] == ["branch0", "branch1"]


# ── create_branch ────────────────────────────────────────────────────────────


class TestCreateBranch:
    @pytest.mark.asyncio
    async def test_creates_from_default_branch_when_omitted(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_repo.default_branch = "main"
        mock_source = MagicMock()
        mock_source.commit.sha = "sha-of-main"
        mock_repo.get_branch.return_value = mock_source

        req = CreateBranchRequest(owner="org", repo="repo", branch_name="feature-x")
        resp = await svc.create_branch(req)

        mock_repo.get_branch.assert_called_once_with("main")
        mock_repo.create_git_ref.assert_called_once_with(
            ref="refs/heads/feature-x", sha="sha-of-main"
        )
        assert resp.branch_name == "feature-x"
        assert resp.sha == "sha-of-main"

    @pytest.mark.asyncio
    async def test_creates_from_explicit_from_branch(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_source = MagicMock()
        mock_source.commit.sha = "sha-of-develop"
        mock_repo.get_branch.return_value = mock_source

        req = CreateBranchRequest(
            owner="org",
            repo="repo",
            branch_name="feature-x",
            from_branch="develop",
        )
        await svc.create_branch(req)

        mock_repo.get_branch.assert_called_once_with("develop")

    @pytest.mark.asyncio
    async def test_denies_repo_not_in_allowlist_before_api_call(self) -> None:
        svc = _make_service({"allowed_repos": ["org/other-repo"]})

        req = CreateBranchRequest(owner="org", repo="repo", branch_name="feature-x")
        with pytest.raises(GitHubAuthorizationError):
            await svc.create_branch(req)

        svc._gh.get_repo.assert_not_called()

    @pytest.mark.asyncio
    async def test_writes_audit_log_with_truncated_sha_and_default_label(
        self, tmp_path: Path
    ) -> None:
        log_file = tmp_path / "audit.log"
        svc = _make_service(
            {"allowed_repos": ["org/repo"], "audit_log_path": str(log_file)}
        )
        mock_repo = svc._gh.get_repo.return_value
        mock_repo.default_branch = "main"
        mock_source = MagicMock()
        mock_source.commit.sha = "0123456789abcdef"
        mock_repo.get_branch.return_value = mock_source

        req = CreateBranchRequest(owner="org", repo="repo", branch_name="feature-x")
        await svc.create_branch(req)

        content = log_file.read_text()
        assert "op=create_branch" in content
        assert "repo='org/repo'" in content
        assert "branch='feature-x'" in content
        assert "from_branch='(default)'" in content
        assert "sha='01234567'" in content

    @pytest.mark.asyncio
    async def test_writes_audit_log_with_explicit_from_branch(
        self, tmp_path: Path
    ) -> None:
        log_file = tmp_path / "audit.log"
        svc = _make_service(
            {"allowed_repos": ["org/repo"], "audit_log_path": str(log_file)}
        )
        mock_repo = svc._gh.get_repo.return_value
        mock_source = MagicMock()
        mock_source.commit.sha = "0123456789abcdef"
        mock_repo.get_branch.return_value = mock_source

        req = CreateBranchRequest(
            owner="org", repo="repo", branch_name="feature-x", from_branch="develop"
        )
        await svc.create_branch(req)

        content = log_file.read_text()
        assert "from_branch='develop'" in content


# ── list_commits ─────────────────────────────────────────────────────────────


class TestListCommits:
    @pytest.mark.asyncio
    async def test_returns_converted_commits_without_branch(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_repo.get_commits.return_value = [
            _make_mock_commit(sha="abc", message="Fix bug\n\nDetails")
        ]

        req = ListCommitsRequest(owner="org", repo="repo")
        resp = await svc.list_commits(req)

        assert len(resp.commits) == 1
        assert resp.commits[0].sha == "abc"
        assert resp.commits[0].message == "Fix bug"
        mock_repo.get_commits.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_passes_sha_kwarg_when_branch_given(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_repo.get_commits.return_value = []

        req = ListCommitsRequest(owner="org", repo="repo", branch="develop")
        await svc.list_commits(req)

        mock_repo.get_commits.assert_called_once_with(sha="develop")

    @pytest.mark.asyncio
    async def test_truncates_to_per_page(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_repo.get_commits.return_value = [
            _make_mock_commit(sha=f"sha{n}") for n in range(5)
        ]

        req = ListCommitsRequest(owner="org", repo="repo", per_page=2)
        resp = await svc.list_commits(req)

        assert [c.sha for c in resp.commits] == ["sha0", "sha1"]


# ── get_commit ───────────────────────────────────────────────────────────────


class TestGetCommit:
    @pytest.mark.asyncio
    async def test_returns_converted_commit_detail(self) -> None:
        svc = _make_service()
        mock_repo = svc._gh.get_repo.return_value
        mock_commit = _make_mock_commit(sha="deadbeef", message="Fix bug\n\nDetails")
        mock_commit.files = [MagicMock(), MagicMock(), MagicMock()]
        mock_repo.get_commit.return_value = mock_commit

        req = GetCommitRequest(owner="org", repo="repo", sha="deadbeef")
        resp = await svc.get_commit(req)

        assert resp.commit.sha == "deadbeef"
        assert resp.commit.message == "Fix bug"
        assert resp.commit.files_changed == 3
        mock_repo.get_commit.assert_called_once_with("deadbeef")


# ── search_code ──────────────────────────────────────────────────────────────


class TestSearchCode:
    @pytest.mark.asyncio
    async def test_returns_converted_results(self) -> None:
        svc = _make_service()
        svc._gh.search_code.return_value = [_make_mock_code_result()]

        req = SearchCodeRequest(query="filename:agent.py repo:org/repo")
        resp = await svc.search_code(req)

        assert resp.query == "filename:agent.py repo:org/repo"
        assert len(resp.results) == 1
        assert resp.results[0].repository == "org/repo"
        assert resp.results[0].path == "scripts/foo.py"
        svc._gh.search_code.assert_called_once_with(
            query="filename:agent.py repo:org/repo"
        )

    @pytest.mark.asyncio
    async def test_truncates_to_per_page(self) -> None:
        svc = _make_service()
        svc._gh.search_code.return_value = [
            _make_mock_code_result(path=f"scripts/foo{n}.py") for n in range(5)
        ]

        req = SearchCodeRequest(query="q", per_page=2)
        resp = await svc.search_code(req)

        assert [r.path for r in resp.results] == [
            "scripts/foo0.py",
            "scripts/foo1.py",
        ]
