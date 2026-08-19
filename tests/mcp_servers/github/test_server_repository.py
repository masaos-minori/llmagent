"""tests/mcp_servers/github/test_server_repository.py

Characterization tests for scripts/mcp_servers/github/github_server_repository.py's FastAPI route
wiring:
  - POST /search_repositories
  - POST /list_branches
  - POST /create_branch
  - POST /list_commits
  - POST /get_commit
  - POST /search_code

Baseline coverage (before this file): 43% -- lines 39-47, 56-64, 73-81, 90-98, 107-115,
124-132 (the body of every route handler) were unexercised. The existing suite exercises
`GitHubService`'s repository methods directly (`test_service_repository.py`) or via the
`fmt_*`/dispatch wrappers (`test_service_dispatch.py`), but nothing sends an HTTP request
through these routes, so the timing (`time.perf_counter()`) and `_info(...)` structured-logging
calls that live only in server_repository.py never ran.

These tests lock the current, observed behavior only -- they monkeypatch the module-level
`_service` singleton on `github_server` (consumed by `_get_service` in server_common.py) so no
real GitHub/PyGithub access occurs, then assert:
  - the route returns exactly what the (mocked) service call returns, serialized per the
    declared `response_model`
  - the service method is awaited once with a request model built from the posted JSON
  - the expected `_info(...)` structured log line is emitted, with the route-specific kwargs
    the current code passes (the `ms=...` timing value is asserted only to be present/numeric,
    since its exact value is time-dependent).
"""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock

import mcp_servers.github.github_server as github_server
import pytest
from fastapi.testclient import TestClient
from mcp_servers.github.github_models import (
    BranchInfo,
    CodeSearchResult,
    CommitDetail,
    CommitInfo,
    CreateBranchResponse,
    GetCommitResponse,
    ListBranchesResponse,
    ListCommitsResponse,
    RepositoryInfo,
    SearchCodeResponse,
    SearchRepositoriesResponse,
)


class _FakeService:
    """Minimal stand-in for GitHubService, exposing only what server_repository.py touches."""

    def __init__(self) -> None:
        self.search_repositories = AsyncMock()
        self.list_branches = AsyncMock()
        self.create_branch = AsyncMock()
        self.list_commits = AsyncMock()
        self.get_commit = AsyncMock()
        self.search_code = AsyncMock()


@pytest.fixture
def fake_service(monkeypatch: pytest.MonkeyPatch) -> _FakeService:
    svc = _FakeService()
    monkeypatch.setattr(github_server, "_service", svc)
    return svc


@pytest.fixture
def client() -> TestClient:
    return TestClient(github_server.app)


def _log_message(caplog: pytest.LogCaptureFixture) -> str:
    """Return the single captured github_server log record's message."""
    assert len(caplog.records) == 1
    assert caplog.records[0].name == github_server.logger.name
    return caplog.records[0].message


def _sample_repo(full_name: str = "org/repo") -> RepositoryInfo:
    return RepositoryInfo(
        full_name=full_name,
        description="A repository",
        url=f"https://github.com/{full_name}",
        stars=42,
        forks=7,
        language="Python",
        updated_at="2026-01-01T00:00:00Z",
    )


def _sample_branch(name: str = "main") -> BranchInfo:
    return BranchInfo(name=name, sha="abc123def456", protected=True)


def _sample_commit(sha: str = "abc123def456") -> CommitInfo:
    return CommitInfo(
        sha=sha,
        message="Fix the thing",
        author="octocat",
        authored_at="2026-01-01T00:00:00Z",
        url=f"https://github.com/org/repo/commit/{sha}",
    )


def _sample_commit_detail(sha: str = "abc123def456") -> CommitDetail:
    return CommitDetail(
        sha=sha,
        message="Fix the thing",
        author="octocat",
        authored_at="2026-01-01T00:00:00Z",
        url=f"https://github.com/org/repo/commit/{sha}",
        files_changed=3,
    )


def _sample_code_result(path: str = "src/main.py") -> CodeSearchResult:
    return CodeSearchResult(
        repository="org/repo",
        path=path,
        url=f"https://github.com/org/repo/blob/main/{path}",
        score=1.5,
    )


