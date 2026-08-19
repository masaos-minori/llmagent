"""tests/mcp_servers/github/test_server_pull_requests.py

Characterization tests for scripts/mcp_servers/github/github_server_pull_requests.py's FastAPI
route wiring:
  - POST /list_pull_requests
  - POST /get_pull_request
  - POST /create_pull_request
  - POST /search_pull_requests
  - POST /update_pull_request
  - POST /merge_pull_request

Baseline coverage (before this file): 43% -- lines 39-48, 57-65, 74-82, 91-99, 108-116,
125-134 (the body of every route handler) were unexercised. The existing suite exercises
`GitHubService`'s pull-request methods directly (`test_service_pull_requests.py`) or via the
`fmt_*`/dispatch wrappers (`test_service_dispatch.py`, `test_github_mcp_service.py`), but
nothing sends an HTTP request through these routes, so the timing (`time.perf_counter()`) and
`_info(...)` structured-logging calls that live only in server_pull_requests.py never ran.

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
    CreatePullRequestResponse,
    GetPullRequestResponse,
    IssueInfo,
    ListPullRequestsResponse,
    MergePullRequestResponse,
    PullRequestInfo,
    SearchPullRequestsResponse,
    UpdatePullRequestResponse,
)


class _FakeService:
    """Minimal stand-in for GitHubService, exposing only what server_pull_requests.py touches."""

    def __init__(self) -> None:
        self.list_pull_requests = AsyncMock()
        self.get_pull_request = AsyncMock()
        self.create_pull_request = AsyncMock()
        self.search_pull_requests = AsyncMock()
        self.update_pull_request = AsyncMock()
        self.merge_pull_request = AsyncMock()


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


def _sample_pr(number: int = 42) -> PullRequestInfo:
    return PullRequestInfo(
        number=number,
        title="Fix the thing",
        state="open",
        url=f"https://github.com/org/repo/pull/{number}",
        body="details",
        head_ref="feature-branch",
        base_ref="main",
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        draft=False,
    )


def _sample_issue(number: int = 42) -> IssueInfo:
    return IssueInfo(
        number=number,
        title="Something is broken",
        state="open",
        url=f"https://github.com/org/repo/issues/{number}",
        body="details",
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        labels=["bug"],
        assignees=["octocat"],
    )


class TestListPullRequestsEndpoint:
    def test_success_returns_service_result(
        self,
        client: TestClient,
        fake_service: _FakeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        fake_service.list_pull_requests.return_value = ListPullRequestsResponse(
            pull_requests=[_sample_pr()]
        )
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            resp = client.post(
                "/list_pull_requests",
                json={"owner": "org", "repo": "repo", "state": "open"},
            )

        assert resp.status_code == 200
        assert resp.json()["pull_requests"][0]["number"] == 42
        fake_service.list_pull_requests.assert_awaited_once()
        assert fake_service.list_pull_requests.await_args is not None
        req = fake_service.list_pull_requests.await_args.args[0]
        assert (req.owner, req.repo, req.state) == ("org", "repo", "open")

        message = _log_message(caplog)
        assert message.startswith(
            "op=list_pull_requests repo=org/repo state=open n=1 ms="
        )
        ms_value = message.rsplit("ms=", 1)[1]
        assert float(ms_value) >= 0


class TestGetPullRequestEndpoint:
    def test_success_returns_service_result(
        self,
        client: TestClient,
        fake_service: _FakeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        fake_service.get_pull_request.return_value = GetPullRequestResponse(
            pull_request=_sample_pr(42)
        )
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            resp = client.post(
                "/get_pull_request",
                json={"owner": "org", "repo": "repo", "pr_number": 42},
            )

        assert resp.status_code == 200
        assert resp.json()["pull_request"]["number"] == 42
        fake_service.get_pull_request.assert_awaited_once()
        assert fake_service.get_pull_request.await_args is not None
        req = fake_service.get_pull_request.await_args.args[0]
        assert (req.owner, req.repo, req.pr_number) == ("org", "repo", 42)

        message = _log_message(caplog)
        assert message.startswith("op=get_pull_request repo=org/repo pr=42 ms=")


class TestCreatePullRequestEndpoint:
    def test_success_returns_service_result(
        self,
        client: TestClient,
        fake_service: _FakeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        fake_service.create_pull_request.return_value = CreatePullRequestResponse(
            pull_request=_sample_pr(7)
        )
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            resp = client.post(
                "/create_pull_request",
                json={
                    "owner": "org",
                    "repo": "repo",
                    "title": "New feature",
                    "head": "feature-branch",
                    "base": "main",
                },
            )

        assert resp.status_code == 200
        assert resp.json()["pull_request"]["number"] == 7
        fake_service.create_pull_request.assert_awaited_once()
        assert fake_service.create_pull_request.await_args is not None
        req = fake_service.create_pull_request.await_args.args[0]
        assert (req.owner, req.repo, req.title, req.head, req.base) == (
            "org",
            "repo",
            "New feature",
            "feature-branch",
            "main",
        )

        message = _log_message(caplog)
        assert message.startswith("op=create_pull_request repo=org/repo pr=7 ms=")


class TestSearchPullRequestsEndpoint:
    def test_success_returns_service_result(
        self,
        client: TestClient,
        fake_service: _FakeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        fake_service.search_pull_requests.return_value = SearchPullRequestsResponse(
            query="repo:org/repo is:pr is:open",
            results=[_sample_issue()],
        )
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            resp = client.post(
                "/search_pull_requests",
                json={"query": "repo:org/repo is:pr is:open"},
            )

        assert resp.status_code == 200
        assert resp.json()["results"][0]["number"] == 42
        fake_service.search_pull_requests.assert_awaited_once()
        assert fake_service.search_pull_requests.await_args is not None
        req = fake_service.search_pull_requests.await_args.args[0]
        assert req.query == "repo:org/repo is:pr is:open"

        message = _log_message(caplog)
        assert message.startswith(
            "op=search_pull_requests q=repo:org/repo is:pr is:open n=1 ms="
        )

    def test_query_truncated_to_80_chars_in_log(
        self,
        client: TestClient,
        fake_service: _FakeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        long_query = "x" * 200
        fake_service.search_pull_requests.return_value = SearchPullRequestsResponse(
            query=long_query, results=[]
        )
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            resp = client.post("/search_pull_requests", json={"query": long_query})

        assert resp.status_code == 200
        assert fake_service.search_pull_requests.await_args is not None
        req = fake_service.search_pull_requests.await_args.args[0]
        assert req.query == long_query

        message = _log_message(caplog)
        assert message.startswith(f"op=search_pull_requests q={'x' * 80} n=0 ms=")


class TestUpdatePullRequestEndpoint:
    def test_success_returns_service_result(
        self,
        client: TestClient,
        fake_service: _FakeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        fake_service.update_pull_request.return_value = UpdatePullRequestResponse(
            pull_request=_sample_pr(42)
        )
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            resp = client.post(
                "/update_pull_request",
                json={
                    "owner": "org",
                    "repo": "repo",
                    "pr_number": 42,
                    "title": "New title",
                },
            )

        assert resp.status_code == 200
        assert resp.json()["pull_request"]["number"] == 42
        fake_service.update_pull_request.assert_awaited_once()
        assert fake_service.update_pull_request.await_args is not None
        req = fake_service.update_pull_request.await_args.args[0]
        assert (req.owner, req.repo, req.pr_number, req.title) == (
            "org",
            "repo",
            42,
            "New title",
        )

        message = _log_message(caplog)
        assert message.startswith("op=update_pull_request repo=org/repo pr=42 ms=")


class TestMergePullRequestEndpoint:
    def test_success_returns_service_result(
        self,
        client: TestClient,
        fake_service: _FakeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        fake_service.merge_pull_request.return_value = MergePullRequestResponse(
            pr_number=42,
            merged=True,
            sha="abc123",
            message="merged successfully",
        )
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            resp = client.post(
                "/merge_pull_request",
                json={"owner": "org", "repo": "repo", "pr_number": 42},
            )

        assert resp.status_code == 200
        assert resp.json() == {
            "pr_number": 42,
            "merged": True,
            "sha": "abc123",
            "message": "merged successfully",
        }
        fake_service.merge_pull_request.assert_awaited_once()
        assert fake_service.merge_pull_request.await_args is not None
        req = fake_service.merge_pull_request.await_args.args[0]
        assert (req.owner, req.repo, req.pr_number) == ("org", "repo", 42)

        message = _log_message(caplog)
        assert message.startswith(
            "op=merge_pull_request repo=org/repo pr=42 merged=True ms="
        )

    def test_not_merged_reflected_in_log(
        self,
        client: TestClient,
        fake_service: _FakeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        fake_service.merge_pull_request.return_value = MergePullRequestResponse(
            pr_number=42,
            merged=False,
            sha="",
            message="conflict",
        )
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            resp = client.post(
                "/merge_pull_request",
                json={"owner": "org", "repo": "repo", "pr_number": 42},
            )

        assert resp.status_code == 200
        assert resp.json()["merged"] is False

        message = _log_message(caplog)
        assert message.startswith(
            "op=merge_pull_request repo=org/repo pr=42 merged=False ms="
        )
