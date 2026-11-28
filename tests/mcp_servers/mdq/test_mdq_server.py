"""tests/mcp_servers/mdq/test_mdq_server.py

Boundary tests for the single availability function shared by discovery and
dispatch (REQ-001, AC-1).

Written in Phase 1 before the production change, so the assertions describe the
boundary REQ-001 requires and fail against current source:

- `/v1/tools` calls `_mdq_tool_availability()` with `""` (`mdq_server.py` line 391),
  so every tool entry receives the same global answer instead of a per-tool one.
- `call_tool()` has no availability check, so a tool discovery reports as disabled
  still executes.

Each assertion names the disagreement it pins. They pass after seq 01 lands.
"""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import mkstemp
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from mcp_servers.mdq import mdq_server
from mcp_servers.mdq.mdq_service import MdqService

from tests.mcp_servers._auth_headers import MCP_TEST_AUTH_HEADERS
from tests.mcp_servers.mdq._startup import make_startup


@pytest.fixture
def service(tmp_path: Path) -> MdqService:
    """MdqService with a temp DB path and tmp_path in allowed_dirs."""
    fd, db = mkstemp(suffix=".db", dir=str(tmp_path))
    try:
        svc = MdqService(make_startup(db))
        svc._allowed_dirs = [str(tmp_path)]
        return svc
    finally:
        os.close(fd)


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, service: MdqService) -> TestClient:
    """The MDQ app with the service singleton replaced, so the boundary reads the test roots."""
    monkeypatch.setattr(mdq_server, "_service", service)
    with TestClient(mdq_server.app, headers=MCP_TEST_AUTH_HEADERS) as test_client:
        yield test_client


def _discovery_entry(client: TestClient, tool_name: str) -> dict[str, Any]:
    """Read one tool entry at the discovery boundary, disabled entries included."""
    response = client.get("/v1/tools?include_disabled=true")
    response.raise_for_status()
    for tool in response.json()["tools"]:
        if tool["name"] == tool_name:
            return dict(tool)
    raise KeyError(f"tool {tool_name!r} is not published at the discovery boundary")


async def _dispatch_programmatically(tool_name: str) -> tuple[Any, AsyncMock]:
    """Run one tool through the in-process dispatch entry with the handler recorded.

    The handler is replaced so a refusal is observable as "the handler never ran"
    rather than as the result of test work.
    """
    handler = AsyncMock(return_value="handler ran")
    with patch.dict(mdq_server._DISPATCH_TABLE, {tool_name: handler}):
        result = await mdq_server._dispatch_mdq_tool(tool_name, {})
    return result, handler


class TestSingleAvailabilityFunction:
    """REQ-001: discovery and dispatch must report the same availability for the same tool name."""

    async def test_discovery_and_dispatch_report_the_same_availability(
        self, client: TestClient, service: MdqService
    ) -> None:
        service._allowed_dirs = []
        entry = _discovery_entry(client, "search_docs")
        result, handler = await _dispatch_programmatically("search_docs")

        assert entry["enabled"] is False
        assert handler.await_count == 0, (
            "dispatch ran the handler for a tool discovery reported disabled, so the "
            "two paths do not share one availability decision"
        )
        assert result.is_error is True
        assert result.output == f"Tool disabled: {entry['disabled_reason']}"


class TestPerToolEvaluation:
    """REQ-001: availability is decided per tool name, so one tool can be disabled while another runs."""

    async def test_one_tool_can_be_disabled_while_another_is_enabled(
        self, client: TestClient, service: MdqService
    ) -> None:
        service.enable_grep = False

        search_entry = _discovery_entry(client, "search_docs")
        grep_entry = _discovery_entry(client, "grep_docs")
        assert search_entry["enabled"] is True
        assert grep_entry["enabled"] is False, (
            "the availability function returns one global answer for every tool name, "
            "so a per-tool rule cannot be expressed"
        )

        grep_result, grep_handler = await _dispatch_programmatically("grep_docs")
        assert grep_handler.await_count == 0, (
            "grep_docs ran while it was configured off"
        )
        assert grep_result.is_error is True

        search_result, search_handler = await _dispatch_programmatically("search_docs")
        assert search_handler.await_count == 1
        assert search_result.is_error is False


class TestReEvaluationAtCallTime:
    """REQ-001: dispatch re-evaluates at call time instead of trusting the discovery response."""

    async def test_the_allowlist_change_between_discovery_and_dispatch_is_honoured(
        self, client: TestClient, service: MdqService
    ) -> None:
        entry = _discovery_entry(client, "search_docs")
        assert entry["enabled"] is True

        service._allowed_dirs = []
        result, handler = await _dispatch_programmatically("search_docs")

        assert handler.await_count == 0, (
            "dispatch used the availability reported at discovery time instead of "
            "re-evaluating the allowlist at call time"
        )
        assert result.is_error is True
        assert result.output == "Tool disabled: allowed_dirs is empty"
