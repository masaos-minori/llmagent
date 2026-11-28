"""tests/mcp_servers/mdq/test_mdq_health_endpoint.py

Full acceptance-criteria coverage for mdq-mcp /health endpoint.

Tests against the current production schema: chunks/chunks_fts/documents/index_state. Uses
httpx.ASGITransport for FastAPI app testing, and supplies the shared startup-configuration result
for the test DB path instead of patching a configuration read (REQ-007). The body assertions pin
the closed state and reason vocabularies: no absolute database path, no database-wide count, no
database-wide timestamp, and no configuration path (REQ-003).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import MappingProxyType
from unittest.mock import patch

from httpx import ASGITransport, AsyncClient
from mcp_servers.mdq import mdq_server
from mcp_servers.mdq.startup_config import StartupConfig
from shared.mcp_health_contract import (
    HEALTH_REASON_SERVER_UNAVAILABLE,
    parse_health_body,
)

from tests.mcp_servers._auth_headers import MCP_TEST_AUTH_HEADERS

DOCUMENTS_SQL = """
CREATE TABLE documents (
    doc_id TEXT PRIMARY KEY,
    source_path TEXT NOT NULL,
    mtime_ns INTEGER NOT NULL,
    size_bytes INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    indexed_at REAL NOT NULL
)
"""
CHUNKS_SQL = """
CREATE TABLE chunks (
    chunk_id TEXT UNIQUE NOT NULL,
    doc_id TEXT NOT NULL,
    source_path TEXT NOT NULL,
    heading TEXT NOT NULL,
    content TEXT NOT NULL,
    indexed_at REAL NOT NULL
)
"""
FTS_SQL = """
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
# A regular table named chunks_fts without the probe column: the FTS5 probe query fails on it.
CORRUPT_FTS_SQL = "CREATE TABLE chunks_fts (rowid INTEGER PRIMARY KEY, col1 TEXT)"
FULL_TRIGGERS = ("chunks_ai", "chunks_ad", "chunks_au")


def _create_db(
    tmp_path: Path,
    name: str,
    tables: dict[str, str],
    triggers: tuple[str, ...] = FULL_TRIGGERS,
) -> str:
    """Create a test database from the given tables and trigger stubs."""
    path = str(tmp_path / name)
    conn = sqlite3.connect(path)
    try:
        for sql in tables.values():
            conn.execute(sql)
        # A trigger needs its table, so trigger stubs are only created when chunks exists.
        if "chunks" in tables:
            for trigger in triggers:
                conn.execute(
                    f"CREATE TRIGGER {trigger} AFTER INSERT ON chunks BEGIN SELECT 1; END"  # nosec B608 — trigger names are fixed constants
                )
        conn.commit()
    finally:
        conn.close()
    return path


def _create_test_db(tmp_path: Path) -> str:
    """The full production-shape schema: documents, chunks, chunks_fts, and the three triggers."""
    return _create_db(
        tmp_path,
        "mdq_health_test.sqlite",
        {"documents": DOCUMENTS_SQL, "chunks": CHUNKS_SQL, "chunks_fts": FTS_SQL},
    )


def _create_test_db_no_documents(tmp_path: Path) -> str:
    """A test database missing the documents table."""
    return _create_db(
        tmp_path,
        "mdq_no_documents.sqlite",
        {"chunks": CHUNKS_SQL, "chunks_fts": FTS_SQL},
    )


def _create_test_db_no_chunks(tmp_path: Path) -> str:
    """A test database with documents but missing the chunks table."""
    return _create_db(
        tmp_path,
        "mdq_no_chunks.sqlite",
        {"documents": DOCUMENTS_SQL, "chunks_fts": FTS_SQL},
    )


def _create_test_db_no_chunks_fts(tmp_path: Path) -> str:
    """A test database missing the chunks_fts table."""
    return _create_db(
        tmp_path,
        "mdq_no_fts.sqlite",
        {"documents": DOCUMENTS_SQL, "chunks": CHUNKS_SQL},
    )


def _create_test_db_no_triggers(tmp_path: Path) -> str:
    """A test database with the tables but no triggers."""
    return _create_db(
        tmp_path,
        "mdq_no_triggers.sqlite",
        {"documents": DOCUMENTS_SQL, "chunks": CHUNKS_SQL, "chunks_fts": FTS_SQL},
        triggers=(),
    )


def _create_test_db_no_ai_trigger(tmp_path: Path) -> str:
    """A test database missing only the chunks_ai trigger."""
    return _create_db(
        tmp_path,
        "mdq_no_ai.sqlite",
        {"documents": DOCUMENTS_SQL, "chunks": CHUNKS_SQL, "chunks_fts": FTS_SQL},
        triggers=("chunks_ad", "chunks_au"),
    )


