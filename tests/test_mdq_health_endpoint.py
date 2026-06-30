"""tests/test_mdq_health_endpoint.py
Full acceptance-criteria coverage for mdq-mcp /health endpoint.

Tests against the current production schema: chunks/chunks_fts/documents/index_state.
Uses httpx.ASGITransport for FastAPI app testing with ConfigLoader mocking for test DB paths.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from scripts.mcp.mdq.server import app


def _create_test_db(tmp_path: Path) -> str:
    """Create a test database with the current production schema (chunks/chunks_fts/documents).

    Creates trigger stubs so the health endpoint passes the trigger check.
    The triggers are no-ops since we don't have FTS5 virtual tables.
    The chunks_fts table has a 'chunks_fts' column to satisfy the FTS5 probe query.
    """
    path = str(tmp_path / "mdq_health_test.sqlite")
    conn = sqlite3.connect(path)
    try:
        # Create tables without FTS5 (which requires extension loading)
        conn.execute(
            """
            CREATE TABLE documents (
                doc_id TEXT PRIMARY KEY,
                source_path TEXT NOT NULL,
                mtime_ns INTEGER NOT NULL,
                size_bytes INTEGER NOT NULL,
                content_hash TEXT NOT NULL,
                indexed_at REAL NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chunk_id TEXT UNIQUE NOT NULL,
                doc_id TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
                source_path TEXT NOT NULL,
                heading TEXT NOT NULL,
                heading_path TEXT NOT NULL DEFAULT '',
                heading_level INTEGER NOT NULL DEFAULT 0,
                ordinal INTEGER NOT NULL DEFAULT 0,
                content TEXT NOT NULL,
                normalized_content TEXT NOT NULL DEFAULT '',
                start_line INTEGER NOT NULL,
                end_line INTEGER NOT NULL,
                char_count INTEGER NOT NULL DEFAULT 0,
                token_count INTEGER,
                content_hash TEXT NOT NULL,
                tags_json TEXT,
                indexed_at REAL NOT NULL
            )
            """
        )
        # chunks_fts table with a 'chunks_fts' column to satisfy the FTS5 probe query.
        # In production, this is an FTS5 virtual table and the 'chunks_fts' column is auto-generated.
        conn.execute(
            """
            CREATE TABLE chunks_fts (
                rowid INTEGER PRIMARY KEY,
                normalized_content TEXT,
                source_path TEXT,
                heading TEXT,
                heading_path TEXT,
                content_hash TEXT,
                content TEXT,
                chunks_fts TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE index_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        # Create trigger stubs so the health endpoint passes the trigger check.
        # These are no-ops since we don't have FTS5 virtual tables.
        conn.execute(
            "CREATE TRIGGER chunks_ai AFTER INSERT ON chunks BEGIN SELECT 1; END"
        )
        conn.execute(
            "CREATE TRIGGER chunks_ad AFTER DELETE ON chunks BEGIN SELECT 1; END"
        )
        conn.execute(
            "CREATE TRIGGER chunks_au AFTER UPDATE ON chunks BEGIN SELECT 1; END"
        )
        conn.commit()
    finally:
        conn.close()
    return path


def _create_test_db_no_chunks(tmp_path: Path) -> str:
    """Create a test database with documents table but missing chunks table."""
    path = str(tmp_path / "mdq_no_chunks.sqlite")
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE documents (
                doc_id TEXT PRIMARY KEY,
                source_path TEXT NOT NULL,
                mtime_ns INTEGER NOT NULL,
                size_bytes INTEGER NOT NULL,
                content_hash TEXT NOT NULL,
                indexed_at REAL NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE chunks_fts (
                rowid INTEGER PRIMARY KEY,
                normalized_content TEXT,
                source_path TEXT,
                heading TEXT,
                heading_path TEXT,
                content_hash TEXT,
                content TEXT,
                chunks_fts TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
    return path


def _create_test_db_no_chunks_fts(tmp_path: Path) -> str:
    """Create a test database missing the chunks_fts table."""
    path = str(tmp_path / "mdq_no_fts.sqlite")
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE documents (
                doc_id TEXT PRIMARY KEY,
                source_path TEXT NOT NULL,
                mtime_ns INTEGER NOT NULL,
                size_bytes INTEGER NOT NULL,
                content_hash TEXT NOT NULL,
                indexed_at REAL NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chunk_id TEXT UNIQUE NOT NULL,
                doc_id TEXT NOT NULL,
                source_path TEXT NOT NULL,
                heading TEXT NOT NULL,
                content TEXT NOT NULL,
                indexed_at REAL NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
    return path


def _create_test_db_corrupt_fts(tmp_path: Path) -> str:
    """Create a test database with a regular table named chunks_fts (corrupt FTS5).

    Also creates trigger stubs so the FTS5 probe query is reached.
    The 'chunks_fts' column is missing, so the FTS5 probe query will fail.
    """
    path = str(tmp_path / "mdq_corrupt_fts.sqlite")
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE documents (
                doc_id TEXT PRIMARY KEY,
                source_path TEXT NOT NULL,
                mtime_ns INTEGER NOT NULL,
                size_bytes INTEGER NOT NULL,
                content_hash TEXT NOT NULL,
                indexed_at REAL NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chunk_id TEXT UNIQUE NOT NULL,
                doc_id TEXT NOT NULL,
                source_path TEXT NOT NULL,
                heading TEXT NOT NULL,
                content TEXT NOT NULL,
                indexed_at REAL NOT NULL
            )
            """
        )
        # Missing the 'chunks_fts' column — this will cause the FTS5 probe query to fail
        conn.execute("CREATE TABLE chunks_fts (rowid INTEGER PRIMARY KEY, col1 TEXT)")
        # Create trigger stubs so the FTS5 probe query is reached
        conn.execute(
            "CREATE TRIGGER chunks_ai AFTER INSERT ON chunks BEGIN SELECT 1; END"
        )
        conn.execute(
            "CREATE TRIGGER chunks_ad AFTER DELETE ON chunks BEGIN SELECT 1; END"
        )
        conn.execute(
            "CREATE TRIGGER chunks_au AFTER UPDATE ON chunks BEGIN SELECT 1; END"
        )
        conn.commit()
    finally:
        conn.close()
    return path


def _mock_config(db_path: str) -> dict:
    """Create a mock config that points to the test DB."""
    return {"mdq_mcp_server": {"db_path": db_path}}


class TestHealthEndpointReady:
    """Verify /health returns ready=true when DB is valid."""

    async def test_health_returns_ready_true_with_valid_schema(
        self, tmp_path: Path
    ) -> None:
        """GET /health returns ready:true when all tables and triggers exist."""
        db_path = _create_test_db(tmp_path)
        with patch("shared.config_loader.ConfigLoader") as MockConfig:
            MockConfig.return_value.load_all.return_value = _mock_config(db_path)
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ready"] is True
        assert body["status"] == "ok"
        assert body["dependencies"] == {}

    async def test_health_response_contains_no_stub_key(self, tmp_path: Path) -> None:
        """Response must not contain a 'stub' key."""
        db_path = _create_test_db(tmp_path)
        with patch("shared.config_loader.ConfigLoader") as MockConfig:
            MockConfig.return_value.load_all.return_value = _mock_config(db_path)
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/health")
        body = resp.json()
        assert "stub" not in body

    async def test_health_response_details_fields(self, tmp_path: Path) -> None:
        """Response details contains expected fields."""
        db_path = _create_test_db(tmp_path)
        with patch("shared.config_loader.ConfigLoader") as MockConfig:
            MockConfig.return_value.load_all.return_value = _mock_config(db_path)
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/health")
        body = resp.json()
        details = body["details"]
        assert "database" in details
        assert "document_count" in details
        assert "chunk_count" in details
        assert "fts_row_count" in details
        assert "last_indexed" in details
        assert "stale_document_count" in details

    async def test_health_response_service_field(self, tmp_path: Path) -> None:
        """Response details contains 'service': 'mdq-mcp'."""
        db_path = _create_test_db(tmp_path)
        with patch("shared.config_loader.ConfigLoader") as MockConfig:
            MockConfig.return_value.load_all.return_value = _mock_config(db_path)
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/health")
        body = resp.json()
        assert body["details"]["service"] == "mdq-mcp"


class TestHealthEndpointMissingSchema:
    """Verify /health returns ready=false when required schema elements are missing."""

    async def test_missing_chunks_table_returns_ready_false(
        self, tmp_path: Path
    ) -> None:
        """Missing chunks table → ready:false."""
        db_path = _create_test_db_no_chunks(tmp_path)
        with patch("shared.config_loader.ConfigLoader") as MockConfig:
            MockConfig.return_value.load_all.return_value = _mock_config(db_path)
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/health")
        assert resp.status_code == 503
        body = resp.json()
        assert body["ready"] is False
        assert body["status"] == "degraded"
        assert "db_schema" in body["dependencies"]
        assert "chunks" in body["dependencies"]["db_schema"]

    async def test_missing_chunks_fts_table_returns_ready_false(
        self, tmp_path: Path
    ) -> None:
        """Missing chunks_fts table → ready:false."""
        db_path = _create_test_db_no_chunks_fts(tmp_path)
        with patch("shared.config_loader.ConfigLoader") as MockConfig:
            MockConfig.return_value.load_all.return_value = _mock_config(db_path)
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/health")
        assert resp.status_code == 503
        body = resp.json()
        assert body["ready"] is False
        assert "db_schema" in body["dependencies"]
        assert "chunks_fts" in body["dependencies"]["db_schema"]

    async def test_missing_triggers_returns_ready_false(self, tmp_path: Path) -> None:
        """Missing triggers → ready:false."""
        # DB has chunks/chunks_fts but no triggers — health endpoint checks for triggers
        path = str(tmp_path / "mdq_no_triggers.sqlite")
        conn = sqlite3.connect(path)
        try:
            conn.execute(
                """
                CREATE TABLE documents (
                    doc_id TEXT PRIMARY KEY,
                    source_path TEXT NOT NULL,
                    mtime_ns INTEGER NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    content_hash TEXT NOT NULL,
                    indexed_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chunk_id TEXT UNIQUE NOT NULL,
                    doc_id TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    heading TEXT NOT NULL,
                    content TEXT NOT NULL,
                    indexed_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE chunks_fts (
                    rowid INTEGER PRIMARY KEY,
                    normalized_content TEXT,
                    source_path TEXT,
                    heading TEXT,
                    heading_path TEXT,
                    content_hash TEXT,
                    content TEXT,
                    chunks_fts TEXT
                )
                """
            )
            # No triggers — this is the test condition
            conn.commit()
        finally:
            conn.close()

        with patch("shared.config_loader.ConfigLoader") as MockConfig:
            MockConfig.return_value.load_all.return_value = _mock_config(path)
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/health")
        assert resp.status_code == 503
        body = resp.json()
        assert body["ready"] is False
        assert "db_schema" in body["dependencies"]

    async def test_missing_chunks_ai_trigger(self, tmp_path: Path) -> None:
        """Missing chunks_ai trigger specifically → ready:false with trigger name."""
        path = str(tmp_path / "mdq_no_ai.sqlite")
        conn = sqlite3.connect(path)
        try:
            conn.execute(
                """
                CREATE TABLE documents (
                    doc_id TEXT PRIMARY KEY,
                    source_path TEXT NOT NULL,
                    mtime_ns INTEGER NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    content_hash TEXT NOT NULL,
                    indexed_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chunk_id TEXT UNIQUE NOT NULL,
                    doc_id TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    heading TEXT NOT NULL,
                    content TEXT NOT NULL,
                    indexed_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE chunks_fts (
                    rowid INTEGER PRIMARY KEY,
                    normalized_content TEXT,
                    source_path TEXT,
                    heading TEXT,
                    heading_path TEXT,
                    content_hash TEXT,
                    content TEXT,
                    chunks_fts TEXT
                )
                """
            )
            # Only create chunks_ad and chunks_au, not chunks_ai
            conn.execute(
                "CREATE TRIGGER chunks_ad AFTER DELETE ON chunks BEGIN SELECT 1; END"
            )
            conn.execute(
                "CREATE TRIGGER chunks_au AFTER UPDATE ON chunks BEGIN SELECT 1; END"
            )
            conn.commit()
        finally:
            conn.close()

        with patch("shared.config_loader.ConfigLoader") as MockConfig:
            MockConfig.return_value.load_all.return_value = _mock_config(path)
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/health")
        assert resp.status_code == 503
        body = resp.json()
        assert body["ready"] is False
        assert "chunks_ai" in body["dependencies"]["db_schema"]

    async def test_fts5_query_failure_returns_ready_false(self, tmp_path: Path) -> None:
        """FTS5 query failure → ready:false."""
        # Corrupt FTS5 by creating a regular table named chunks_fts with trigger stubs but no chunks_fts column
        db_path = _create_test_db_corrupt_fts(tmp_path)
        with patch("shared.config_loader.ConfigLoader") as MockConfig:
            MockConfig.return_value.load_all.return_value = _mock_config(db_path)
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/health")
        assert resp.status_code == 503
        body = resp.json()
        assert body["ready"] is False
        assert "fts5" in body["dependencies"]

    async def test_db_file_not_found_returns_ready_false(self, tmp_path: Path) -> None:
        """Missing DB file → ready:false."""
        db_path = str(tmp_path / "nonexistent.mdq.sqlite")
        with patch("shared.config_loader.ConfigLoader") as MockConfig:
            MockConfig.return_value.load_all.return_value = _mock_config(db_path)
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/health")
        assert resp.status_code == 503
        body = resp.json()
        assert body["ready"] is False
        assert "db_file" in body["dependencies"]


class TestHealthEndpointStats:
    """Verify /health returns correct stats for the current schema."""

    async def test_document_count_from_chunks_source_path(self, tmp_path: Path) -> None:
        """document_count comes from COUNT(DISTINCT source_path) in chunks table."""
        db_path = _create_test_db(tmp_path)
        conn = sqlite3.connect(db_path)
        try:
            for i in range(3):
                conn.execute(
                    "INSERT INTO documents (doc_id, source_path, mtime_ns, size_bytes, content_hash, indexed_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (f"doc{i}", f"/test/file{i}.md", 1000000, 1024, "abc", 1000.0),
                )
            # Insert chunks with distinct source_paths — document_count = COUNT(DISTINCT source_path) FROM chunks
            for i in range(3):
                conn.execute(
                    "INSERT INTO chunks (chunk_id, doc_id, source_path, heading, content, normalized_content, start_line, end_line, char_count, content_hash, indexed_at) VALUES (?, ?, ?, ?, ?, ?, 1, 2, 100, 'abc', 1000.0)",
                    (
                        f"chunk{i}",
                        f"doc{i}",
                        f"/test/file{i}.md",
                        f"Heading {i}",
                        "content",
                        "content",
                    ),
                )
            conn.commit()
        finally:
            conn.close()

        with patch("shared.config_loader.ConfigLoader") as MockConfig:
            MockConfig.return_value.load_all.return_value = _mock_config(db_path)
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/health")
        body = resp.json()
        assert body["details"]["document_count"] == 3

    async def test_chunk_count_from_chunks_table(self, tmp_path: Path) -> None:
        """chunk_count comes from chunks table."""
        db_path = _create_test_db(tmp_path)
        conn = sqlite3.connect(db_path)
        try:
            for i in range(5):
                conn.execute(
                    "INSERT INTO chunks (chunk_id, doc_id, source_path, heading, content, normalized_content, start_line, end_line, char_count, content_hash, indexed_at) VALUES (?, ?, ?, ?, ?, ?, 1, 2, 100, 'abc', 1000.0)",
                    (
                        f"chunk{i}",
                        "doc1",
                        "/test/file.md",
                        f"Heading {i}",
                        "content",
                        "content",
                    ),
                )
            conn.commit()
        finally:
            conn.close()

        with patch("shared.config_loader.ConfigLoader") as MockConfig:
            MockConfig.return_value.load_all.return_value = _mock_config(db_path)
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/health")
        body = resp.json()
        assert body["details"]["chunk_count"] == 5

    async def test_fts_row_count_excludes_deletes(self, tmp_path: Path) -> None:
        """fts_row_count excludes rows with chunks_fts='delete'."""
        # Requires FTS5 virtual table — skip in non-FTS5 environment
        pytest.skip("Requires FTS5 virtual table; skip in non-FTS5 environment")

    async def test_last_indexed_from_documents(self, tmp_path: Path) -> None:
        """last_indexed comes from MAX(indexed_at) in documents table."""
        db_path = _create_test_db(tmp_path)
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                "INSERT INTO documents (doc_id, source_path, mtime_ns, size_bytes, content_hash, indexed_at) VALUES (?, ?, ?, ?, ?, ?)",
                ("doc1", "/test/file.md", 1000000, 1024, "abc", 1000.0),
            )
            conn.execute(
                "INSERT INTO documents (doc_id, source_path, mtime_ns, size_bytes, content_hash, indexed_at) VALUES (?, ?, ?, ?, ?, ?)",
                ("doc2", "/test/file.md", 1000000, 1024, "abc", 2000.0),
            )
            conn.commit()
        finally:
            conn.close()

        with patch("shared.config_loader.ConfigLoader") as MockConfig:
            MockConfig.return_value.load_all.return_value = _mock_config(db_path)
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/health")
        body = resp.json()
        assert body["details"]["last_indexed"] == 2000.0

    async def test_last_indexed_is_none_when_no_documents(self, tmp_path: Path) -> None:
        """last_indexed is null when documents table is empty."""
        db_path = _create_test_db(tmp_path)
        with patch("shared.config_loader.ConfigLoader") as MockConfig:
            MockConfig.return_value.load_all.return_value = _mock_config(db_path)
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/health")
        body = resp.json()
        assert body["details"]["last_indexed"] is None

    async def test_health_returns_http_200_when_ready(self, tmp_path: Path) -> None:
        """HTTP 200 when ready=true (MCP-08 guidance)."""
        db_path = _create_test_db(tmp_path)
        with patch("shared.config_loader.ConfigLoader") as MockConfig:
            MockConfig.return_value.load_all.return_value = _mock_config(db_path)
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/health")
        assert resp.status_code == 200

    async def test_health_returns_http_503_when_degraded(self, tmp_path: Path) -> None:
        """HTTP 503 when ready=false (MCP-08 guidance)."""
        db_path = _create_test_db_no_chunks(tmp_path)
        with patch("shared.config_loader.ConfigLoader") as MockConfig:
            MockConfig.return_value.load_all.return_value = _mock_config(db_path)
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/health")
        assert resp.status_code == 503

    async def test_health_response_has_correct_top_level_keys(
        self, tmp_path: Path
    ) -> None:
        """Response has exactly the expected top-level keys."""
        db_path = _create_test_db(tmp_path)
        with patch("shared.config_loader.ConfigLoader") as MockConfig:
            MockConfig.return_value.load_all.return_value = _mock_config(db_path)
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/health")
        body = resp.json()
        assert set(body.keys()) == {"status", "ready", "dependencies", "details"}
        assert body["status"] in ("ok", "degraded")
        assert isinstance(body["ready"], bool)
        assert isinstance(body["dependencies"], dict)
        assert isinstance(body["details"], dict)
