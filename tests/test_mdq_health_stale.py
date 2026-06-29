"""tests/test_mdq_health_stale.py
Unit tests for mdq-mcp /health stale_document_count field.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    """Create a test database with sections and sections_fts tables."""
    path = str(tmp_path / "mdq_test.sqlite")
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE sections (
                seq INTEGER PRIMARY KEY,
                file_path TEXT NOT NULL,
                heading_path TEXT NOT NULL,
                ordinal INTEGER NOT NULL,
                content TEXT NOT NULL,
                file_mtime REAL NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE VIRTUAL TABLE sections_fts USING fts5(
                file_path, heading_path, ordinal, content,
                content=sections,
                content_rowid=seq
            )
            """
        )
        conn.execute(
            "CREATE TRIGGER sections_ai AFTER INSERT ON sections BEGIN "
            "INSERT INTO sections_fts(rowid, file_path, heading_path, ordinal, content) "
            "VALUES (new.seq, new.file_path, new.heading_path, new.ordinal, new.content); END"
        )
        conn.execute(
            "CREATE TRIGGER sections_ad AFTER DELETE ON sections BEGIN "
            "INSERT INTO sections_fts(sections_fts, rowid, file_path, heading_path, ordinal, content) "
            "VALUES ('delete', old.seq, old.file_path, old.heading_path, old.ordinal, old.content); END"
        )
        conn.execute(
            "CREATE TRIGGER sections_au AFTER UPDATE ON sections BEGIN "
            "INSERT INTO sections_fts(sections_fts, rowid, file_path, heading_path, ordinal, content) "
            "VALUES ('delete', old.seq, old.file_path, old.heading_path, old.ordinal, old.content); "
            "INSERT INTO sections_fts(rowid, file_path, heading_path, ordinal, content) "
            "VALUES (new.seq, new.file_path, new.heading_path, new.ordinal, new.content); END"
        )
        conn.commit()
    finally:
        conn.close()
    return path


def _insert_sections(db_path: str, rows: list[tuple[int, str, float]]) -> None:
    """Insert section rows into the test database."""
    conn = sqlite3.connect(db_path)
    try:
        for seq, file_path, mtime in rows:
            conn.execute(
                "INSERT INTO sections (seq, file_path, heading_path, ordinal, content, file_mtime) VALUES (?, ?, 'h1', 1, 'content', ?)",
                (seq, file_path, mtime),
            )
        conn.commit()
    finally:
        conn.close()


class TestStaleDocumentCount:
    """Verify stale_document_count field in /health response."""

    def test_stale_document_count_zero_when_fresh(self, db_path: str) -> None:
        """When file_mtime matches current mtime, stale count should be 0."""
        # Insert sections with current mtime
        current_mtime = Path(db_path).stat().st_mtime
        _insert_sections(db_path, [(1, "/test/file1.md", current_mtime)])

        # Query for stale documents
        conn = sqlite3.connect(db_path)
        try:
            conn.row_factory = sqlite3.Row
            result = conn.execute(
                "SELECT COUNT(DISTINCT file_path) as cnt FROM sections WHERE file_mtime < ?",
                (current_mtime,),
            ).fetchone()
            stale_count = result["cnt"] or 0
        finally:
            conn.close()

        assert stale_count == 0

    def test_stale_document_count_positive_when_outdated(self, db_path: str) -> None:
        """When file_mtime is older than current mtime, stale count should be > 0."""
        # Insert sections with old mtime (1 day ago)
        import time

        old_mtime = time.time() - 86400
        _insert_sections(db_path, [(1, "/test/file1.md", old_mtime)])

        # Query for stale documents
        conn = sqlite3.connect(db_path)
        try:
            conn.row_factory = sqlite3.Row
            result = conn.execute(
                "SELECT COUNT(DISTINCT file_path) as cnt FROM sections WHERE file_mtime < ?",
                (time.time(),),
            ).fetchone()
            stale_count = result["cnt"] or 0
        finally:
            conn.close()

        assert stale_count == 1

    def test_stale_document_count_mixed(self, db_path: str) -> None:
        """When some files are fresh and some are stale, count only stale."""
        import time

        current_mtime = Path(db_path).stat().st_mtime
        old_mtime = time.time() - 86400

        _insert_sections(
            db_path,
            [
                (1, "/test/file1.md", current_mtime),
                (2, "/test/file2.md", old_mtime),
                (3, "/test/file2.md", old_mtime),
            ],
        )

        # Query for stale documents
        conn = sqlite3.connect(db_path)
        try:
            conn.row_factory = sqlite3.Row
            result = conn.execute(
                "SELECT COUNT(DISTINCT file_path) as cnt FROM sections WHERE file_mtime < ?",
                (time.time(),),
            ).fetchone()
            stale_count = result["cnt"] or 0
        finally:
            conn.close()

        assert stale_count == 2
