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
        """Rebuild the FTS5 full-text search index from chunks."""
        with SQLiteHelper("rag").open() as db:
            db.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")

    def vacuum(self) -> None:
        """VACUUM the RAG database to reclaim space."""
        with SQLiteHelper("rag").open() as db:
            db.execute("VACUUM")
