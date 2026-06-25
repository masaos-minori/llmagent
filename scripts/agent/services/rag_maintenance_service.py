"""agent/services/rag_maintenance_service.py
RagMaintenanceService — maintenance operations on rag.sqlite only.
Operates exclusively on rag.sqlite.
"""

from __future__ import annotations

from typing import Any

from db.helper import SQLiteHelper
from db.maintenance import (
    check_rag_consistency,
    is_consistent,
    recover_corruption,
    summarize_issues,
)

from agent.services.models import DbRecoverResult, RagConsistencyResult


class RagMaintenanceService:
    """Maintenance operations scoped exclusively to rag.sqlite."""

    def stats_rag(self) -> tuple[int, int]:
        """Return (docs, chunks) counts from rag.sqlite."""
        with SQLiteHelper("rag").open(row_factory=True) as db:
            docs = self._count_table(db, "documents")
            chunks = self._count_table(db, "chunks")
        return docs, chunks

    @staticmethod
    def _count_table(db: Any, table: str) -> int:
        return int(db.fetchall(f"SELECT COUNT(*) AS n FROM {table}")[0]["n"])  # nosec B608 — table is always a hardcoded name, never user input

    def rebuild_fts(self) -> None:
        """Rebuild the FTS5 chunks_fts index in rag.sqlite."""
        with SQLiteHelper("rag").open(write_mode=True) as db:
            db.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
            db.commit()

    def consistency(self) -> RagConsistencyResult:
        """Run RAG consistency check on rag.sqlite; return (is_consistent, issue_strings)."""
        with SQLiteHelper("rag").open() as db:
            report = check_rag_consistency(db)
        return RagConsistencyResult(
            is_consistent=is_consistent(report),
            issues=summarize_issues(report),
            report=report,
        )

    def recover(self, backup_path: str | None) -> DbRecoverResult:
        """Run integrity check; restore from backup_path if corruption found."""
        result = recover_corruption(backup_path)
        return DbRecoverResult(
            integrity_ok=result.success,
            recovered=result.action == "restored",
            detail=result.detail or "",
        )

    def rebuild_vec(self) -> int:
        """Rebuild chunks_vec from chunks. Returns number of rows inserted."""
        with SQLiteHelper("rag").open(write_mode=True) as db:
            db.execute("DELETE FROM chunks_vec")
            rows = db.execute(
                "SELECT chunk_id, embedding FROM chunks WHERE embedding IS NOT NULL"
            ).fetchall()
            for row in rows:
                db.execute(
                    "INSERT INTO chunks_vec(chunk_id, embedding) VALUES(?, ?)",
                    (row["chunk_id"], row["embedding"]),
                )
            return len(rows)

    def reconcile_url(self, url: str) -> dict[str, bool | int]:
        """Rebuild FTS/vec for a single URL."""
        with SQLiteHelper("rag").open(write_mode=True) as db:
            doc = db.execute(
                "SELECT doc_id FROM documents WHERE url = ?", (url,)
            ).fetchone()
            if doc is None:
                return {"found": False}
            doc_id = doc["doc_id"]
            chunk_ids = [
                r["chunk_id"]
                for r in db.execute(
                    "SELECT chunk_id FROM chunks WHERE doc_id = ?", (doc_id,)
                ).fetchall()
            ]
            for cid in chunk_ids:
                db.execute("DELETE FROM chunks_vec WHERE chunk_id = ?", (cid,))
            if chunk_ids:
                placeholders = ",".join("?" * len(chunk_ids))
                db.execute(
                    f"DELETE FROM chunks_fts WHERE chunk_id IN ({placeholders})",
                    tuple(chunk_ids),
                )
            for cid in chunk_ids:
                row = db.execute(
                    "SELECT content, embedding FROM chunks WHERE chunk_id = ?", (cid,)
                ).fetchone()
                if row:
                    db.execute(
                        "INSERT INTO chunks_fts(chunk_id, content) VALUES(?, ?)",
                        (cid, row["content"]),
                    )
                    if row["embedding"]:
                        db.execute(
                            "INSERT INTO chunks_vec(chunk_id, embedding) VALUES(?, ?)",
                            (cid, row["embedding"]),
                        )
            return {"found": True, "chunks": len(chunk_ids)}
