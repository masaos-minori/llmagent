"""ETag manager for document freshness tracking."""

from __future__ import annotations

from shared.logger import Logger
from db.helper import SQLiteHelper

logger = Logger(__name__, "/opt/llm/logs/ingest.log")


class ETagManager:
    """Manages ETag/Last-Modified updates for existing documents."""

    def __init__(self, db: SQLiteHelper, doc_id: int) -> None:
        self._db = db
        self._doc_id = doc_id

    def update(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str | None = None,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if etag is None and last_modified is None:
            return
        if self._is_stale_update(new_fetched_at):
            logger.info(
                "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
                new_fetched_at,
                self._doc_id,
                extra={"stage_name": "ingester"},
            )
            return
        if new_fetched_at is not None:
            self._update_with_freshness(etag, last_modified, new_fetched_at)
        else:
            self._update_null_fill(etag, last_modified)
        self._log_updated()

    def _is_stale_update(self, new_fetched_at: str | None) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if new_fetched_at is None:
            return False
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        return bool(stored_fetched_at and new_fetched_at < stored_fetched_at)

    def _update_with_freshness(
        self,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str,
    ) -> None:
        """Overwrite ETag/Last-Modified when freshness is proven."""
        self._db.execute(
            "UPDATE documents SET etag = ?, last_modified = ?,"
            " fetched_at = COALESCE(?, fetched_at) WHERE doc_id = ?",
            (etag, last_modified, fetched_at, self._doc_id),
        )
        self._db.commit()

    def _update_null_fill(
        self, etag: str | None, last_modified: str | None
    ) -> None:
        """Fill NULL only; never overwrite existing values."""
        self._db.execute(
            "UPDATE documents SET etag = COALESCE(etag, ?), last_modified = COALESCE(last_modified, ?)"
            " WHERE doc_id = ?",
            (etag, last_modified, self._doc_id),
        )
        self._db.commit()

    def _log_updated(self) -> None:
        """Log the etag update."""
        logger.info(
            "skip-path etag updated for doc_id=%d",
            self._doc_id,
            extra={"stage_name": "ingester"},
        )
