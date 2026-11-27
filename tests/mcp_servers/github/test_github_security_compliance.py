"""tests/mcp_servers/github/test_github_security_compliance.py

Runtime-enforcement contract tests at `POST /v1/call_tool` (AC-1, AC-2, AC-4, REQ-002): the
authorization, validation, and dedup decisions are observed through the real HTTP boundary with only
the GitHub API client mocked.

Contract tests, not characterization tests: the service, the request-model validation, and the
durable dedup gate are the production ones, so a refused call is a refusal the boundary actually
made rather than a stubbed response. Consumes the shared `http_boundary` fixture (mcpai010 REQ-003),
which carries `isolated_dedup` through the dispatch seam. Marker: `security_contract` (REQ-004).

Validation failures are asserted as boundary error results, not as 400: `GitHubValidationError` is a
`ValueError` subclass and `dispatch_tool` converts `ValueError` into an error result before the
transport handler runs (`scripts/mcp_servers/dispatch.py:486-498`), so only the `RuntimeError`-based
domain errors reach `exception_handlers.py` and produce a status code.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime
from types import ModuleType, SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest
from mcp_servers.github import github_server
from mcp_servers.github.github_models_config import GitHubConfig
from mcp_servers.github.github_service_dispatch import GitHubService

from tests.mcp_servers._auth_headers import MCP_TEST_AUTH_HEADERS
from tests.mcp_servers.conftest import HttpBoundary

ALLOWED = "owner/allowed"


def _search_hit() -> SimpleNamespace:
    """One search result shaped like the PyGithub object the mapper reads."""
    return SimpleNamespace(
        full_name=ALLOWED,
        description="d",
        html_url="https://github.com/owner/allowed",
        stargazers_count=1,
        forks_count=2,
        language="Python",
        updated_at=datetime(2026, 11, 26, tzinfo=UTC),
    )


def _file_content(size: int, decoded: bytes) -> SimpleNamespace:
    """Content metadata shaped like the PyGithub object the read path reads.

    Plain objects, not `MagicMock`: the response models validate these fields, and a mock attribute
    fails validation instead of proving the guard ran.
    """
    return SimpleNamespace(size=size, decoded_content=decoded, path="a.txt", sha="sha1")


@pytest.fixture
def service(monkeypatch: pytest.MonkeyPatch) -> GitHubService:
    """The real service with only the API client mocked, patched onto the app.

    Nothing is bypassed below the client: the `fmt_*` handlers, the guards, and the dedup gate are
    the production ones. `_GITHUB_TOKEN` is patched because the disabled-tool gate runs before
    dispatch and refuses every tool when the token is empty, which is the test environment's state.
    """
    svc = GitHubService(
        gh=MagicMock(),
        cfg=GitHubConfig.from_dict(
            {
                "allowed_repos": [ALLOWED],
                "path_denylist": ["*.env"],
                "max_file_read_size_kb": 1,
            }
        ),
    )
    monkeypatch.setattr(github_server, "_service", svc)
    monkeypatch.setattr(github_server, "_GITHUB_TOKEN", "fake-token")
    return svc


def _call(
    boundary: HttpBoundary,
    name: str,
    args: dict[str, Any],
    key: str = "",
) -> Any:
    """POST one tool call through the boundary, with the idempotency key when one is required."""
    headers = dict(MCP_TEST_AUTH_HEADERS)
    if key:
        headers["x-idempotency-key"] = key
    return boundary.client.post(
        "/v1/call_tool", json={"name": name, "args": args}, headers=headers
    )


@pytest.mark.security_contract
class TestAuthorizationAtTheBoundary:
    def test_read_outside_allowlist_is_refused_and_calls_no_api(
        self,
        http_boundary: Callable[[ModuleType], HttpBoundary],
        service: GitHubService,
    ) -> None:
        boundary = http_boundary(github_server)
        resp = _call(
            boundary,
            "github_get_file_contents",
            {"owner": "other", "repo": "somewhere", "path": "a.txt"},
        )
        assert resp.status_code == 403
        assert "other/somewhere" in resp.json()["detail"]
        assert service._gh.get_repo.call_count == 0

    def test_search_query_is_scoped_to_the_allowlisted_repository(
        self,
        http_boundary: Callable[[ModuleType], HttpBoundary],
        service: GitHubService,
    ) -> None:
        gh = service._gh
        gh.search_repositories.return_value = [_search_hit()]
        boundary = http_boundary(github_server)
        resp = _call(
            boundary, "github_search_repositories", {"query": "topic:contract"}
        )
        assert resp.status_code == 200
        query = gh.search_repositories.call_args.kwargs["query"]
        assert f"repo:{ALLOWED}" in query

    def test_search_qualifier_outside_the_allowlist_is_refused(
        self,
        http_boundary: Callable[[ModuleType], HttpBoundary],
        service: GitHubService,
    ) -> None:
        boundary = http_boundary(github_server)
        resp = _call(
            boundary, "github_search_repositories", {"query": "repo:other/somewhere"}
        )
        assert resp.status_code == 403
        assert service._gh.search_repositories.call_count == 0

    def test_denied_path_is_refused_before_the_api_call(
        self,
        http_boundary: Callable[[ModuleType], HttpBoundary],
        service: GitHubService,
    ) -> None:
        boundary = http_boundary(github_server)
        resp = _call(
            boundary,
            "github_get_file_contents",
            {"owner": "owner", "repo": "allowed", "path": ".env"},
        )
        assert resp.status_code == 403
        assert service._gh.get_repo.call_count == 0


@pytest.mark.security_contract
class TestValidationAtTheBoundary:
    def test_extra_argument_is_refused_by_the_strict_model(
        self,
        http_boundary: Callable[[ModuleType], HttpBoundary],
        service: GitHubService,
    ) -> None:
        """The wire enforces the `additionalProperties: false` schema row 3 asserts is published."""
        boundary = http_boundary(github_server)
        resp = _call(
            boundary,
            "github_get_file_contents",
            {"owner": "owner", "repo": "allowed", "path": "a.txt", "unexpected": "x"},
        )
        body = resp.json()
        assert body["is_error"] is True
        assert "unexpected" in body["result"]
        assert service._gh.get_repo.call_count == 0

    def test_oversized_read_is_refused_before_decoding(
        self,
        http_boundary: Callable[[ModuleType], HttpBoundary],
        service: GitHubService,
    ) -> None:
        gh = service._gh
        gh.get_repo.return_value.get_contents.return_value = _file_content(4096, b"ok")
        boundary = http_boundary(github_server)
        resp = _call(
            boundary,
            "github_get_file_contents",
            {"owner": "owner", "repo": "allowed", "path": "a.txt"},
        )
        body = resp.json()
        assert body["is_error"] is True
        # The size error, not a decode error: the guard runs on the metadata size first.
        assert "max_file_read_size_kb" in body["result"]

    def test_non_utf8_content_is_refused(
        self,
        http_boundary: Callable[[ModuleType], HttpBoundary],
        service: GitHubService,
    ) -> None:
        gh = service._gh
        gh.get_repo.return_value.get_contents.return_value = _file_content(
            10, b"\xff\xfe\x00"
        )
        boundary = http_boundary(github_server)
        resp = _call(
            boundary,
            "github_get_file_contents",
            {"owner": "owner", "repo": "allowed", "path": "a.txt"},
        )
        body = resp.json()
        assert body["is_error"] is True
        assert "does not decode as UTF-8" in body["result"]


@pytest.mark.security_contract
class TestDedupAtTheBoundary:
    def _mock_branch(self, service: GitHubService) -> Any:
        """Configure the client so one executed write handler produces a valid response model."""
        repo = service._gh.get_repo.return_value
        repo.get_branch.return_value = SimpleNamespace(
            commit=SimpleNamespace(sha="abc1234567890def")
        )
        return repo

    def test_dedup_state_reports_fresh_acquisition_then_duplicate(
        self,
        http_boundary: Callable[[ModuleType], HttpBoundary],
        service: GitHubService,
        isolated_dedup: Any,
    ) -> None:
        repo = self._mock_branch(service)
        boundary = http_boundary(github_server)
        assert boundary.dedup_path == isolated_dedup, (
            "the boundary is not on the injected store"
        )
        args = {
            "owner": "owner",
            "repo": "allowed",
            "branch_name": "contract",
            "from_branch": "main",
        }

        first = _call(boundary, "github_create_branch", args, key="k1").json()
        assert first["is_error"] is False
        assert first["dedup_state"] == ""
        assert first["execution_mode"] == "applied"

        second = _call(boundary, "github_create_branch", args, key="k1").json()
        assert second["dedup_state"] in {"duplicate_hit", "in_progress"}
        assert second["execution_mode"] == "no_op"
        assert repo.get_branch.call_count == 1, (
            "the handler ran more than once for one key"
        )

    async def test_concurrent_same_key_writes_execute_the_handler_once(
        self,
        http_boundary: Callable[[ModuleType], HttpBoundary],
        service: GitHubService,
    ) -> None:
        """Two concurrent same-key calls, one event loop: one acquisition, one handler run.

        `TestClient` is synchronous, so the concurrent half uses `httpx.ASGITransport` on the same
        app, matching `tests/mcp_servers/test_mcp_dispatch_concurrency.py:113-121`.
        """
        repo = self._mock_branch(service)
        boundary = http_boundary(github_server)
        assert boundary.dedup_path.exists(), "the boundary is not on the injected store"
        args = {
            "owner": "owner",
            "repo": "allowed",
            "branch_name": "contract",
            "from_branch": "main",
        }

        async def post(client: httpx.AsyncClient) -> dict[str, Any]:
            resp = await client.post(
                "/v1/call_tool",
                json={"name": "github_create_branch", "args": args},
                headers={"x-idempotency-key": "k2"},
            )
            body: dict[str, Any] = resp.json()
            return body

        transport = httpx.ASGITransport(app=github_server.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test", headers=MCP_TEST_AUTH_HEADERS
        ) as client:
            results = await asyncio.gather(*(post(client) for _ in range(2)))

        executed = [r for r in results if r["dedup_state"] == "" and not r["is_error"]]
        assert len(executed) == 1
        for result in results:
            if result is executed[0]:
                continue
            assert result["dedup_state"] in {"in_progress", "duplicate_hit"}
        assert repo.get_branch.call_count == 1


@pytest.mark.security_contract
class TestAuthenticationAtTheBoundary:
    async def test_authenticated_call_succeeds_and_unauthenticated_call_is_401(
        self,
        http_boundary: Callable[[ModuleType], HttpBoundary],
        service: GitHubService,
    ) -> None:
        gh = service._gh
        gh.get_repo.return_value.get_contents.return_value = _file_content(10, b"ok")
        boundary = http_boundary(github_server)
        name = "github_get_file_contents"
        args = {"owner": "owner", "repo": "allowed", "path": "a.txt"}

        assert _call(boundary, name, args).status_code == 200

        # The fixture's client carries the headers and httpx merges per-request headers, so the
        # unauthenticated half is the same app through a header-less client.
        transport = httpx.ASGITransport(app=github_server.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            resp = await client.post("/v1/call_tool", json={"name": name, "args": args})
            assert resp.status_code == 401
