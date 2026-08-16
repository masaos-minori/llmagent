"""tests/mcp_servers/mdq/test_mdq_exception_handlers.py

Characterization tests for two previously-uncovered code paths in
mdq_server.py, added ahead of a refactor that extracts (a) the
request-id/session-id parsing duplicated between `_mdq_error_handler` and
`call_tool`, and (b) the per-tool audit `detail_parts` construction inside
`call_tool`:

1. The FastAPI-level exception handlers (MdqDatabaseError, MdqConsistencyError,
   MdqServiceError). These three error types are NOT intercepted by
   call_tool()'s inline try/except, so they propagate out of the endpoint and
   are handled by the module's `@app.exception_handler(...)`-registered
   handlers, which all funnel through the shared `_mdq_error_handler` helper.
2. The `r.is_error` ("error_kind=tool_error") and `get_chunk` truncation
   branches of call_tool()'s per-tool audit-detail construction, which were
   not exercised by any existing test.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from mcp_servers.mdq.indexer import index_paths
from mcp_servers.mdq.mdq_models import (
    IndexPathsRequest,
    MdqConsistencyError,
    MdqDatabaseError,
    MdqServiceError,
)
from mcp_servers.mdq.mdq_server import app
from mcp_servers.mdq.mdq_service import MdqService


class TestMdqDatabaseErrorHandler:
    """MdqDatabaseError raised from dispatch -> HTTP 503 via exception_handler."""

    def test_returns_503_with_detail_message(self) -> None:
        client = TestClient(app)
        with patch(
            "mcp_servers.mdq.server._dispatch_mdq_tool",
            new=AsyncMock(side_effect=MdqDatabaseError("db unavailable")),
        ):
            response = client.post(
                "/v1/call_tool",
                json={"name": "stats", "args": {}},
            )
        assert response.status_code == 503
        assert response.json() == {"detail": "db unavailable"}

    def test_logs_audit_entry_with_error_type(self) -> None:
        client = TestClient(app)
        mock_audit = MagicMock()
        with (
            patch(
                "mcp_servers.mdq.server._dispatch_mdq_tool",
                new=AsyncMock(side_effect=MdqDatabaseError("db unavailable")),
            ),
            patch("mcp_servers.mdq.server._audit_log", new=mock_audit),
        ):
            client.post("/v1/call_tool", json={"name": "stats", "args": {}})
        assert mock_audit.call_args.kwargs["error_type"] == "database_error"
        assert mock_audit.call_args.kwargs["server_key"] == "mdq"
        assert mock_audit.call_args.kwargs["outcome"] == "error"


class TestMdqConsistencyErrorHandler:
    """MdqConsistencyError raised from dispatch -> HTTP 500 via exception_handler."""

    def test_returns_500_with_detail_message(self) -> None:
        client = TestClient(app)
        with patch(
            "mcp_servers.mdq.server._dispatch_mdq_tool",
            new=AsyncMock(side_effect=MdqConsistencyError("index corrupt")),
        ):
            response = client.post(
                "/v1/call_tool",
                json={"name": "search_docs", "args": {"query": "x"}},
            )
        assert response.status_code == 500
        assert response.json() == {"detail": "index corrupt"}


class TestMdqServiceErrorHandler:
    """MdqServiceError raised from dispatch -> HTTP 500 via exception_handler."""

    def test_returns_500_with_detail_message(self) -> None:
        client = TestClient(app)
        with patch(
            "mcp_servers.mdq.server._dispatch_mdq_tool",
            new=AsyncMock(side_effect=MdqServiceError("unexpected failure")),
        ):
            response = client.post(
                "/v1/call_tool",
                json={"name": "outline", "args": {"path": "/tmp/x.md"}},
            )
        assert response.status_code == 500
        assert response.json() == {"detail": "unexpected failure"}

    def test_session_id_from_header_and_request_id_from_middleware_state(self) -> None:
        """_mdq_error_handler reads session_id from the x-session-id header, and
        request_id from request.state.request_id — which attach_auth_middleware
        (scripts/mcp_servers/server.py) always populates with a fresh UUID
        before the handler runs, so the x-request-id header fallback in
        `getattr(request.state, "request_id", ...)` is never actually reached
        on this server. This test locks that (pre-existing) behavior as-is."""
        client = TestClient(app)
        mock_audit = MagicMock()
        with (
            patch(
                "mcp_servers.mdq.server._dispatch_mdq_tool",
                new=AsyncMock(side_effect=MdqServiceError("boom")),
            ),
            patch("mcp_servers.mdq.server._audit_log", new=mock_audit),
        ):
            client.post(
                "/v1/call_tool",
                json={"name": "outline", "args": {"path": "/tmp/x.md"}},
                headers={"x-request-id": "req-123", "x-session-id": "sess-456"},
            )
        assert mock_audit.call_args.kwargs["session_id"] == "sess-456"
        assert mock_audit.call_args.kwargs["request_id"] != "req-123"
        assert mock_audit.call_args.kwargs["request_id"]


class TestUnknownToolAuditDetail:
    """call_tool's audit `detail` for a dispatch-level tool error (r.is_error
    True without a raised exception, e.g. an unknown tool name)."""

    def test_unknown_tool_name_reports_error_kind_tool_error(self) -> None:
        client = TestClient(app)
        mock_audit = MagicMock()
        with patch("mcp_servers.mdq.server._audit_log", new=mock_audit):
            response = client.post(
                "/v1/call_tool",
                json={"name": "not_a_real_tool", "args": {}},
            )
        # dispatch_tool() returns an error DispatchResult without raising —
        # HTTP 200 per MCP spec, is_error=True in the body.
        assert response.status_code == 200
        assert response.json()["is_error"] is True
        detail = mock_audit.call_args.kwargs["detail"]
        assert "error_kind=tool_error" in detail


class TestGetChunkTruncationAuditDetail:
    """call_tool's audit `detail` for get_chunk, sourced from the '[Truncated'
    marker in the tool's own output text (the one tool whose truncation flag
    is not carried via structured metadata)."""

    @pytest.fixture()
    def service(self, tmp_path: Path) -> MdqService:
        db = tmp_path / "mdq.sqlite"
        svc = MdqService(db_path=str(db))
        svc._allowed_dirs = [str(tmp_path)]
        svc.max_chars_per_chunk = 10
        return svc

    def test_truncated_chunk_reports_truncated_true(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        import asyncio

        md_file = tmp_path / "long.md"
        md_file.write_text(
            "# Heading\n\nThis content is much longer than ten characters.",
            encoding="utf-8",
        )
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(md_file)])))
        conn = service._get_db_connection()
        try:
            row = conn.execute("SELECT chunk_id FROM chunks LIMIT 1").fetchone()
        finally:
            conn.close()
        chunk_id = row["chunk_id"]

        client = TestClient(app)
        mock_audit = MagicMock()
        with (
            patch("mcp_servers.mdq.server._service", service),
            patch("mcp_servers.mdq.server._audit_log", new=mock_audit),
        ):
            response = client.post(
                "/v1/call_tool",
                json={"name": "get_chunk", "args": {"chunk_id": chunk_id}},
            )
        assert response.status_code == 200
        assert "[Truncated" in response.json()["result"]
        detail = mock_audit.call_args.kwargs["detail"]
        assert "truncated=true" in detail

    def test_non_truncated_chunk_omits_truncated_flag(self, tmp_path: Path) -> None:
        import asyncio

        db = tmp_path / "mdq2.sqlite"
        service = MdqService(db_path=str(db))
        service._allowed_dirs = [str(tmp_path)]
        md_file = tmp_path / "short.md"
        md_file.write_text("# Heading\n\nShort.", encoding="utf-8")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(md_file)])))
        conn = service._get_db_connection()
        try:
            row = conn.execute("SELECT chunk_id FROM chunks LIMIT 1").fetchone()
        finally:
            conn.close()
        chunk_id = row["chunk_id"]

        client = TestClient(app)
        mock_audit = MagicMock()
        with (
            patch("mcp_servers.mdq.server._service", service),
            patch("mcp_servers.mdq.server._audit_log", new=mock_audit),
        ):
            client.post(
                "/v1/call_tool",
                json={"name": "get_chunk", "args": {"chunk_id": chunk_id}},
            )
        detail = mock_audit.call_args.kwargs["detail"]
        assert "truncated=true" not in detail
