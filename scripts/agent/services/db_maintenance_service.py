"""agent/services/db_maintenance_service.py
DbMaintenanceService — wraps rag/session DB maintenance operations.

Extracted from cmd_db._DbMixin so the DB logic can be tested
independently of the REPL command layer.
"""

from __future__ import annotations

from typing import Any

from db.helper import SQLiteHelper
from db.maintenance import (
    RetentionConfig,
    checkpoint_wal,
    purge_old_sessions,
    recover_corruption,
    vacuum_db,
)

from agent.services.models import (
    DbCheckpointResult,
    DbHealth,
    DbPurgeResult,
    DbRecoverResult,
    DbStats,
)


class DbMaintenanceService:
    """Wraps all maintenance operations on rag.sqlite and session.sqlite."""

    def stats(self) -> DbStats:
        """Return document/chunk/session/message counts from both DBs."""
        with SQLiteHelper("rag").open(row_factory=True) as db:
            docs = self._count_table(db, "documents")
            chunks = self._count_table(db, "chunks")
        with SQLiteHelper("session").open(row_factory=True) as db:
            sessions = self._count_table(db, "sessions")
            messages = self._count_table(db, "messages")
        return DbStats(docs=docs, chunks=chunks, sessions=sessions, messages=messages)

    @staticmethod
    def _count_table(db: Any, table: str) -> int:
        """Return row count for a single table."""
        return int(db.fetchall(f"SELECT COUNT(*) AS n FROM {table}")[0]["n"])

    def rebuild_fts(self) -> None:
        """Rebuild the FTS5 chunks_fts index in rag.sqlite."""
        with SQLiteHelper("rag").open(write_mode=True) as db:
            db.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
            db.commit()

    def health(self) -> DbHealth:
        """Return DB health metrics from session.sqlite."""
        with SQLiteHelper("session").open() as db:
            raw = db.health_check()
        return DbHealth(
            integrity_ok=raw.integrity == "ok",
            wal_pages=0,
            size_bytes=raw.db_size_bytes,
        )

    def checkpoint(self, mode: str | None) -> DbCheckpointResult:
        """Run WAL checkpoint on session.sqlite."""
        with SQLiteHelper("session").open(write_mode=True) as db:
            raw = checkpoint_wal(db, mode)
        return DbCheckpointResult(
            mode=mode or "TRUNCATE",
            pages_written=raw.pages_checkpointed,
        )

    def vacuum(self) -> None:
        """Run VACUUM on session.sqlite."""
        with SQLiteHelper("session").open(write_mode=True) as db:
            vacuum_db(db)

    def purge(
        self, max_sessions: int | None, max_age_days: int | None
    ) -> DbPurgeResult:
        """Purge old sessions per retention config."""
        cfg = _build_retention_config(max_sessions, max_age_days)
        with SQLiteHelper("session").open(write_mode=True) as db:
            raw = purge_old_sessions(db, cfg)
        return DbPurgeResult(
            sessions_removed=raw.age_deleted + raw.count_deleted,
        )

    def recover(self, backup_path: str | None) -> DbRecoverResult:
        """Run integrity check; restore from backup_path if corruption found."""
        result = recover_corruption(backup_path)
        return DbRecoverResult(
            integrity_ok=result.success,
            recovered=result.action == "restored",
            detail=result.detail or "",
        )

    def list_documents(self, lang: str | None = None, limit: int = 20) -> list[dict]:
        """Return registered documents as structured data (delegates to rag.sqlite)."""
        sql = (
            "SELECT d.url, d.title, d.lang, d.fetched_at, d.chunking_strategy,"
            " COUNT(c.chunk_id) AS n"
            " FROM documents d"
            " LEFT JOIN chunks c USING(doc_id)"
        )
        params: list[str | int] = []
        if lang:
            sql += " WHERE d.lang = ?"
            params.append(lang)
        sql += " GROUP BY d.doc_id ORDER BY d.fetched_at DESC LIMIT ?"
        params.append(limit)
        with SQLiteHelper("rag").open(row_factory=True) as db:
            rows = db.fetchall(sql, tuple(params))
        return [
            {
                "url": r["url"],
                "title": r["title"],
                "lang": r["lang"],
                "fetched_at": r["fetched_at"],
                "chunking_strategy": r["chunking_strategy"],
                "chunk_count": r["n"],
            }
            for r in rows
        ]

    def delete_document(self, url: str) -> bool:
        """Delete a document and its chunks from DB by URL (delegates to rag.sqlite)."""
        with SQLiteHelper("rag").open(write_mode=True) as db:
            row = db.execute(
                "SELECT doc_id FROM documents WHERE url = ?", (url,)
            ).fetchone()
            if row is None:
                return False
            doc_id = row[0]
            db.execute(
                "DELETE FROM chunks_vec"
                " WHERE chunk_id IN"
                " (SELECT chunk_id FROM chunks WHERE doc_id = ?)",
                (doc_id,),
            )
            db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
            db.commit()
        return True


def _build_retention_config(
    max_sessions: int | None, max_age_days: int | None
) -> RetentionConfig | None:
    """Build a RetentionConfig from optional parameters."""
    kwargs: dict[str, int] = {}
    if max_sessions is not None:
        kwargs["max_sessions"] = max_sessions
    if max_age_days is not None:
        kwargs["max_age_days"] = max_age_days
    return RetentionConfig(**kwargs) if kwargs else None
