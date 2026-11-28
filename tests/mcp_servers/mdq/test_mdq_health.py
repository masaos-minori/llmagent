"""tests/mcp_servers/mdq/test_mdq_health.py

New `/health` fields: `allowed_dirs_count` and `deny_all` (mdq-mcp deny-all visibility).

The ordinary health body reports non-sensitive state only, so these tests assert the state codes
the body carries and that no configuration path, database path, or database-wide count reaches it
(REQ-003). The startup result is supplied by the test rather than read from the production
configuration, so no test depends on a host path.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import MappingProxyType
from unittest.mock import patch

from httpx import ASGITransport, AsyncClient
from mcp_servers.mdq import mdq_server
from mcp_servers.mdq.startup_config import StartupConfig
from shared.mcp_health_contract import parse_health_body

from tests.mcp_servers._auth_headers import MCP_TEST_AUTH_HEADERS

SECRET_DIR = "/secret/path"


def _create_test_db(tmp_path: Path) -> str:
    """Create a minimal schema-valid test DB (documents/chunks/chunks_fts + trigger stubs)."""
    path = str(tmp_path / "mdq_health_allowed_dirs_test.sqlite")
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


def _startup(db_path: str, values: dict[str, object]) -> StartupConfig:
    """The shared startup result with only the keys a test cares about supplied."""
    return StartupConfig(
        values=MappingProxyType(values),
        db_path=db_path,
        auth_token="test-token",
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


class TestHealthAllowedDirsVisibility:
    async def test_deny_all_reports_zero_count_and_true(self, tmp_path: Path) -> None:
        _, body = await _get_health(
            _startup(_create_test_db(tmp_path), {"allowed_dirs": []})
        )
        assert body["details"]["allowed_dirs_count"] == 0
        assert body["details"]["deny_all"] is True

    async def test_non_empty_allowed_dirs_reports_count_and_false(
        self, tmp_path: Path
    ) -> None:
        _, body = await _get_health(
            _startup(_create_test_db(tmp_path), {"allowed_dirs": ["a", "b"]})
        )
        assert body["details"]["allowed_dirs_count"] == 2
        assert body["details"]["deny_all"] is False

    async def test_missing_allowed_dirs_key_treated_as_deny_all(
        self, tmp_path: Path
    ) -> None:
        _, body = await _get_health(_startup(_create_test_db(tmp_path), {}))
        assert body["details"]["allowed_dirs_count"] == 0
        assert body["details"]["deny_all"] is True

    async def test_raw_allowed_dirs_paths_not_exposed(self, tmp_path: Path) -> None:
        startup = _startup(_create_test_db(tmp_path), {"allowed_dirs": [SECRET_DIR]})
        with patch.object(mdq_server, "_cfg", startup):
            async with AsyncClient(
                transport=ASGITransport(app=mdq_server.app),
                base_url="http://test",
                headers=MCP_TEST_AUTH_HEADERS,
            ) as client:
                resp = await client.get("/health")
        assert SECRET_DIR not in resp.text


class TestHealthReportsStateCodes:
    """Readiness is reported through the closed state and reason vocabularies (REQ-003)."""

    async def test_ready_body_reports_the_corpus_capability_as_ok(
        self, tmp_path: Path
    ) -> None:
        startup = _startup(_create_test_db(tmp_path), {"allowed_dirs": [str(tmp_path)]})
        _, body = await _get_health(startup)
        report = parse_health_body(body)
        assert report.ready is True
        assert report.capabilities["mdq.corpus"].state == "ok"
        assert report.degraded_reasons == ()

    async def test_details_carrys_only_non_sensitive_state(
        self, tmp_path: Path
    ) -> None:
        startup = _startup(_create_test_db(tmp_path), {"allowed_dirs": [str(tmp_path)]})
        _, body = await _get_health(startup)
        details = body["details"]
        assert details["service"] == "mdq-mcp"
        assert "allowed_dirs_count" in details
        assert "deny_all" in details
        # `dedup` is the read-only metrics block the handler merges in; nothing else may appear.
        assert set(details) <= {"service", "allowed_dirs_count", "deny_all", "dedup"}

    async def test_details_carrys_no_database_wide_count_or_timestamp(
        self, tmp_path: Path
    ) -> None:
        _, body = await _get_health(
            _startup(_create_test_db(tmp_path), {"allowed_dirs": [str(tmp_path)]})
        )
        for key in (
            "database",
            "document_count",
            "chunk_count",
            "fts_row_count",
            "stale_document_count",
            "last_indexed",
        ):
            assert key not in body["details"]

    async def test_body_carries_no_absolute_database_path(self, tmp_path: Path) -> None:
        startup = _startup(_create_test_db(tmp_path), {"allowed_dirs": [str(tmp_path)]})
        with patch.object(mdq_server, "_cfg", startup):
            async with AsyncClient(
                transport=ASGITransport(app=mdq_server.app),
                base_url="http://test",
                headers=MCP_TEST_AUTH_HEADERS,
            ) as client:
                resp = await client.get("/health")
        assert str(tmp_path) not in resp.text
