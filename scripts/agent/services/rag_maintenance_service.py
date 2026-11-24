"""scripts/agent/services/rag_maintenance_service.py

RagMaintenanceService — maintenance operations on rag.sqlite only.
Operates exclusively on rag.sqlite.
"""

from __future__ import annotations

import sqlite3
import threading

from db.config import DbConfig
from db.helper import SQLiteHelper
from db.rag_consistency import (
    check_rag_consistency,
    is_consistent,
    summarize_issues,
)
from db.recovery import recover_corruption
from shared.db_maintenance import count_table

from agent.services.models import (
    DbRecoverResult,
    RagConsistencyResult,
    RagFtsRebuildResult,
)


class RagMaintenanceService:
    """Maintenance operations scoped exclusively to rag.sqlite."""

    def __init__(self, db_config: DbConfig) -> None:
        """Accepts the typed configuration supplied by the process that owns the file.

        `db_config` is the resolved `DbConfig`; this service reads no configuration
        file and resolves no path itself.
        """
        self._db_config = db_config

    def stats_rag(self) -> tuple[int, int]:
        """Return (docs, chunks) counts from rag.sqlite."""
        with SQLiteHelper("rag", db_config=self._db_config).open(
            row_factory=True
        ) as db:
            docs = count_table(db, "documents")
            chunks = count_table(db, "chunks")
        return docs, chunks

    def rebuild_fts(
        self, *, stop: threading.Event | None = None
    ) -> RagFtsRebuildResult:
        """Rebuild the FTS5 chunks_fts index using COALESCE(normalized_content, content).

        The FTS5 built-in 'rebuild' reads chunks.content directly, missing
        normalized_content for Japanese chunks.  This explicit delete-all +
        re-insert preserves the same rule as the chunks_ai trigger.

        `stop` is the job's cancellation event, passed to the connection's progress
        handler (REQ-002). The postcondition re-counts the index against `chunks` after
        the commit, so the result reports what the index holds, not what the run attempted
        to insert (REQ-004). A stopped run reports the state it was in, never a count it
        did not measure.
        """
        with SQLiteHelper("rag", db_config=self._db_config).open(
            write_mode=True, row_factory=True
        ) as db:
            if stop is not None:
                db.interrupt_when(stop)
            try:
                db.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('delete-all')")
                cursor = db.execute(
                    "INSERT INTO chunks_fts(rowid, content)"
                    " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
                )
                inserted = cursor.rowcount
                db.commit()
            except sqlite3.OperationalError:
                if stop is None or not stop.is_set():
                    raise
                return RagFtsRebuildResult(interrupted=True)
            chunks = count_table(db, "chunks")
            # `chunks_fts` is an external-content table, so its own count reflects the
            # `chunks` rows. The index rows are the ones the postcondition must measure,
            # which is why the count is read from chunks_fts_docsize, as the consistency
            # check reads it (`scripts/db/rag_consistency_queries.py:24`).
            fts_rows = db.execute("SELECT COUNT(*) FROM chunks_fts_docsize").fetchone()[
                0
            ]
        return RagFtsRebuildResult(
            rows_inserted=inserted,
            chunks=chunks,
            fts_rows=fts_rows,
            verified=fts_rows == chunks,
        )

    def consistency(
        self, *, stop: threading.Event | None = None
    ) -> RagConsistencyResult:
        """Run RAG consistency check on rag.sqlite; return (is_consistent, issue_strings).

        stop: when set, aborts the running statements via the connection progress
            handler; aborted stages are recorded by the check as diagnostics.
        """
        with SQLiteHelper("rag", db_config=self._db_config).open() as db:
            if stop is not None:
                db.interrupt_when(stop)
            report = check_rag_consistency(db)
        return RagConsistencyResult(
            is_consistent=is_consistent(report),
            issues=summarize_issues(report),
            report=report,
            findings=report.findings,
            fatal_count=report.fatal_count,
            degraded_count=report.degraded_count,
        )

    def recover(self, backup_path: str | None) -> DbRecoverResult:
        """Run integrity check; restore from backup_path if corruption found."""
        result = recover_corruption(self._db_config, backup_path)
        return DbRecoverResult(
            # VACUUM runs only after the integrity check passed, so its failure is
            # not corruption.
            integrity_ok=result.success or result.action == "vacuum_failed",
            recovered=result.action == "restored",
            detail=result.detail or "",
            logical_ok=result.logical_ok,
        )

    def rebuild_vec(self, *, stop: threading.Event | None = None) -> int:
        """Remove chunks_vec rows that have no chunks row.

        Returns the number of chunks_vec rows left. Vector rows cannot be regenerated
        from chunks: the embeddings live only in chunks_vec.

        `stop` is the job's cancellation event, passed to the connection's progress
        handler (REQ-002).
        """
        with SQLiteHelper("rag", db_config=self._db_config).open(write_mode=True) as db:
            if stop is not None:
                db.interrupt_when(stop)
            orphans = db.execute(
                "SELECT chunk_id FROM chunks_vec"
                " WHERE chunk_id NOT IN (SELECT chunk_id FROM chunks)"
            ).fetchall()
            db.executemany(
                "DELETE FROM chunks_vec WHERE chunk_id = ?",
                [(row[0],) for row in orphans],
            )
            remaining: int = db.execute("SELECT COUNT(*) FROM chunks_vec").fetchone()[0]
            db.commit()
            return remaining

    def reconcile_url(self, url: str) -> dict[str, bool | int]:
        """Insert the missing chunks_fts entries of the chunks of one URL.

        An FTS5 'delete' of an entry that is not indexed corrupts the index, so only
        chunks absent from chunks_fts_docsize are inserted; indexed entries and
        chunks_vec are left alone.
        """
        with SQLiteHelper("rag", db_config=self._db_config).open(
            write_mode=True, row_factory=True
        ) as db:
            doc = db.execute(
                "SELECT doc_id FROM documents WHERE url = ?", (url,)
            ).fetchone()
            if doc is None:
                return {"found": False}
            doc_id = doc["doc_id"]
            db.execute(
                "INSERT INTO chunks_fts(rowid, content)"
                " SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks"
                " WHERE doc_id = ?"
                " AND chunk_id NOT IN (SELECT id FROM chunks_fts_docsize)",
                (doc_id,),
            )
            chunk_count: int = db.execute(
                "SELECT COUNT(*) FROM chunks WHERE doc_id = ?", (doc_id,)
            ).fetchone()[0]
            db.commit()
            return {"found": True, "chunks": chunk_count}
