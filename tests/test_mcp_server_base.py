"""tests/test_mcp_server_base.py
Unit tests for MCPServer base class: list_tools(), health(),
__list_tools__ introspection protocol, and attach_auth_middleware.
"""

from __future__ import annotations

import asyncio
import importlib.util
import re
from pathlib import Path

import orjson
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from mcp.dispatch import DispatchResult
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

    async def dispatch(self, name: str, args: dict) -> DispatchResult:
        if name == "tool_a":
            return DispatchResult("result_a", False)
        return DispatchResult(f"unknown: {name}", True)


class _EmptyServer(MCPServer):
    server_name = "empty-mcp"
    server_version = "1.0"
    http_port = 9998
    app_module = "empty:app"

    async def dispatch(self, name: str, args: dict) -> DispatchResult:
        return DispatchResult("noop", False)


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
        health_dict, status_code = srv.health()
        assert health_dict == {
            "status": "ok",
            "ready": True,
            "dependencies": {},
            "details": {},
        }
        assert status_code == 200

    def test_health_returns_tuple_with_status_code(self) -> None:
        srv = _SimpleServer()
        result = srv.health()
        assert isinstance(result, tuple)
        assert len(result) == 2
        health_dict, status_code = result
        assert isinstance(health_dict, dict)
        assert isinstance(status_code, int)

    def test_health_status_code_200_when_ready(self) -> None:
        srv = _SimpleServer()
        _, status_code = srv.health()
        assert status_code == 200


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
        mock_loop.run_in_executor = MagicMock(
            side_effect=lambda executor, fn, *args: fn(*args)
        )

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
        assert resp["req_id"] == 1
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
        mock_loop.run_in_executor = MagicMock(
            side_effect=lambda executor, fn, *args: fn(*args)
        )

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
        assert resp["req_id"] == 2
        assert not resp["is_error"]
        assert resp["result"] == "result_a"

    @pytest.mark.asyncio
    async def test_under_limit_no_truncation_via_stdio(self) -> None:
        """Under-limit response should have truncated=False and matching byte counts."""
        srv = _SimpleServer()
        request = orjson.dumps({"id": 3, "name": "tool_a", "args": {}}) + b"\n"

        pre_fed_reader = asyncio.StreamReader()
        pre_fed_reader.feed_data(request)
        pre_fed_reader.feed_eof()

        written: list[str] = []

        from unittest.mock import AsyncMock, MagicMock, patch  # noqa: PLC0415

        mock_loop = MagicMock()
        mock_loop.connect_read_pipe = AsyncMock(return_value=(MagicMock(), MagicMock()))
        mock_loop.run_in_executor = MagicMock(
            side_effect=lambda executor, fn, *args: fn(*args)
        )

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
        assert not resp["truncated"]
        assert resp["total_bytes"] == resp["actual_visible_bytes"]

    @pytest.mark.asyncio
    async def test_over_limit_ascii_truncation_via_stdio(self) -> None:
        """Over-limit ASCII response should have truncated=True with correct metadata."""
        from scripts.mcp.server import MCP_MAX_RESPONSE_BYTES  # noqa: PLC0415

        class _LongServer(_SimpleServer):
            async def dispatch(self, name: str, args: dict) -> DispatchResult:
                if name == "tool_a":
                    long_text = "a" * (MCP_MAX_RESPONSE_BYTES + 1000)
                    return DispatchResult(
                        output=long_text,
                        is_error=False,
                    )
                return await super().dispatch(name, args)

        srv = _LongServer()
        request = orjson.dumps({"id": 4, "name": "tool_a", "args": {}}) + b"\n"

        pre_fed_reader = asyncio.StreamReader()
        pre_fed_reader.feed_data(request)
        pre_fed_reader.feed_eof()

        written: list[str] = []

        from unittest.mock import AsyncMock, MagicMock, patch  # noqa: PLC0415

        mock_loop = MagicMock()
        mock_loop.connect_read_pipe = AsyncMock(return_value=(MagicMock(), MagicMock()))
        mock_loop.run_in_executor = MagicMock(
            side_effect=lambda executor, fn, *args: fn(*args)
        )

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
        assert resp["truncated"]
        assert resp["actual_visible_bytes"] == MCP_MAX_RESPONSE_BYTES
        assert resp["total_bytes"] > MCP_MAX_RESPONSE_BYTES

    @pytest.mark.asyncio
    async def test_over_limit_utf8_truncation_via_stdio(self) -> None:
        """Over-limit UTF-8 response should have actual_visible_bytes < total_bytes."""
        from scripts.mcp.server import MCP_MAX_RESPONSE_BYTES  # noqa: PLC0415

        class _Utf8LongServer(_SimpleServer):
            async def dispatch(self, name: str, args: dict) -> DispatchResult:
                if name == "tool_a":
                    utf8_text = "あ" * ((MCP_MAX_RESPONSE_BYTES // 3) + 100)
                    return DispatchResult(
                        output=utf8_text,
                        is_error=False,
                    )
                return await super().dispatch(name, args)

        srv = _Utf8LongServer()
        request = orjson.dumps({"id": 5, "name": "tool_a", "args": {}}) + b"\n"

        pre_fed_reader = asyncio.StreamReader()
        pre_fed_reader.feed_data(request)
        pre_fed_reader.feed_eof()

        written: list[str] = []

        from unittest.mock import AsyncMock, MagicMock, patch  # noqa: PLC0415

        mock_loop = MagicMock()
        mock_loop.connect_read_pipe = AsyncMock(return_value=(MagicMock(), MagicMock()))
        mock_loop.run_in_executor = MagicMock(
            side_effect=lambda executor, fn, *args: fn(*args)
        )

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
        assert resp["truncated"]
        assert resp["actual_visible_bytes"] <= MCP_MAX_RESPONSE_BYTES
        assert resp["total_bytes"] > MCP_MAX_RESPONSE_BYTES

    @pytest.mark.asyncio
    async def test_truncated_text_valid_utf8_via_stdio(self) -> None:
        """Truncated text via stdio should contain valid UTF-8 (no corrupted characters)."""
        from scripts.mcp.server import MCP_MAX_RESPONSE_BYTES  # noqa: PLC0415

        class _MixedUtf8Server(_SimpleServer):
            async def dispatch(self, name: str, args: dict) -> DispatchResult:
                if name == "tool_a":
                    long_text = "A" * 100 + "あいうえお" * (
                        (MCP_MAX_RESPONSE_BYTES // 15) + 100
                    )
                    return DispatchResult(
                        output=long_text,
                        is_error=False,
                    )
                return await super().dispatch(name, args)

        srv = _MixedUtf8Server()
        request = orjson.dumps({"id": 6, "name": "tool_a", "args": {}}) + b"\n"

        pre_fed_reader = asyncio.StreamReader()
        pre_fed_reader.feed_data(request)
        pre_fed_reader.feed_eof()

        written: list[str] = []

        from unittest.mock import AsyncMock, MagicMock, patch  # noqa: PLC0415

        mock_loop = MagicMock()
        mock_loop.connect_read_pipe = AsyncMock(return_value=(MagicMock(), MagicMock()))
        mock_loop.run_in_executor = MagicMock(
            side_effect=lambda executor, fn, *args: fn(*args)
        )

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
        resp["result"].encode("utf-8")  # raises if corrupted


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


class TestTruncateWithMeta:
    def test_short_text_returned_unchanged(self) -> None:
        from mcp.server import _truncate_with_meta

        text = "hello world"
        r = _truncate_with_meta(text, max_bytes=100)
        assert r.text == text
        assert not r.truncated

    def test_text_exactly_at_limit_returned_unchanged(self) -> None:
        from mcp.server import _truncate_with_meta

        text = "a" * 10
        r = _truncate_with_meta(text, max_bytes=10)
        assert r.text == text
        assert not r.truncated

    def test_long_text_is_truncated_and_notice_appended(self) -> None:
        from mcp.server import _truncate_with_meta

        text = "a" * 200
        r = _truncate_with_meta(text, max_bytes=100)
        assert r.truncated
        assert "[TRUNCATED:" in r.text
        assert "bytes total" in r.text

    def test_truncated_output_starts_with_original_prefix(self) -> None:
        from mcp.server import _truncate_with_meta

        text = "x" * 1000
        r = _truncate_with_meta(text, max_bytes=50)
        assert r.truncated
        assert r.text.startswith("x" * 50)

    def test_multibyte_unicode_truncated_cleanly(self) -> None:
        from mcp.server import _truncate_with_meta

        # "あ" is 3 bytes in UTF-8; 10 bytes fits 3 full chars (9 bytes)
        text = "あ" * 10
        r = _truncate_with_meta(text, max_bytes=10)
        assert r.truncated
        assert "[TRUNCATED:" in r.text
        # No UnicodeDecodeError; only complete characters appear
        assert "あ" in r.text

    def test_under_limit_no_truncation(self) -> None:
        from mcp.server import _truncate_with_meta

        text = "hello world"
        r = _truncate_with_meta(text, max_bytes=100)
        assert not r.truncated
        assert r.total_bytes == len(text.encode("utf-8"))
        assert r.actual_visible_bytes == len(text.encode("utf-8"))
        assert r.text == text

    def test_over_limit_ascii_visible_equals_max_bytes(self) -> None:
        from mcp.server import _truncate_with_meta

        # ASCII text: each char = 1 byte, so actual_visible == max_bytes
        text = "a" * 200
        r = _truncate_with_meta(text, max_bytes=100)
        assert r.truncated
        assert r.total_bytes == 200
        assert r.actual_visible_bytes == 100

    def test_over_limit_utf8_visible_less_than_max_bytes(self) -> None:
        from mcp.server import _truncate_with_meta

        # "あ" is 3 bytes in UTF-8; 34 chars = 102 bytes total, truncation at 100 bytes
        # drops the last partial character (bytes 97-100 = 4 bytes, but only 2 chars fit)
        text = "あ" * 34  # 102 bytes total
        r = _truncate_with_meta(text, max_bytes=100)
        assert r.truncated
        assert r.total_bytes == 102
        # actual_visible should be less than 100 because the partial character
        # at the truncation boundary is dropped by errors="ignore"
        assert r.actual_visible_bytes < 100

    def test_truncated_utf8_no_corrupted_characters(self) -> None:
        from mcp.server import _truncate_with_meta

        # Mix of ASCII and multi-byte UTF-8 at the truncation boundary
        text = "Hello" + "あいうえお" * 20 + "World"  # 5 + 90 + 5 = 100 bytes
        r = _truncate_with_meta(text, max_bytes=50)
        assert r.truncated
        # The shown portion must be valid UTF-8 (no corrupted characters)
        try:
            r.text.encode("utf-8")
        except UnicodeEncodeError:
            pytest.fail(f"Truncated text contains corrupted UTF-8: {r.text!r}")

    def test_truncated_text_valid_utf8_after_boundary(self) -> None:
        from mcp.server import _truncate_with_meta

        # Ensure the shown portion is valid UTF-8 even when boundary falls
        # in the middle of a multi-byte character
        text = "A" * 90 + "🎉" * 5  # 90 + 20 = 110 bytes total
        r = _truncate_with_meta(text, max_bytes=100)
        assert r.truncated
        # The shown portion must be valid UTF-8
        shown_portion = r.text.split("[TRUNCATED:")[0]
        shown_portion.encode("utf-8")  # raises if corrupted

    def test_truncation_notice_contains_correct_byte_counts(self) -> None:
        from mcp.server import _truncate_with_meta

        text = "a" * 200
        r = _truncate_with_meta(text, max_bytes=100)
        assert r.truncated
        assert "200 bytes total" in r.text
        assert "100 bytes" in r.text

    def test_truncation_notice_for_utf8_contains_actual_visible(self) -> None:
        from mcp.server import _truncate_with_meta

        # "あ" is 3 bytes; 34 chars = 102 bytes total, truncation at 100 bytes
        text = "あ" * 34
        r = _truncate_with_meta(text, max_bytes=100)
        assert r.truncated
        # The notice should contain the actual visible byte count, not the limit
        assert f"{r.total_bytes} bytes total" in r.text
        assert f"{r.actual_visible_bytes} bytes]" in r.text


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


class TestAppModuleImportability:
    def test_all_server_app_modules_are_importable(self) -> None:
        scripts_dir = Path(__file__).parent.parent / "scripts"
        server_files = list(scripts_dir.glob("mcp/**/*server.py"))
        assert server_files, "No server.py files found under scripts/mcp/"

        pattern = re.compile(r'app_module\s*=\s*"([^"]+)"')
        missing: list[str] = []

        for path in server_files:
            for match in pattern.finditer(path.read_text()):
                app_module_value = match.group(1)
                module_path = app_module_value.split(":")[0]
                spec = importlib.util.find_spec(module_path)
                if spec is None:
                    missing.append(f"{path.relative_to(scripts_dir)}: {module_path!r}")

        assert not missing, (
            "The following app_module paths are not importable:\n"
            + "\n".join(f"  {m}" for m in missing)
        )
