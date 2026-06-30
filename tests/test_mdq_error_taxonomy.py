#!/usr/bin/env python3
"""Tests for MDQ error taxonomy and exception handling."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from mcp.mdq.indexer import index_paths
from mcp.mdq.models import (
    GrepDocsRequest,
    IndexPathsRequest,
    MdqAuthorizationError,
    MdqConsistencyError,
    MdqDatabaseError,
    MdqNotFoundError,
    MdqServiceError,
    MdqValidationError,
)
from mcp.mdq.service import MdqService


@pytest.fixture()
def service(tmp_path: Path) -> MdqService:
    db = tmp_path / "mdq.db"
    svc = MdqService(db_path=str(db))
    svc._allowed_dirs = [str(tmp_path)]
    return svc


class TestErrorHierarchy:
    """Test that all error classes inherit from MdqServiceError."""

    def test_mdq_validation_error_inherits_from_service_error(self) -> None:
        assert issubclass(MdqValidationError, MdqServiceError)

    def test_mdq_authorization_error_inherits_from_service_error(self) -> None:
        assert issubclass(MdqAuthorizationError, MdqServiceError)

    def test_mdq_not_found_error_inherits_from_service_error(self) -> None:
        assert issubclass(MdqNotFoundError, MdqServiceError)

    def test_mdq_database_error_inherits_from_service_error(self) -> None:
        assert issubclass(MdqDatabaseError, MdqServiceError)

    def test_mdq_consistency_error_inherits_from_service_error(self) -> None:
        assert issubclass(MdqConsistencyError, MdqServiceError)


class TestValidationError:
    """Test MdqValidationError is raised for validation errors."""

    def test_grep_docs_invalid_regex_raises_validation_error(
        self, service: MdqService
    ) -> None:
        from mcp.mdq.models import GrepDocsRequest

        req = GrepDocsRequest(pattern="[invalid")
        with pytest.raises(MdqValidationError):
            asyncio.run(service.grep_docs(req))


class TestAuthorizationError:
    """Test MdqAuthorizationError is raised for authorization errors."""

    def test_outline_unauthorized_path_raises_authorization_error(
        self, service: MdqService
    ) -> None:
        from mcp.mdq.models import OutlineRequest

        req = OutlineRequest(path="/etc/passwd")
        with pytest.raises(MdqAuthorizationError):
            asyncio.run(service.outline(req))


class TestNotFoundError:
    """Test MdqNotFoundError is raised for not found errors."""

    def test_get_chunk_not_found_raises_not_found_error(
        self, service: MdqService
    ) -> None:
        from mcp.mdq.models import GetChunkRequest

        req = GetChunkRequest(chunk_id="nonexistent")
        with pytest.raises(MdqNotFoundError):
            asyncio.run(service.get_chunk(req))

    def test_outline_file_not_found_raises_not_found_error(
        self, service: MdqService
    ) -> None:
        from mcp.mdq.models import OutlineRequest

        req = OutlineRequest(path="/nonexistent/file.md")
        with pytest.raises(MdqNotFoundError):
            asyncio.run(service.outline(req))


class TestDatabaseError:
    """Test MdqDatabaseError is raised for database errors."""

    def test_database_error_raised_on_connection_failure(
        self, service: MdqService
    ) -> None:
        # Set db_path to a non-existent directory to trigger a DB error
        service.db_path = "/nonexistent/path/mdq.db"
        req = GrepDocsRequest(pattern="test")
        with pytest.raises(MdqDatabaseError):
            asyncio.run(service.grep_docs(req))


class TestConsistencyError:
    """Test MdqConsistencyError is raised for consistency errors."""

    def test_fts_search_raises_consistency_error_on_corrupt_index(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        from mcp.mdq.models import SearchDocsRequest

        # Create a valid index first
        md_file = tmp_path / "test_consistency.md"
        md_file.write_text("# Test\n\nContent")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(md_file)])))
        md_file.unlink()

        # Corrupt the FTS5 index by dropping it
        conn = service._get_db_connection()
        try:
            conn.execute("DROP TABLE IF EXISTS chunks_fts")
            conn.commit()
        finally:
            conn.close()

        req = SearchDocsRequest(query="test")
        with pytest.raises(MdqConsistencyError):
            asyncio.run(service.search_docs(req))


class TestCallToolDomainExceptionHandling:
    """Verify call_tool endpoint maps domain exceptions to is_error=True (MCP spec)."""

    def test_call_tool_returns_is_error_for_validation_exception(
        self, tmp_path: Path
    ) -> None:
        """MdqValidationError from dispatch → is_error=True with HTTP 200."""
        from unittest.mock import AsyncMock, patch

        from fastapi.testclient import TestClient
        from mcp.mdq.server import app

        client = TestClient(app)
        with patch(
            "mcp.mdq.server._dispatch_mdq_tool",
            new=AsyncMock(side_effect=MdqValidationError("bad input")),
        ):
            response = client.post(
                "/v1/call_tool",
                json={"name": "search_docs", "args": {"query": "test"}},
            )
        assert response.status_code == 200
        body = response.json()
        assert body.get("is_error") is True
        assert "bad input" in (body.get("result") or "")

    def test_call_tool_returns_is_error_for_not_found_exception(
        self, tmp_path: Path
    ) -> None:
        """MdqNotFoundError from dispatch → is_error=True with HTTP 200."""
        from unittest.mock import AsyncMock, patch

        from fastapi.testclient import TestClient
        from mcp.mdq.models import MdqNotFoundError
        from mcp.mdq.server import app

        client = TestClient(app)
        with patch(
            "mcp.mdq.server._dispatch_mdq_tool",
            new=AsyncMock(side_effect=MdqNotFoundError("chunk not found")),
        ):
            response = client.post(
                "/v1/call_tool",
                json={"name": "get_chunk", "args": {"chunk_id": "missing"}},
            )
        assert response.status_code == 200
        body = response.json()
        assert body.get("is_error") is True
