"""tests/mcp_servers/github/test_server_issues.py

Characterization tests for scripts/mcp_servers/github/server_issues.py's FastAPI route
wiring:
  - POST /list_issues
  - POST /get_issue
  - POST /create_issue
  - POST /search_issues
  - POST /add_issue_comment

Baseline coverage (before this file): 44% -- lines 37-46, 55-63, 72-80, 89-97, 106-114 (the
body of every route handler) were unexercised. The existing suite exercises `GitHubService`'s
issues methods directly (`test_service_issues.py`) or via the `fmt_*`/dispatch wrappers
(`test_service_dispatch.py`, `test_github_mcp_service.py`), but nothing sends an HTTP request
through these routes, so the timing (`time.perf_counter()`) and `_info(...)` structured-logging
calls that live only in server_issues.py never ran.

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
    AddIssueCommentResponse,
    CreateIssueResponse,
    GetIssueResponse,
    IssueInfo,
    ListIssuesResponse,
    SearchIssuesResponse,
)


class _FakeService:
    """Minimal stand-in for GitHubService, exposing only what server_issues.py touches."""

    def __init__(self) -> None:
        self.list_issues = AsyncMock()
        self.get_issue = AsyncMock()
        self.create_issue = AsyncMock()
        self.search_issues = AsyncMock()
        self.add_issue_comment = AsyncMock()


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


class TestListIssuesEndpoint:
    def test_success_returns_service_result(
        self,
        client: TestClient,
        fake_service: _FakeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        fake_service.list_issues.return_value = ListIssuesResponse(
            issues=[_sample_issue()]
        )
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            resp = client.post(
                "/list_issues",
                json={"owner": "org", "repo": "repo", "state": "open"},
            )

        assert resp.status_code == 200
        assert resp.json()["issues"][0]["number"] == 42
        fake_service.list_issues.assert_awaited_once()
        assert fake_service.list_issues.await_args is not None
        req = fake_service.list_issues.await_args.args[0]
        assert (req.owner, req.repo, req.state) == ("org", "repo", "open")

        message = _log_message(caplog)
        assert message.startswith("op=list_issues repo=org/repo state=open n=1 ms=")
        ms_value = message.rsplit("ms=", 1)[1]
        assert float(ms_value) >= 0


class TestGetIssueEndpoint:
    def test_success_returns_service_result(
        self,
        client: TestClient,
        fake_service: _FakeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        fake_service.get_issue.return_value = GetIssueResponse(issue=_sample_issue(42))
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            resp = client.post(
                "/get_issue",
                json={"owner": "org", "repo": "repo", "issue_number": 42},
            )

        assert resp.status_code == 200
        assert resp.json()["issue"]["number"] == 42
        fake_service.get_issue.assert_awaited_once()
        assert fake_service.get_issue.await_args is not None
        req = fake_service.get_issue.await_args.args[0]
        assert (req.owner, req.repo, req.issue_number) == ("org", "repo", 42)

        message = _log_message(caplog)
        assert message.startswith("op=get_issue repo=org/repo issue=42 ms=")


class TestCreateIssueEndpoint:
    def test_success_returns_service_result(
        self,
        client: TestClient,
        fake_service: _FakeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        fake_service.create_issue.return_value = CreateIssueResponse(
            issue=_sample_issue(7)
        )
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            resp = client.post(
                "/create_issue",
                json={"owner": "org", "repo": "repo", "title": "New bug"},
            )

        assert resp.status_code == 200
        assert resp.json()["issue"]["number"] == 7
        fake_service.create_issue.assert_awaited_once()
        assert fake_service.create_issue.await_args is not None
        req = fake_service.create_issue.await_args.args[0]
        assert (req.owner, req.repo, req.title) == ("org", "repo", "New bug")

        message = _log_message(caplog)
        assert message.startswith("op=create_issue repo=org/repo issue=7 ms=")


class TestSearchIssuesEndpoint:
    def test_success_returns_service_result(
        self,
        client: TestClient,
        fake_service: _FakeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        fake_service.search_issues.return_value = SearchIssuesResponse(
            query="repo:org/repo is:issue label:bug",
            results=[_sample_issue()],
        )
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            resp = client.post(
                "/search_issues",
                json={"query": "repo:org/repo is:issue label:bug"},
            )

        assert resp.status_code == 200
        assert resp.json()["results"][0]["number"] == 42
        fake_service.search_issues.assert_awaited_once()
        assert fake_service.search_issues.await_args is not None
        req = fake_service.search_issues.await_args.args[0]
        assert req.query == "repo:org/repo is:issue label:bug"

        message = _log_message(caplog)
        assert message.startswith(
            "op=search_issues q=repo:org/repo is:issue label:bug n=1 ms="
        )

    def test_query_truncated_to_80_chars_in_log(
        self,
        client: TestClient,
        fake_service: _FakeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        long_query = "x" * 200
        fake_service.search_issues.return_value = SearchIssuesResponse(
            query=long_query, results=[]
        )
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            resp = client.post("/search_issues", json={"query": long_query})

        assert resp.status_code == 200
        assert fake_service.search_issues.await_args is not None
        req = fake_service.search_issues.await_args.args[0]
        assert req.query == long_query

        message = _log_message(caplog)
        assert message.startswith(f"op=search_issues q={'x' * 80} n=0 ms=")


class TestAddIssueCommentEndpoint:
    def test_success_returns_service_result(
        self,
        client: TestClient,
        fake_service: _FakeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        fake_service.add_issue_comment.return_value = AddIssueCommentResponse(
            issue_number=42,
            comment_url="https://github.com/org/repo/issues/42#issuecomment-1",
        )
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            resp = client.post(
                "/add_issue_comment",
                json={
                    "owner": "org",
                    "repo": "repo",
                    "issue_number": 42,
                    "body": "thanks!",
                },
            )

        assert resp.status_code == 200
        assert resp.json() == {
            "issue_number": 42,
            "comment_url": "https://github.com/org/repo/issues/42#issuecomment-1",
        }
        fake_service.add_issue_comment.assert_awaited_once()
        assert fake_service.add_issue_comment.await_args is not None
        req = fake_service.add_issue_comment.await_args.args[0]
        assert (req.owner, req.repo, req.issue_number, req.body) == (
            "org",
            "repo",
            42,
            "thanks!",
        )

        message = _log_message(caplog)
        assert message.startswith("op=add_issue_comment repo=org/repo issue=42 ms=")
