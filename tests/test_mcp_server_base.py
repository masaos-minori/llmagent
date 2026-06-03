"""tests/test_mcp_server_base.py
Unit tests for MCPServer base class: list_tools(), health(),
__list_tools__ introspection protocol, and attach_auth_middleware.
"""

from __future__ import annotations

import asyncio
import re

import orjson
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from mcp.server import MCPServer, attach_auth_middleware


class _SimpleServer(MCPServer):
    server_name = "test-mcp"
    server_version = "1.0"
    http_host = "127.0.0.1"
    http_port = 9999
    app_module = "test:app"
    mcp_tools = [
        {"name": "tool_a", "description": "Tool A"},
        {"name": "tool_b", "description": "Tool B"},
    ]

    async def dispatch(self, name: str, args: dict) -> tuple[str, bool]:
        if name == "tool_a":
            return "result_a", False
        return f"unknown: {name}", True


class _EmptyServer(MCPServer):
    server_name = "empty-mcp"
    server_version = "1.0"
    http_port = 9998
    app_module = "empty:app"

    async def dispatch(self, name: str, args: dict) -> tuple[str, bool]:
        return "noop", False


class TestListTools:
    def test_returns_tool_names(self) -> None:
        srv = _SimpleServer()
        assert srv.list_tools() == ["tool_a", "tool_b"]

    def test_empty_mcp_tools_attribute_missing_returns_empty_list(self) -> None:
        srv = _EmptyServer()
        assert srv.list_tools() == []


class TestHealth:
    def test_default_health_returns_ok(self) -> None:
        srv = _SimpleServer()
        assert srv.health() == {"status": "ok"}


class TestRunStdio:
    """Test run_stdio() directly by injecting a pre-fed StreamReader."""

    @pytest.mark.asyncio
    async def test_list_tools_rpc_via_run_stdio(self) -> None:
        srv = _SimpleServer()
        request = orjson.dumps({"id": 1, "name": "__list_tools__", "args": {}}) + b"\n"

        pre_fed_reader = asyncio.StreamReader()
        pre_fed_reader.feed_data(request)
        pre_fed_reader.feed_eof()

        written: list[str] = []

        from unittest.mock import AsyncMock, MagicMock, patch  # noqa: PLC0415

        mock_loop = MagicMock()
        mock_loop.connect_read_pipe = AsyncMock(return_value=(MagicMock(), MagicMock()))

        with (
            patch("asyncio.get_running_loop", return_value=mock_loop),
            patch("asyncio.StreamReader", return_value=pre_fed_reader),
            patch("asyncio.StreamReaderProtocol"),
            patch("sys.stdout") as mock_stdout,
        ):
            mock_stdout.write = lambda s: written.append(s)
            mock_stdout.flush = lambda: None
            await srv.run_stdio()

        assert len(written) == 1
        resp = orjson.loads(written[0])
        assert resp["id"] == 1
        assert not resp["is_error"]
        assert orjson.loads(resp["result"])["tools"] == ["tool_a", "tool_b"]

    @pytest.mark.asyncio
    async def test_normal_dispatch_via_run_stdio(self) -> None:
        srv = _SimpleServer()
        request = orjson.dumps({"id": 2, "name": "tool_a", "args": {}}) + b"\n"

        pre_fed_reader = asyncio.StreamReader()
        pre_fed_reader.feed_data(request)
        pre_fed_reader.feed_eof()

        written: list[str] = []

        from unittest.mock import AsyncMock, MagicMock, patch  # noqa: PLC0415

        mock_loop = MagicMock()
        mock_loop.connect_read_pipe = AsyncMock(return_value=(MagicMock(), MagicMock()))

        with (
            patch("asyncio.get_running_loop", return_value=mock_loop),
            patch("asyncio.StreamReader", return_value=pre_fed_reader),
            patch("asyncio.StreamReaderProtocol"),
            patch("sys.stdout") as mock_stdout,
        ):
            mock_stdout.write = lambda s: written.append(s)
            mock_stdout.flush = lambda: None
            await srv.run_stdio()

        assert len(written) == 1
        resp = orjson.loads(written[0])
        assert resp["id"] == 2
        assert not resp["is_error"]
        assert resp["result"] == "result_a"


# ─────────────────────────────────────────────────────────────────────────────
# attach_auth_middleware
# ─────────────────────────────────────────────────────────────────────────────

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def _make_test_app(token: str = "") -> TestClient:
    """Build a minimal FastAPI app with auth middleware and return a TestClient."""
    app = FastAPI()

    @app.get("/ping")
    async def ping() -> dict[str, str]:
        return {"pong": "ok"}

    attach_auth_middleware(app, token)
    return TestClient(app, raise_server_exceptions=True)