def _create_test_db_corrupt_fts(tmp_path: Path) -> str:
    """A test database with a regular table named chunks_fts (corrupt FTS5) and trigger stubs."""
    return _create_db(
        tmp_path,
        "mdq_corrupt_fts.sqlite",
        {
            "documents": DOCUMENTS_SQL,
            "chunks": CHUNKS_SQL,
            "chunks_fts": CORRUPT_FTS_SQL,
        },
    )


def _startup(db_path: str, values: dict[str, object] | None = None) -> StartupConfig:
    """The shared startup result pointed at the test DB.

    `allowed_dirs` is present because a deny-all allowlist is a readiness failure, so a test that
    expects a ready response has to supply it. The supplied directory is the directory holding the
    test DB, which always exists, so no test depends on a host path.
    """
    merged: dict[str, object] = {"allowed_dirs": [str(Path(db_path).parent)]}
    if values:
        merged.update(values)
    return StartupConfig(
        values=MappingProxyType(merged), db_path=db_path, auth_token="test-token"
    )


async def _get_health(startup: StartupConfig) -> tuple[int, dict]:
    """Read /health for the supplied startup result, the one the server already holds."""
    with patch.object(mdq_server, "_cfg", startup):
        async with AsyncClient(
            transport=ASGITransport(app=mdq_server.app),
            base_url="http://test",
            headers=MCP_TEST_AUTH_HEADERS,
        ) as client:
            resp = await client.get("/health")
    return resp.status_code, resp.json()


class TestHealthEndpointReady:
    """Verify /health returns ready=true when DB is valid."""

    async def test_health_returns_ready_true_with_valid_schema(
        self, tmp_path: Path
    ) -> None:
        """GET /health returns ready:true when all tables and triggers exist."""
        status, body = await _get_health(_startup(_create_test_db(tmp_path)))
        assert status == 200
        assert body["ready"] is True
        assert body["status"] == "ok"
        assert body["dependencies"] == {}

    async def test_health_response_contains_no_stub_key(self, tmp_path: Path) -> None:
        """Response must not contain a 'stub' key."""
        _, body = await _get_health(_startup(_create_test_db(tmp_path)))
        assert "stub" not in body

    async def test_health_response_details_fields(self, tmp_path: Path) -> None:
        """Response details carries only the non-sensitive state the contract defines."""
        _, body = await _get_health(_startup(_create_test_db(tmp_path)))
        details = body["details"]
        assert details["service"] == "mdq-mcp"
        assert details["allowed_dirs_count"] == 1
        assert details["deny_all"] is False
        assert set(details) <= {"service", "allowed_dirs_count", "deny_all", "dedup"}

    async def test_ready_body_reports_the_capability_state(
        self, tmp_path: Path
    ) -> None:
        """Readiness is reported as the corpus capability state, not as counts."""
        _, body = await _get_health(_startup(_create_test_db(tmp_path)))
        report = parse_health_body(body)
        assert report.capabilities["mdq.corpus"].state == "ok"
        assert report.degraded_reasons == ()