class TestSearchRepositoriesEndpoint:
    def test_success_returns_service_result(
        self,
        client: TestClient,
        fake_service: _FakeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        fake_service.search_repositories.return_value = SearchRepositoriesResponse(
            query="agent language:python", results=[_sample_repo()]
        )
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            resp = client.post(
                "/search_repositories",
                json={"query": "agent language:python"},
            )

        assert resp.status_code == 200
        assert resp.json()["results"][0]["full_name"] == "org/repo"
        fake_service.search_repositories.assert_awaited_once()
        assert fake_service.search_repositories.await_args is not None
        req = fake_service.search_repositories.await_args.args[0]
        assert req.query == "agent language:python"

        message = _log_message(caplog)
        assert message.startswith(
            "op=search_repositories q=agent language:python n=1 ms="
        )
        ms_value = message.rsplit("ms=", 1)[1]
        assert float(ms_value) >= 0

    def test_query_truncated_to_80_chars_in_log(
        self,
        client: TestClient,
        fake_service: _FakeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        long_query = "x" * 200
        fake_service.search_repositories.return_value = SearchRepositoriesResponse(
            query=long_query, results=[]
        )
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            resp = client.post("/search_repositories", json={"query": long_query})

        assert resp.status_code == 200
        assert fake_service.search_repositories.await_args is not None
        req = fake_service.search_repositories.await_args.args[0]
        assert req.query == long_query

        message = _log_message(caplog)
        assert message.startswith(f"op=search_repositories q={'x' * 80} n=0 ms=")


class TestListBranchesEndpoint:
    def test_success_returns_service_result(
        self,
        client: TestClient,
        fake_service: _FakeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        fake_service.list_branches.return_value = ListBranchesResponse(
            branches=[_sample_branch()]
        )
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            resp = client.post(
                "/list_branches",
                json={"owner": "org", "repo": "repo"},
            )

        assert resp.status_code == 200
        assert resp.json()["branches"][0]["name"] == "main"
        fake_service.list_branches.assert_awaited_once()
        assert fake_service.list_branches.await_args is not None
        req = fake_service.list_branches.await_args.args[0]
        assert (req.owner, req.repo) == ("org", "repo")

        message = _log_message(caplog)
        assert message.startswith("op=list_branches repo=org/repo n=1 ms=")


class TestCreateBranchEndpoint:
    def test_success_returns_service_result(
        self,
        client: TestClient,
        fake_service: _FakeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        fake_service.create_branch.return_value = CreateBranchResponse(
            branch_name="feature-branch", sha="abc123def456"
        )
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            resp = client.post(
                "/create_branch",
                json={
                    "owner": "org",
                    "repo": "repo",
                    "branch_name": "feature-branch",
                },
            )

        assert resp.status_code == 200
        assert resp.json() == {
            "branch_name": "feature-branch",
            "sha": "abc123def456",
        }
        fake_service.create_branch.assert_awaited_once()
        assert fake_service.create_branch.await_args is not None
        req = fake_service.create_branch.await_args.args[0]
        assert (req.owner, req.repo, req.branch_name) == (
            "org",
            "repo",
            "feature-branch",
        )

        message = _log_message(caplog)
        assert message.startswith(
            "op=create_branch repo=org/repo branch=feature-branch ms="
        )


class TestListCommitsEndpoint:
    def test_success_returns_service_result(
        self,
        client: TestClient,
        fake_service: _FakeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        fake_service.list_commits.return_value = ListCommitsResponse(
            commits=[_sample_commit()]
        )
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            resp = client.post(
                "/list_commits",
                json={"owner": "org", "repo": "repo"},
            )

        assert resp.status_code == 200
        assert resp.json()["commits"][0]["sha"] == "abc123def456"
        fake_service.list_commits.assert_awaited_once()
        assert fake_service.list_commits.await_args is not None
        req = fake_service.list_commits.await_args.args[0]
        assert (req.owner, req.repo) == ("org", "repo")

        message = _log_message(caplog)
        assert message.startswith("op=list_commits repo=org/repo n=1 ms=")


class TestGetCommitEndpoint:
    def test_success_returns_service_result(
        self,
        client: TestClient,
        fake_service: _FakeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        fake_service.get_commit.return_value = GetCommitResponse(
            commit=_sample_commit_detail()
        )
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            resp = client.post(
                "/get_commit",
                json={"owner": "org", "repo": "repo", "sha": "abc123def456"},
            )

        assert resp.status_code == 200
        assert resp.json()["commit"]["sha"] == "abc123def456"
        fake_service.get_commit.assert_awaited_once()
        assert fake_service.get_commit.await_args is not None
        req = fake_service.get_commit.await_args.args[0]
        assert (req.owner, req.repo, req.sha) == ("org", "repo", "abc123def456")

        message = _log_message(caplog)
        assert message.startswith("op=get_commit repo=org/repo sha=abc123de ms=")


class TestSearchCodeEndpoint:
    def test_success_returns_service_result(
        self,
        client: TestClient,
        fake_service: _FakeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        fake_service.search_code.return_value = SearchCodeResponse(
            query="filename:agent.py repo:org/repo",
            results=[_sample_code_result()],
        )
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            resp = client.post(
                "/search_code",
                json={"query": "filename:agent.py repo:org/repo"},
            )

        assert resp.status_code == 200
        assert resp.json()["results"][0]["path"] == "src/main.py"
        fake_service.search_code.assert_awaited_once()
        assert fake_service.search_code.await_args is not None
        req = fake_service.search_code.await_args.args[0]
        assert req.query == "filename:agent.py repo:org/repo"

        message = _log_message(caplog)
        assert message.startswith(
            "op=search_code q=filename:agent.py repo:org/repo n=1 ms="
        )

    def test_query_truncated_to_80_chars_in_log(
        self,
        client: TestClient,
        fake_service: _FakeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        long_query = "y" * 200
        fake_service.search_code.return_value = SearchCodeResponse(
            query=long_query, results=[]
        )
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            resp = client.post("/search_code", json={"query": long_query})

        assert resp.status_code == 200
        assert fake_service.search_code.await_args is not None
        req = fake_service.search_code.await_args.args[0]
        assert req.query == long_query

        message = _log_message(caplog)
        assert message.startswith(f"op=search_code q={'y' * 80} n=0 ms=")
