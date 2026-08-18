"""tests/mcp_servers/mdq/test_index_delete.py
Characterization tests for scripts/mcp_servers/mdq/index_delete.py.

Locks current behavior of delete_file_from_index() before refactoring:
- chunks/documents rows are removed by doc_id = sha256(str(path)).hexdigest()
- chunks_fts stays in sync via the chunks_ad trigger (no manual FTS cleanup needed)
- index_state rows are removed via a `LIKE 'mtime:<path>%'` prefix match
- rows belonging to an unrelated doc_id / index_state key are left untouched
- the transaction is committed (visible from a second connection to the same file)
- calling with no matching rows at all is a no-op, not an error
- the `service` argument is accepted but not read by the function body (see the
  refactor report's Proposals section -- this is characterized as-is, not endorsed)
"""

from __future__ import annotations

import sqlite3
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING, cast

from mcp_servers.mdq.db_schema import create_production_tables
from mcp_servers.mdq.index_delete import delete_file_from_index

if TYPE_CHECKING:
    from mcp_servers.mdq.mdq_service import MdqService


def _doc_id(path: Path) -> str:
    return sha256(str(path).encode()).hexdigest()


def _make_conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    create_production_tables(conn, db_path, sqlite_busy_timeout=5000)
    return conn


def _insert_document(conn: sqlite3.Connection, doc_id: str, source_path: str) -> None:
    conn.execute(
        "INSERT INTO documents (doc_id, source_path, mtime_ns, size_bytes, "
        "content_hash, indexed_at) VALUES (?, ?, 0, 0, 'h', 0.0)",
        (doc_id, source_path),
    )


def _insert_chunk(
    conn: sqlite3.Connection, chunk_id: str, doc_id: str, source_path: str
) -> None:
    conn.execute(
        "INSERT INTO chunks (chunk_id, doc_id, source_path, heading, "
        "start_line, end_line, content, content_hash, indexed_at) VALUES "
        "(?, ?, ?, 'h', 1, 2, 'body', 'h', 0.0)",
        (chunk_id, doc_id, source_path),
    )


def _call(conn: sqlite3.Connection, path: Path) -> None:
    delete_file_from_index(cast("MdqService", None), conn, path)


class TestDeletesTargetRows:
    """Rows keyed to the deleted file's own doc_id/path are removed."""

    def test_deletes_matching_chunks(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "db.sqlite")
        conn = _make_conn(db_path)
        path = tmp_path / "a.md"
        doc_id = _doc_id(path)
        _insert_document(conn, doc_id, str(path))
        _insert_chunk(conn, "c1", doc_id, str(path))
        conn.commit()

        _call(conn, path)

        rows = conn.execute(
            "SELECT * FROM chunks WHERE doc_id = ?", (doc_id,)
        ).fetchall()
        assert rows == []

    def test_deletes_matching_document_row(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "db.sqlite")
        conn = _make_conn(db_path)
        path = tmp_path / "a.md"
        doc_id = _doc_id(path)
        _insert_document(conn, doc_id, str(path))
        conn.commit()

        _call(conn, path)

        rows = conn.execute(
            "SELECT * FROM documents WHERE doc_id = ?", (doc_id,)
        ).fetchall()
        assert rows == []

    def test_chunks_fts_is_cleaned_up_via_trigger(self, tmp_path: Path) -> None:
        """Comment in source claims the chunks_ad trigger handles FTS cleanup."""
        db_path = str(tmp_path / "db.sqlite")
        conn = _make_conn(db_path)
        path = tmp_path / "a.md"
        doc_id = _doc_id(path)
        _insert_document(conn, doc_id, str(path))
        _insert_chunk(conn, "c1", doc_id, str(path))
        conn.commit()

        _call(conn, path)

        rows = conn.execute(
            "SELECT * FROM chunks_fts WHERE content_hash = 'h'"
        ).fetchall()
        assert rows == []

    def test_deletes_index_state_row_for_exact_key(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "db.sqlite")
        conn = _make_conn(db_path)
        path = tmp_path / "a.md"
        conn.execute(
            "INSERT INTO index_state (key, value) VALUES (?, '123')",
            (f"mtime:{path}",),
        )
        conn.commit()

        _call(conn, path)

        rows = conn.execute("SELECT * FROM index_state").fetchall()
        assert rows == []

    def test_noop_when_nothing_matches(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "db.sqlite")
        conn = _make_conn(db_path)
        path = tmp_path / "never_indexed.md"

        _call(conn, path)  # must not raise

        assert conn.execute("SELECT * FROM documents").fetchall() == []


