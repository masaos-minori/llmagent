"""tests/mcp_servers/mdq/test_mdq_disabled_tools.py

Disabled-tool and stale-discovery tests for mdq-mcp (REQ-001, AC-1).

Written in Phase 1 before the production change, so the assertions describe the
boundary REQ-001 requires and fail against current source:

- `call_tool()` has no availability check, so a tool discovery reports as disabled
  still executes through both HTTP and programmatic dispatch.
- `grep_docs` is gated only inside `MdqService.grep_docs()`, so the refusal carries
  the exception-class name rather than the stable code.

Each assertion names the disagreement it pins. They pass after seq 01 lands.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path
from tempfile import mkstemp
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

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
def boundary(
    monkeypatch: pytest.MonkeyPatch, service: MdqService
) -> tuple[TestClient, Callable[[], list[dict[str, Any]]]]:
    """The MDQ app with the service singleton replaced and its records captured.

    The logger is replaced so the real emission path is exercised rather than stubbed.
    Non-record info lines are skipped, so the count is the count of audit records.
    """
    fake = MagicMock()
    monkeypatch.setattr(mdq_server, "logger", fake)
    monkeypatch.setattr(mdq_server, "_service", service)

    def records() -> list[dict[str, Any]]:
        parsed: list[dict[str, Any]] = []
        for call in fake.info.call_args_list:
            try:
                parsed.append(json.loads(call.args[0]))
            except (json.JSONDecodeError, IndexError):
                continue
        return parsed

    with TestClient(mdq_server.app, headers=MCP_TEST_AUTH_HEADERS) as client:
        yield client, records


def _discovery_entry(client: TestClient, tool_name: str) -> dict[str, Any]:
    """Read one tool entry at the discovery boundary, disabled entries included."""
    response = client.get("/v1/tools?include_disabled=true")
    response.raise_for_status()
    for tool in response.json()["tools"]:
        if tool["name"] == tool_name:
            return dict(tool)
    raise KeyError(f"tool {tool_name!r} is not published at the discovery boundary")


class TestDisabledToolRefusal:
    """AC-1: a tool reported as disabled cannot be executed through either path."""

    def test_a_disabled_tool_is_refused_through_http(
        self,
        boundary: tuple[TestClient, Callable[[], list[dict[str, Any]]]],
        service: MdqService,
    ) -> None:
        client, records = boundary
        service._allowed_dirs = []

        entry = _discovery_entry(client, "search_docs")
        assert entry["enabled"] is False

        handler = AsyncMock(return_value="handler ran")
        with patch.dict(mdq_server._DISPATCH_TABLE, {"search_docs": handler}):
            response = client.post(
                "/v1/call_tool", json={"name": "search_docs", "args": {}}
            )

        assert handler.await_count == 0, "the handler ran for a tool reported disabled"
        assert response.status_code == 200
        body = response.json()
        assert body["is_error"] is True
        assert body["result"] == f"Tool disabled: {entry['disabled_reason']}"

        emitted = records()
        assert len(emitted) == 1, "the refusal path must emit exactly one audit record"
        assert emitted[0]["outcome"] == "rejected"
        assert emitted[0]["error_type"] == "tool_disabled", (
            "the record names the refusal by code, not by an exception class name"
        )

    async def test_a_disabled_tool_is_refused_through_programmatic_dispatch(
        self, monkeypatch: pytest.MonkeyPatch, service: MdqService
    ) -> None:
        # The gate evaluates the module singleton, so the fixture service must be the
        # instance the gate reads for this assertion to describe the boundary.
        monkeypatch.setattr(mdq_server, "_service", service)
        service._allowed_dirs = []
        handler = AsyncMock(return_value="handler ran")
        with patch.dict(mdq_server._DISPATCH_TABLE, {"search_docs": handler}):
            result = await mdq_server._dispatch_mdq_tool("search_docs", {})

        assert handler.await_count == 0, (
            "programmatic dispatch ran the handler for a disabled tool, so the gate is "
            "not on the entry both paths reach"
        )
        assert result.is_error is True
        assert result.output.startswith("Tool disabled:")

    async def test_grep_docs_configured_off_is_refused_on_both_paths(
        self,
        boundary: tuple[TestClient, Callable[[], list[dict[str, Any]]]],
        service: MdqService,
    ) -> None:
        client, records = boundary
        service.enable_grep = False

        entry = _discovery_entry(client, "grep_docs")
        assert entry["enabled"] is False, (
            "grep_docs is gated only inside the service, so discovery does not report it disabled"
        )

        handler = AsyncMock(return_value="handler ran")
        with patch.dict(mdq_server._DISPATCH_TABLE, {"grep_docs": handler}):
            response = client.post(
                "/v1/call_tool", json={"name": "grep_docs", "args": {"pattern": "x"}}
            )
        assert handler.await_count == 0
        assert response.json()["is_error"] is True

        emitted = records()
        assert len(emitted) == 1
        assert emitted[0]["outcome"] == "rejected"
        assert emitted[0]["error_type"] == "tool_disabled", (
            "the refusal carries the exception-class name today; the stable code is required"
        )

        programmatic_handler = AsyncMock(return_value="handler ran")
        with patch.dict(
            mdq_server._DISPATCH_TABLE, {"grep_docs": programmatic_handler}
        ):
            result = await mdq_server._dispatch_mdq_tool("grep_docs", {"pattern": "x"})
        assert programmatic_handler.await_count == 0
        assert result.is_error is True


class TestStaleDiscovery:
    """The stale-discovery case: discovery, a configuration change, then dispatch."""

    def test_dispatch_refuses_after_the_configuration_changes(
        self,
        boundary: tuple[TestClient, Callable[[], list[dict[str, Any]]]],
        service: MdqService,
    ) -> None:
        client, records = boundary

        entry = _discovery_entry(client, "search_docs")
        assert entry["enabled"] is True

        service._allowed_dirs = []
        handler = AsyncMock(return_value="handler ran")
        with patch.dict(mdq_server._DISPATCH_TABLE, {"search_docs": handler}):
            response = client.post(
                "/v1/call_tool", json={"name": "search_docs", "args": {}}
            )

        assert handler.await_count == 0, (
            "dispatch used the availability reported at discovery time instead of "
            "re-evaluating the configuration at call time"
        )
        assert response.json()["is_error"] is True

        emitted = records()
        assert len(emitted) == 1
        assert emitted[0]["outcome"] == "rejected"
        assert emitted[0]["error_type"] == "tool_disabled"
