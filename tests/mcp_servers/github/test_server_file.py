"""tests/mcp_servers/github/test_server_file.py

Characterization tests for scripts/mcp_servers/github/github_server_file.py's FastAPI route
wiring:
  - POST /get_file_contents
  - POST /create_or_update_file
  - POST /push_files
  - POST /delete_repo_file

Baseline coverage (before this file): 47% -- lines 35-43, 52-61, 70-79, 88-96 (the body of
every route handler) were unexercised. The existing suite exercises `GitHubService`'s methods
directly (`test_service_file.py`) or via the `fmt_*`/dispatch wrappers (`test_service_dispatch.py`,
`test_github_mcp_service.py`), but nothing sends an HTTP request through these routes, so the
timing (`time.perf_counter()`) and `_info(...)` structured-logging calls that live only in
server_file.py never ran.

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
    CreateOrUpdateFileResponse,
    DeleteRepoFileResponse,
    GetFileContentsResponse,
    PushFilesResponse,
)


class _FakeService:
    """Minimal stand-in for GitHubService, exposing only what server_file.py touches."""

    def __init__(self) -> None:
        self.get_file_contents = AsyncMock()
        self.create_or_update_file = AsyncMock()
        self.push_files = AsyncMock()
        self.delete_repo_file = AsyncMock()


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


class TestGetFileContentsEndpoint:
    def test_success_returns_service_result(
        self,
        client: TestClient,
        fake_service: _FakeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        fake_service.get_file_contents.return_value = GetFileContentsResponse(
            path="a.txt",
            content="aGVsbG8=",
            sha="deadbeef",
            size=5,
            encoding="base64",
        )
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            resp = client.post(
                "/get_file_contents",
                json={"owner": "org", "repo": "repo", "path": "a.txt"},
            )

        assert resp.status_code == 200
        assert resp.json() == {
            "path": "a.txt",
            "content": "aGVsbG8=",
            "sha": "deadbeef",
            "size": 5,
            "encoding": "base64",
        }
        fake_service.get_file_contents.assert_awaited_once()
        assert fake_service.get_file_contents.await_args is not None
        req = fake_service.get_file_contents.await_args.args[0]
        assert (req.owner, req.repo, req.path) == ("org", "repo", "a.txt")

        message = _log_message(caplog)
        assert message.startswith("op=get_file_contents repo=org/repo path=a.txt ms=")
        ms_value = message.rsplit("ms=", 1)[1]
        assert float(ms_value) >= 0


class TestCreateOrUpdateFileEndpoint:
    def test_success_returns_service_result(
        self,
        client: TestClient,
        fake_service: _FakeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        fake_service.create_or_update_file.return_value = CreateOrUpdateFileResponse(
            path="a.txt",
            commit_sha="abc123",
            operation="created",
        )
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            resp = client.post(
                "/create_or_update_file",
                json={
                    "owner": "org",
                    "repo": "repo",
                    "path": "a.txt",
                    "content": "hello",
                    "message": "add file",
                },
            )

        assert resp.status_code == 200
        assert resp.json() == {
            "path": "a.txt",
            "commit_sha": "abc123",
            "operation": "created",
        }
        fake_service.create_or_update_file.assert_awaited_once()
        assert fake_service.create_or_update_file.await_args is not None
        req = fake_service.create_or_update_file.await_args.args[0]
        assert (req.owner, req.repo, req.path, req.message) == (
            "org",
            "repo",
            "a.txt",
            "add file",
        )

        message = _log_message(caplog)
        assert message.startswith(
            "op=create_or_update_file repo=org/repo path=a.txt operation=created ms="
        )


class TestPushFilesEndpoint:
    def test_success_returns_service_result(
        self,
        client: TestClient,
        fake_service: _FakeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        fake_service.push_files.return_value = PushFilesResponse(
            branch="main",
            commit_sha="abc123",
            files_pushed=2,
        )
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            resp = client.post(
                "/push_files",
                json={
                    "owner": "org",
                    "repo": "repo",
                    "branch": "main",
                    "files": [
                        {"path": "a.txt", "content": "hello"},
                        {"path": "b.txt", "content": "world"},
                    ],
                    "message": "push two files",
                },
            )

        assert resp.status_code == 200
        assert resp.json() == {
            "branch": "main",
            "commit_sha": "abc123",
            "files_pushed": 2,
        }
        fake_service.push_files.assert_awaited_once()
        assert fake_service.push_files.await_args is not None
        req = fake_service.push_files.await_args.args[0]
        assert (req.owner, req.repo, req.branch, len(req.files)) == (
            "org",
            "repo",
            "main",
            2,
        )

        message = _log_message(caplog)
        assert message.startswith("op=push_files repo=org/repo branch=main n=2 ms=")


class TestDeleteRepoFileEndpoint:
    def test_success_returns_service_result(
        self,
        client: TestClient,
        fake_service: _FakeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        fake_service.delete_repo_file.return_value = DeleteRepoFileResponse(
            path="a.txt",
            commit_sha="abc123",
        )
        with caplog.at_level(logging.INFO, logger=github_server.logger.name):
            resp = client.post(
                "/delete_repo_file",
                json={
                    "owner": "org",
                    "repo": "repo",
                    "path": "a.txt",
                    "message": "remove file",
                    "sha": "deadbeef",
                },
            )

        assert resp.status_code == 200
        assert resp.json() == {"path": "a.txt", "commit_sha": "abc123"}
        fake_service.delete_repo_file.assert_awaited_once()
        assert fake_service.delete_repo_file.await_args is not None
        req = fake_service.delete_repo_file.await_args.args[0]
        assert (req.owner, req.repo, req.path, req.sha) == (
            "org",
            "repo",
            "a.txt",
            "deadbeef",
        )

        message = _log_message(caplog)
        assert message.startswith("op=delete_repo_file repo=org/repo path=a.txt ms=")
