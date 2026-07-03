"""rag/maintenance.py — RAG-specific database maintenance operations."""

from __future__ import annotations

from db.helper import SQLiteHelper


class RagDbMaintenanceService:
    """Maintenance operations scoped to the RAG database."""

    def rotate(self) -> None:
        """Rotate the RAG database (copy + truncate + WAL checkpoint)."""
        with SQLiteHelper("rag").open() as db:
            db.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    def rebuild_fts(self) -> None:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  For content-mapped FTS5 tables,
        'delete-all' and 'DELETE FROM' do not work, so we drop and recreate the
        table to ensure COALESCE is applied.
        """
        with SQLiteHelper("rag").open() as db:
            # Drop triggers to prevent interference during rebuild
            db.execute("DROP TRIGGER IF EXISTS chunks_ai")
            db.execute("DROP TRIGGER IF EXISTS chunks_ad")
            db.execute("DROP TRIGGER IF EXISTS chunks_au")
            # Drop and recreate FTS table (without content=chunks mapping so we can insert)
            db.execute("DROP TABLE IF EXISTS chunks_fts")
            db.execute(
                "CREATE VIRTUAL TABLE chunks_fts USING fts5("
                "  content,"
                "  tokenize = 'unicode61'"
                ")"
            )
            # Repopulate FTS with COALESCE(normalized_content, content)
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )
            db.commit()
            # Recreate the insert trigger
            db.execute(
                "CREATE TRIGGER IF NOT EXISTS chunks_ai "
                "AFTER INSERT ON chunks BEGIN "
                "  INSERT INTO chunks_fts (rowid, content) "
                "  VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content)); "
                "END"
            )

    def vacuum(self) -> None:
        """VACUUM the RAG database to reclaim space."""
        with SQLiteHelper("rag").open() as db:
            db.execute("VACUUM")
