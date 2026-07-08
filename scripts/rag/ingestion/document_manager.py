"""Document management for RagIngester."""

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
    """Delete chunks_vec → chunks → documents for doc_id.

    chunks_vec has no FK to chunks, so it must be deleted first.
    chunks deletion fires FTS5 triggers automatically (via ON DELETE trigger on chunks).
    documents deletion cascades to any remaining chunks rows.
    """
    db.execute(
        "DELETE FROM chunks_vec"
        " WHERE chunk_id IN (SELECT chunk_id FROM chunks WHERE doc_id = ?)",
        (doc_id,),
    )
    db.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
    db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))


class DocumentManager:
    """Manages document lifecycle for RagIngester.

    Handles existing document detection, ETag updates, and consistency reports.
    """

    def __init__(self, db: SQLiteHelper) -> None:
        self._db = db

    def handle_existing_document(
        self,
        url: str,
        existing_doc_id: int,
        force: bool,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str | None,
        is_file_url: Callable[[str], bool],
    ) -> bool:
        """Handle an existing document; return True when the caller should skip insertion."""
        if force:
            return False
        if is_file_url(url):
            return self._handle_existing_file(url, existing_doc_id, etag, last_modified)
        self._update_etag(etag, last_modified, fetched_at)
        return True

    def _handle_existing_file(
        self,
        url: str,
        existing_doc_id: int,
        etag: str | None,
        last_modified: str | None,
    ) -> bool:
        """Handle an existing file:// document; return True when unchanged."""
        stored = self._db.execute(
            "SELECT etag, last_modified FROM documents WHERE doc_id = ?",
            (existing_doc_id,),
        ).fetchone()
        if stored is None:
            return False
        if self._is_file_unchanged(
            stored["etag"], stored["last_modified"], etag, last_modified
        ):
            logger.info(
                "file:// unchanged (sha256 match): %s",
                url,
                extra={"stage_name": "ingester"},
            )
            return True
        logger.info(
            "file:// changed — auto re-ingesting: %s",
            url,
            extra={"stage_name": "ingester"},
        )
        return False

    def _update_etag(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document (skip-case)."""
        ETagManager(self._db, 0).update(etag, last_modified, new_fetched_at)

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
        """Delete a document and its chunks; chunks_vec removed first because it has no FK constraint to chunks."""
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
