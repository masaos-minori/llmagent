"""tests/test_mdq_health.py

New `/health` fields: `allowed_dirs_count` and `deny_all` (mdq-mcp deny-all visibility).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

from httpx import ASGITransport, AsyncClient

from scripts.mcp_servers.mdq.mdq_server import app


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


def _mock_config_with_allowed_dirs(db_path: str, allowed_dirs: list[str]) -> dict:
    return {"db_path": db_path, "allowed_dirs": allowed_dirs}


class TestHealthAllowedDirsVisibility:
    async def test_deny_all_reports_zero_count_and_true(self, tmp_path: Path) -> None:
        db_path = _create_test_db(tmp_path)
        with patch("mcp_servers.mdq.health_check.ConfigLoader") as MockConfig:
            MockConfig.return_value.load.return_value = _mock_config_with_allowed_dirs(
                db_path, []
            )
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/health")
        body = resp.json()
        assert body["details"]["allowed_dirs_count"] == 0
        assert body["details"]["deny_all"] is True

    async def test_non_empty_allowed_dirs_reports_count_and_false(
        self, tmp_path: Path
    ) -> None:
        db_path = _create_test_db(tmp_path)
        with patch("mcp_servers.mdq.health_check.ConfigLoader") as MockConfig:
            MockConfig.return_value.load.return_value = _mock_config_with_allowed_dirs(
                db_path, ["/some/dir", "/other/dir"]
            )
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/health")
        body = resp.json()
        assert body["details"]["allowed_dirs_count"] == 2
        assert body["details"]["deny_all"] is False

    async def test_missing_allowed_dirs_key_treated_as_deny_all(
        self, tmp_path: Path
    ) -> None:
        db_path = _create_test_db(tmp_path)
        with patch("mcp_servers.mdq.health_check.ConfigLoader") as MockConfig:
            MockConfig.return_value.load.return_value = {"db_path": db_path}
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/health")
        body = resp.json()
        assert body["details"]["allowed_dirs_count"] == 0
        assert body["details"]["deny_all"] is True

    async def test_raw_allowed_dirs_paths_not_exposed(self, tmp_path: Path) -> None:
        db_path = _create_test_db(tmp_path)
        with patch("mcp_servers.mdq.health_check.ConfigLoader") as MockConfig:
            MockConfig.return_value.load.return_value = _mock_config_with_allowed_dirs(
                db_path, ["/secret/path"]
            )
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/health")
        assert "/secret/path" not in resp.text