class TestHealthEndpointMissingSchema:
    """Verify /health returns ready=false when required schema elements are missing."""

    async def test_missing_documents_table_returns_ready_false(
        self, tmp_path: Path
    ) -> None:
        """Missing documents table → ready:false with the availability reason code."""
        _, body = await _get_health(_startup(_create_test_db_no_documents(tmp_path)))
        assert body["ready"] is False
        assert body["status"] == "degraded"
        assert body["dependencies"]["db_schema"] == HEALTH_REASON_SERVER_UNAVAILABLE

    async def test_missing_chunks_table_returns_ready_false(
        self, tmp_path: Path
    ) -> None:
        """Missing chunks table → ready:false with the same reason code."""
        _, body = await _get_health(_startup(_create_test_db_no_chunks(tmp_path)))
        assert body["ready"] is False
        assert body["status"] == "degraded"
        assert body["dependencies"]["db_schema"] == HEALTH_REASON_SERVER_UNAVAILABLE

    async def test_missing_chunks_fts_table_returns_ready_false(
        self, tmp_path: Path
    ) -> None:
        """Missing chunks_fts table → ready:false with the same reason code."""
        _, body = await _get_health(_startup(_create_test_db_no_chunks_fts(tmp_path)))
        assert body["ready"] is False
        assert body["dependencies"]["db_schema"] == HEALTH_REASON_SERVER_UNAVAILABLE

    async def test_missing_triggers_returns_ready_false(self, tmp_path: Path) -> None:
        """Missing triggers → ready:false."""
        _, body = await _get_health(_startup(_create_test_db_no_triggers(tmp_path)))
        assert body["ready"] is False
        assert body["dependencies"]["db_schema"] == HEALTH_REASON_SERVER_UNAVAILABLE

    async def test_fts5_query_failure_returns_ready_false(self, tmp_path: Path) -> None:
        """FTS5 query failure → ready:false on its own dependency key."""
        _, body = await _get_health(_startup(_create_test_db_corrupt_fts(tmp_path)))
        assert body["ready"] is False
        assert body["dependencies"]["fts5"] == HEALTH_REASON_SERVER_UNAVAILABLE

    async def test_degraded_body_names_the_capability_as_unavailable(
        self, tmp_path: Path
    ) -> None:
        """A schema failure makes the corpus capability unavailable, and the reason is reported."""
        _, body = await _get_health(_startup(_create_test_db_no_chunks(tmp_path)))
        report = parse_health_body(body)
        assert report.capabilities["mdq.corpus"].state == "unavailable"
        assert report.capabilities["mdq.corpus"].reason_code == (
            HEALTH_REASON_SERVER_UNAVAILABLE
        )
        assert report.degraded_reasons == (HEALTH_REASON_SERVER_UNAVAILABLE,)

    async def test_db_file_not_found_returns_ready_false(self, tmp_path: Path) -> None:
        """Missing DB file → ready:false, and the value names no path."""
        _, body = await _get_health(_startup(str(tmp_path / "nonexistent.mdq.sqlite")))
        assert body["ready"] is False
        assert body["dependencies"]["db_file"] == HEALTH_REASON_SERVER_UNAVAILABLE
        assert str(tmp_path) not in str(body)


class TestHealthEndpointNonSensitiveBody:
    """The ordinary health body reports state codes, not database-wide facts (REQ-003)."""

    async def test_body_carries_no_database_path(self, tmp_path: Path) -> None:
        """No absolute database path appears anywhere in the body."""
        db_path = _create_test_db(tmp_path)
        _, body = await _get_health(_startup(db_path))
        assert str(tmp_path) not in str(body)

    async def test_body_carries_no_database_wide_counts(self, tmp_path: Path) -> None:
        """Counts the posture judges are not written into the health body."""
        db_path = _create_test_db(tmp_path)
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                "INSERT INTO documents (doc_id, source_path, mtime_ns, size_bytes, content_hash, indexed_at) VALUES (?, ?, ?, ?, ?, ?)",
                ("doc1", "/test/file.md", 1000000, 1024, "abc", 1000.0),
            )
            conn.execute(
                "INSERT INTO chunks (chunk_id, doc_id, source_path, heading, content, indexed_at) VALUES (?, ?, ?, ?, ?, ?)",
                ("chunk1", "doc1", "/test/file.md", "Heading", "content", 1000.0),
            )
            conn.commit()
        finally:
            conn.close()
        _, body = await _get_health(_startup(db_path))
        for key in (
            "document_count",
            "chunk_count",
            "fts_row_count",
            "stale_document_count",
            "last_indexed",
        ):
            assert key not in body["details"]

    async def test_degraded_response_reports_reason_codes_only(
        self, tmp_path: Path
    ) -> None:
        """A degraded body holds reason codes and no configuration path (AC-2, AC-4)."""
        _, body = await _get_health(_startup(_create_test_db_no_documents(tmp_path)))
        for value in body["dependencies"].values():
            assert value in {HEALTH_REASON_SERVER_UNAVAILABLE}
        assert "config" not in body["dependencies"]


class TestHealthEndpointStatusCodes:
    """Verify the status code follows readiness (MCP-08 guidance)."""

    async def test_health_returns_http_200_when_ready(self, tmp_path: Path) -> None:
        status, _ = await _get_health(_startup(_create_test_db(tmp_path)))
        assert status == 200

    async def test_health_returns_http_503_when_degraded(self, tmp_path: Path) -> None:
        status, _ = await _get_health(_startup(_create_test_db_no_chunks(tmp_path)))
        assert status == 503

    async def test_health_response_has_correct_top_level_keys(
        self, tmp_path: Path
    ) -> None:
        """Response has exactly the expected top-level keys."""
        _, body = await _get_health(_startup(_create_test_db(tmp_path)))
        assert {"status", "ready", "dependencies", "details"}.issubset(body.keys())
        assert body["status"] in ("ok", "degraded")
        assert isinstance(body["ready"], bool)
        assert isinstance(body["dependencies"], dict)
        assert isinstance(body["details"], dict)
