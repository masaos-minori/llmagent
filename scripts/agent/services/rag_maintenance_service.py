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