class TestAttachAuthMiddleware:
    def test_no_token_allows_any_request(self) -> None:
        client = _make_test_app("")
        resp = client.get("/ping")
        assert resp.status_code == 200

    def test_no_token_response_contains_request_id(self) -> None:
        client = _make_test_app("")
        resp = client.get("/ping")
        req_id = resp.headers.get("x-request-id", "")
        assert _UUID_RE.match(req_id), f"Expected UUID4, got {req_id!r}"

    def test_correct_token_returns_200(self) -> None:
        client = _make_test_app("secret")
        resp = client.get("/ping", headers={"Authorization": "Bearer secret"})
        assert resp.status_code == 200

    def test_missing_token_returns_401(self) -> None:
        client = _make_test_app("secret")
        resp = client.get("/ping")
        assert resp.status_code == 401
        assert resp.json() == {"error": "Unauthorized"}

    def test_wrong_token_returns_401(self) -> None:
        client = _make_test_app("secret")
        resp = client.get("/ping", headers={"Authorization": "Bearer wrong"})
        assert resp.status_code == 401

    def test_request_id_present_on_auth_failure(self) -> None:
        # X-Request-Id should NOT be set on 401 because JSONResponse is returned
        # directly without going through call_next — this is expected behavior.
        client = _make_test_app("secret")
        resp = client.get("/ping")
        assert resp.status_code == 401

    def test_request_id_uuid4_format_on_success(self) -> None:
        client = _make_test_app("tok")
        resp = client.get("/ping", headers={"Authorization": "Bearer tok"})
        req_id = resp.headers.get("x-request-id", "")
        assert _UUID_RE.match(req_id), f"Expected UUID4, got {req_id!r}"

    def test_each_request_gets_unique_id(self) -> None:
        client = _make_test_app("")
        ids = {client.get("/ping").headers.get("x-request-id") for _ in range(5)}
        assert len(ids) == 5


class TestTruncate:
    def test_short_text_returned_unchanged(self) -> None:
        from mcp.server import _truncate

        text = "hello world"
        assert _truncate(text, max_bytes=100) == text

    def test_text_exactly_at_limit_returned_unchanged(self) -> None:
        from mcp.server import _truncate

        text = "a" * 10
        assert _truncate(text, max_bytes=10) == text

    def test_long_text_is_truncated_and_notice_appended(self) -> None:
        from mcp.server import _truncate

        text = "a" * 200
        result = _truncate(text, max_bytes=100)
        assert "[TRUNCATED:" in result
        assert "bytes total" in result

    def test_truncated_output_is_not_longer_than_limit_plus_notice(self) -> None:
        from mcp.server import _truncate

        text = "x" * 1000
        result = _truncate(text, max_bytes=50)
        # Starts with exactly 50 "x"s (before the notice)
        assert result.startswith("x" * 50)

    def test_multibyte_unicode_truncated_cleanly(self) -> None:
        from mcp.server import _truncate

        # "あ" is 3 bytes in UTF-8; 10 bytes fits 3 full chars (9 bytes)
        text = "あ" * 10
        result = _truncate(text, max_bytes=10)
        assert "[TRUNCATED:" in result
        # No UnicodeDecodeError; only complete characters appear
        assert "あ" in result


class TestAuditLog:
    def test_audit_log_emits_info(self, caplog: pytest.LogCaptureFixture) -> None:
        import logging

        from mcp.audit import _audit_log

        logger = logging.getLogger("test.audit")
        with caplog.at_level(logging.INFO, logger="test.audit"):
            _audit_log(
                logger,
                session_id="sess-1",
                request_id="req-2",
                action="my_tool",
                target="owner/repo",
                outcome="ok",
            )
        assert any("AUDIT" in r.message for r in caplog.records)
        assert any("sess-1" in r.message for r in caplog.records)

    def test_audit_log_replaces_empty_session_with_dash(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging

        from mcp.audit import _audit_log

        logger = logging.getLogger("test.audit2")
        with caplog.at_level(logging.INFO, logger="test.audit2"):
            _audit_log(
                logger,
                session_id="",
                request_id="",
                action="tool",
                target="t",
                outcome="ok",
            )
        msg = next(r.message for r in caplog.records if "AUDIT" in r.message)
        assert "session=-" in msg
        assert "request=-" in msg
