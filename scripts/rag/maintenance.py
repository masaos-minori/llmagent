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
        normalized_content for Japanese chunks.  This explicit delete-all +
        re-insert preserves the same rule as the chunks_ai trigger.
        """
        with SQLiteHelper("rag").open() as db:
            db.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('delete-all')")
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
            )

    def vacuum(self) -> None:
        """VACUUM the RAG database to reclaim space."""
        with SQLiteHelper("rag").open() as db:
            db.execute("VACUUM")
