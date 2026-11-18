"""tests/mcp_servers/mdq/test_mdq_foreign_keys.py

FK enforcement lock for MDQ connections (adrchk019 REQ-001 / REQ-002):
- a raw `DELETE FROM documents` cascades to the document's chunks on a connection
  built by the production factory (`MdqService._get_db_connection()`)
- `PRAGMA foreign_keys` returns 1 on connections from `_get_db_connection()` and
  from `create_production_tables()`
- a chunk INSERT referencing a nonexistent `doc_id` is rejected with
  `sqlite3.IntegrityError`

The cascade clause (`db_schema.py` chunks DDL) is exercised here by raw SQL on
purpose: no production delete path bypasses `delete_file_from_index()`'s ordered
deletes, so only FK enforcement can keep this guarantee.
"""

from __future__ import annotations

import sqlite3
from hashlib import sha256
from pathlib import Path

import pytest
from mcp_servers.mdq.db_schema import create_production_tables
from mcp_servers.mdq.index_write import write_document_chunks
from mcp_servers.mdq.mdq_models import ParsedSection
from mcp_servers.mdq.mdq_service import MdqService

_SECTION: ParsedSection = {
    "heading": "H1",
    "heading_level": 1,
    "heading_path": "H1",
    "content": "section body",
    "start_line": 2,
    "end_line": 2,
    "ordinal": 0,
    "parent_heading": None,
}


@pytest.fixture
def service(tmp_path: Path) -> MdqService:
    """MdqService on a tmp DB, tables created through the production DDL path."""
    db_path = tmp_path / "mdq.sqlite"
    svc = MdqService(db_path=str(db_path))
    conn = sqlite3.connect(db_path)
    try:
        create_production_tables(conn, str(db_path), sqlite_busy_timeout=5000)
    finally:
        conn.close()
    return svc


def _write_doc(service: MdqService, tmp_path: Path) -> Path:
    """Insert one document + chunk through the production write path."""
    path = tmp_path / "doc.md"
    path.write_text("# H1\nsection body\n", encoding="utf-8")
    conn = service._get_db_connection()
    try:
        write_document_chunks(conn, service, path, [dict(_SECTION)], "[]")
        conn.commit()
    finally:
        conn.close()
    return path


class TestMdqForeignKeys:
    def test_cascade_delete_removes_chunks(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """Raw documents DELETE cascades to chunks on a production connection."""
        path = _write_doc(service, tmp_path)
        doc_id = sha256(str(path).encode()).hexdigest()
        conn = service._get_db_connection()
        try:
            conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
            conn.commit()
            remaining = conn.execute(
                "SELECT COUNT(*) FROM chunks WHERE doc_id = ?", (doc_id,)
            ).fetchone()[0]
        finally:
            conn.close()
        assert remaining == 0

    def test_connection_pragma_foreign_keys_on(self, service: MdqService) -> None:
        """PRAGMA foreign_keys is 1 on service and DDL-path connections."""
        conn = service._get_db_connection()
        try:
            assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        finally:
            conn.close()
        ddl_conn = sqlite3.connect(service.db_path)
        try:
            create_production_tables(
                ddl_conn, service.db_path, sqlite_busy_timeout=5000
            )
            assert ddl_conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        finally:
            ddl_conn.close()

    def test_orphan_chunk_insert_rejected(self, service: MdqService) -> None:
        """A chunk row referencing a nonexistent doc_id cannot be inserted."""
        conn = service._get_db_connection()
        try:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO chunks (chunk_id, doc_id, source_path, heading, content, "
                    "start_line, end_line, content_hash, indexed_at) "
                    "VALUES ('orphan-chunk', 'no-such-doc', 'x.md', 'h', 'body', 1, 1, 'h', 0.0)",
                )
        finally:
            conn.close()
