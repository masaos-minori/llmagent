"""scripts/rag/ingestion/document_manager.py

Document management for RagIngester."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable

from db.helper import SQLiteHelper
from db.models import RagConsistencyReport
from db.rag_consistency import check_rag_consistency, is_consistent
from rag.ingestion.etag_manager import ETagManager
from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/ingest.log")


def delete_document_chain(db: SQLiteHelper, doc_id: int) -> None:
    """Delete chunks_vec, then documents; ON DELETE CASCADE removes chunks.

    chunks_vec has no FK to chunks (sqlite-vec limitation), so it is deleted
    explicitly first. Deleting documents cascades to chunks (requires the
    write-mode connection's PRAGMA foreign_keys=ON), which in turn fires the
    chunks_ad (FTS5 sync) and chunks_vec_ad (defensive vec cleanup) triggers
    automatically. chunks_vec_ad is a backstop for direct chunks deletes that
    bypass this helper -- it is not the primary mechanism here.
    """
    # 1. delete chunks_vec rows for this doc's chunks (no FK, must be explicit)
    db.execute(
        "DELETE FROM chunks_vec WHERE chunk_id IN (SELECT chunk_id FROM chunks WHERE doc_id = ?)",
        (doc_id,),
    )
    # 2. delete documents row (CASCADE removes chunks automatically)
    db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))


class DocumentManager:
    """Manages document lifecycle for RagIngester.

    Handles existing document detection, ETag updates, and consistency reports.
    """

    def __init__(self, db: SQLiteHelper) -> None:
        """Initialize with a database helper instance."""
        self._db = db

    def handle_existing_document(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str,
        is_file_url: Callable[[str], bool],
    ) -> tuple[int, bool, bool]:
        """Handle an existing document case.

        Returns:
            Tuple of (existing_doc_id, skip_flag, replace_chunks_flag)
            - When force=True: (existing_doc_id, False, True) — caller should delete then proceed
            - When force=False and file unchanged: (existing_doc_id, True, False) — skip
            - When force=False and file changed: (existing_doc_id, False, True) — caller should delete then proceed
        """
        if force:
            return existing_doc_id, False, True
        if is_file_url(url):
            stored = self._db.execute(
                "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
                (existing_doc_id,),
            ).fetchone()
            if stored is None:
                return existing_doc_id, False, False
            if self._is_file_unchanged(
                stored["etag"], stored["last_modified"], etag, last_modified
            ):
                logger.info(
                    "file:// unchanged (sha256 match): %s",
                    url,
                    extra={"stage_name": "ingester"},
                )
                return existing_doc_id, True, False
            logger.info(
                "file:// changed — auto re-ingesting: %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return existing_doc_id, False, True

        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return existing_doc_id, False, False

        if stored["etag"] == etag and stored["last_modified"] == last_modified:
            return existing_doc_id, True, False

        self._update_etag(existing_doc_id, etag, last_modified, fetched_at)
        return existing_doc_id, False, True

    def _update_etag(
        self,
        doc_id: int,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document (skip-case)."""
        ETagManager(self._db, doc_id).update(etag, last_modified, new_fetched_at)

    @staticmethod
    def _is_file_unchanged(
        existing_etag: str | None,
        existing_last_modified: str | None,
        new_etag: str | None,
        new_last_modified: str | None,
    ) -> bool:
        """Return True when the file SHA-256 hash is unchanged."""
        if existing_etag is None or new_etag is None:
            return False
        return existing_etag == new_etag

    def delete_existing_document(self, doc_id: int) -> None:
        """Delete a document and its chunks_vec rows; documents delete cascades to chunks."""
        delete_document_chain(self._db, doc_id)

    def check_consistency(
        self, embed_failed: int, on_ingest_complete: Callable[[], None] | None = None
    ) -> RagConsistencyReport | None:
        """Run post-ingestion consistency check and callback."""
        try:
            report = check_rag_consistency(self._db, embed_failed=embed_failed)
        except (sqlite3.OperationalError, sqlite3.DatabaseError, ValueError):
            logger.exception("Post-ingest consistency check failed")
            return None
        self._log_consistency_issues(report)
        self._invoke_callback(on_ingest_complete)
        return report

    def _log_consistency_issues(self, report: RagConsistencyReport) -> None:
        """Log each issue when the report indicates inconsistency."""
        if not is_consistent(report):
            for issue in report.issues:
                logger.warning(
                    "Post-ingest consistency: %s",
                    issue,
                    extra={"stage_name": "ingester"},
                )

    @staticmethod
    def _invoke_callback(callback: Callable[[], None] | None) -> None:
        """Invoke the callback, logging any exception without re-raising."""
        if callback is not None:
            try:
                callback()
            except (TypeError, ValueError):
                logger.exception("on_ingest_complete callback failed")
