"""tests/mcp_servers/mdq/test_mdq_exception_handlers.py

Characterization tests for the exception-handler and audit-detail paths of `call_tool()`.

The assertions follow the boundary decided for `scripts/mcp_servers/mdq/mdq_server.py`
(SEQ 01):

- Records are read from the audit sink the single emission boundary writes to, because the
  handlers no longer emit: only `call_tool()`'s `finally` writes one record per call.
- Domain failures are rendered from the closed code vocabulary (`mdq_error_codes.py`,
  seq 08), never from `type(exc).__name__` or the exception text, so the client response
  carries the code only.
- The tool-level classes are answered at HTTP 200 with `is_error=true` and the code as
  `result`; the remaining classes keep their handler's transport status.

Records-count tests live in `tests/mcp_servers/mdq/test_mdq_exception_audit.py` (seq 14);
this file asserts codes and detail content, so the two do not duplicate the same assertion.
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
from mcp_servers.mdq.indexer import index_paths
from mcp_servers.mdq.mdq_models import (
    IndexPathsRequest,
    MdqConsistencyError,
    MdqDatabaseError,
    MdqServiceError,
    MdqValidationError,
)
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
def audit_records(
    monkeypatch: pytest.MonkeyPatch, service: MdqService
) -> Callable[[], list[dict[str, Any]]]:
    """Capture the records the emission boundary writes, without stubbing the emission."""
    sink = MagicMock()
    monkeypatch.setattr(mdq_server, "logger", sink)
    monkeypatch.setattr(mdq_server, "_service", service)

    def records() -> list[dict[str, Any]]:
        # Non-record info lines are skipped so the record list is the records only.
        parsed: list[dict[str, Any]] = []
        for call in sink.info.call_args_list:
            try:
                parsed.append(json.loads(call.args[0]))
            except (json.JSONDecodeError, IndexError):
                continue
        return parsed

    return records


def _client() -> TestClient:
    return TestClient(mdq_server.app, headers=MCP_TEST_AUTH_HEADERS)


class TestMdqDatabaseErrorHandler:
    """MdqDatabaseError raised from dispatch -> HTTP 503 via exception_handler."""

    def test_returns_503_with_the_code(self) -> None:
        client = _client()
        with patch(
            "mcp_servers.mdq.mdq_server._dispatch_mdq_tool",
            new=AsyncMock(side_effect=MdqDatabaseError("db unavailable")),
        ):
            response = client.post(
                "/v1/call_tool",
                json={"name": "stats", "args": {}},
            )
        assert response.status_code == 503
        # The transport response carries the code, not the exception text.
        assert response.json() == {"detail": "database_unavailable"}

    def test_the_single_boundary_records_the_code(self, audit_records) -> None:
        with patch(
            "mcp_servers.mdq.mdq_server._dispatch_mdq_tool",
            new=AsyncMock(side_effect=MdqDatabaseError("db unavailable")),
        ):
            _client().post("/v1/call_tool", json={"name": "stats", "args": {}})

        emitted = audit_records()
        assert len(emitted) == 1, (
            "the handler must not emit; only call_tool()'s finally does"
        )
        record = emitted[0]
        assert record["error_type"] == "database_unavailable"
        assert record["server_key"] == "mdq"
        assert record["outcome"] == "error"


class TestMdqConsistencyErrorHandler:
    """MdqConsistencyError raised from dispatch -> HTTP 500 via exception_handler."""

    def test_returns_500_with_the_code(self, audit_records) -> None:
        client = _client()
        with patch(
            "mcp_servers.mdq.mdq_server._dispatch_mdq_tool",
            new=AsyncMock(side_effect=MdqConsistencyError("index corrupt")),
        ):
            response = client.post(
                "/v1/call_tool",
                json={"name": "search_docs", "args": {"query": "x"}},
            )
        assert response.status_code == 500
        assert response.json() == {"detail": "consistency_error"}
        assert len(audit_records()) == 1
        assert audit_records()[0]["error_type"] == "consistency_error"


class TestMdqServiceErrorHandler:
    """MdqServiceError raised from dispatch -> HTTP 500 via exception_handler."""

    def test_returns_500_with_the_code(self, audit_records) -> None:
        client = _client()
        with patch(
            "mcp_servers.mdq.mdq_server._dispatch_mdq_tool",
            new=AsyncMock(side_effect=MdqServiceError("unexpected failure")),
        ):
            response = client.post(
                "/v1/call_tool",
                json={"name": "outline", "args": {"path": "/tmp/x.md"}},
            )
        assert response.status_code == 500
        assert response.json() == {"detail": "unexpected_error"}

    def test_session_id_from_header_and_request_id_from_middleware_state(
        self, audit_records
    ) -> None:
        """The record's session_id comes from the x-session-id header and its request_id
        from request.state.request_id, which attach_auth_middleware
        (scripts/mcp_servers/server.py) always populates with a fresh UUID before the
        handler runs, so the x-request-id header fallback is never reached on this server.
        """
        _client().post(
            "/v1/call_tool",
            json={"name": "outline", "args": {"path": "/tmp/x.md"}},
            headers={"x-request-id": "req-123", "x-session-id": "sess-456"},
        )
        record = audit_records()[0]
        assert record["session_id"] == "sess-456"
        assert record["request_id"] != "req-123"
        assert record["request_id"]


class TestToolLevelErrorCodes:
    """The tool-level classes stay HTTP 200 with is_error=true and carry the code."""

    def test_tool_level_error_response_carries_the_code(self, audit_records) -> None:
        client = _client()
        with patch(
            "mcp_servers.mdq.mdq_server._dispatch_mdq_tool",
            new=AsyncMock(side_effect=MdqValidationError("bad regex")),
        ):
            response = client.post(
                "/v1/call_tool",
                json={"name": "search_docs", "args": {"query": "("}},
            )
        assert response.status_code == 200
        body = response.json()
        assert body["is_error"] is True
        assert body["result"] == "validation_error"

        record = audit_records()[0]
        assert record["outcome"] == "error"
        assert record["error_type"] == "validation_error"


class TestUnknownToolAuditDetail:
    """call_tool's audit `detail` for a dispatch-level tool error (r.is_error
    True without a raised exception, e.g. an unknown tool name)."""

    def test_unknown_tool_name_reports_error_kind_tool_error(
        self, audit_records
    ) -> None:
        response = _client().post(
            "/v1/call_tool",
            json={"name": "not_a_real_tool", "args": {}},
        )
        # dispatch_tool() returns an error DispatchResult without raising —
        # HTTP 200 per MCP spec, is_error=True in the body.
        assert response.status_code == 200
        assert response.json()["is_error"] is True
        detail = audit_records()[0]["detail"]
        assert "error_kind=tool_error" in detail


class TestGetChunkTruncationAuditDetail:
    """call_tool's audit `detail` for get_chunk, sourced from the '[Truncated'
    marker in the tool's own output text (the one tool whose truncation flag
    is not carried via structured metadata)."""

    def _chunk_id(self, service: MdqService, md_file: Path) -> str:
        import asyncio

        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(md_file)])))
        conn = service._get_db_connection()
        try:
            row = conn.execute("SELECT chunk_id FROM chunks LIMIT 1").fetchone()
        finally:
            conn.close()
        return str(row["chunk_id"])

    def test_truncated_chunk_reports_truncated_true(
        self, service: MdqService, tmp_path: Path, audit_records
    ) -> None:
        md_file = tmp_path / "long.md"
        md_file.write_text(
            "# Heading\n\nThis content is much longer than ten characters.",
            encoding="utf-8",
        )
        service.max_chars_per_chunk = 10
        chunk_id = self._chunk_id(service, md_file)

        response = _client().post(
            "/v1/call_tool",
            json={"name": "get_chunk", "args": {"chunk_id": chunk_id}},
        )
        assert response.status_code == 200
        assert "[Truncated" in response.json()["result"]
        assert "truncated=true" in audit_records()[0]["detail"]

    def test_non_truncated_chunk_omits_truncated_flag(
        self, service: MdqService, tmp_path: Path, audit_records
    ) -> None:
        md_file = tmp_path / "short.md"
        md_file.write_text("# Heading\n\nShort.", encoding="utf-8")
        chunk_id = self._chunk_id(service, md_file)

        response = _client().post(
            "/v1/call_tool",
            json={"name": "get_chunk", "args": {"chunk_id": chunk_id}},
        )
        assert response.status_code == 200
        assert "truncated=true" not in audit_records()[0]["detail"]