class TestLeavesUnrelatedRowsUntouched:
    """A delete for one file must not disturb another file's rows."""

    def test_leaves_unrelated_doc_id_chunks_and_document(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "db.sqlite")
        conn = _make_conn(db_path)
        deleted_path = tmp_path / "a.md"
        kept_path = tmp_path / "b.md"
        deleted_doc_id = _doc_id(deleted_path)
        kept_doc_id = _doc_id(kept_path)
        _insert_document(conn, deleted_doc_id, str(deleted_path))
        _insert_chunk(conn, "c1", deleted_doc_id, str(deleted_path))
        _insert_document(conn, kept_doc_id, str(kept_path))
        _insert_chunk(conn, "c2", kept_doc_id, str(kept_path))
        conn.commit()

        _call(conn, deleted_path)

        remaining_docs = conn.execute("SELECT doc_id FROM documents").fetchall()
        remaining_chunks = conn.execute("SELECT chunk_id FROM chunks").fetchall()
        assert remaining_docs == [(kept_doc_id,)]
        assert remaining_chunks == [("c2",)]

    def test_leaves_unrelated_index_state_key_untouched(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "db.sqlite")
        conn = _make_conn(db_path)
        deleted_path = tmp_path / "a.md"
        other_key = "mtime:/completely/different/file.md"
        conn.execute(
            "INSERT INTO index_state (key, value) VALUES (?, '1')",
            (f"mtime:{deleted_path}",),
        )
        conn.execute(
            "INSERT INTO index_state (key, value) VALUES (?, '2')", (other_key,)
        )
        conn.commit()

        _call(conn, deleted_path)

        remaining = conn.execute("SELECT key FROM index_state").fetchall()
        assert remaining == [(other_key,)]


class TestIndexStateWildcardMatchIsCharacterizedAsIs:
    """The index_state delete uses `LIKE 'mtime:<path>%'`, i.e. a trailing wildcard,
    not an exact-key match. This test locks that current behavior; it is not an
    endorsement -- see the refactor report's Proposals section for the associated
    over-match risk when one path's key string is a literal prefix of another's."""

    def test_trailing_wildcard_also_matches_a_longer_shared_prefix_key(
        self, tmp_path: Path
    ) -> None:
        db_path = str(tmp_path / "db.sqlite")
        conn = _make_conn(db_path)
        path = tmp_path / "a.md"
        longer_key = f"mtime:{path}.bak"
        conn.execute(
            "INSERT INTO index_state (key, value) VALUES (?, '1')",
            (f"mtime:{path}",),
        )
        conn.execute(
            "INSERT INTO index_state (key, value) VALUES (?, '2')", (longer_key,)
        )
        conn.commit()

        _call(conn, path)

        # Current behavior: the trailing '%' sweeps up the longer, distinct key too.
        assert conn.execute("SELECT * FROM index_state").fetchall() == []


class TestCommitsTheTransaction:
    def test_delete_is_visible_from_a_second_connection(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "db.sqlite")
        conn = _make_conn(db_path)
        path = tmp_path / "a.md"
        doc_id = _doc_id(path)
        _insert_document(conn, doc_id, str(path))
        conn.commit()

        _call(conn, path)

        second_conn = sqlite3.connect(db_path)
        try:
            rows = second_conn.execute(
                "SELECT * FROM documents WHERE doc_id = ?", (doc_id,)
            ).fetchall()
            assert rows == []
        finally:
            second_conn.close()


class TestServiceArgumentIsAcceptedButUnused:
    def test_none_service_does_not_raise(self, tmp_path: Path) -> None:
        """`service` is not read by the function body (confirmed via vulture,
        100% confidence unused-variable). Characterizes the current signature;
        do not read this as license to silently drop the parameter."""
        db_path = str(tmp_path / "db.sqlite")
        conn = _make_conn(db_path)
        path = tmp_path / "a.md"

        _call(conn, path)  # cast(None) for `service` -- must not raise
