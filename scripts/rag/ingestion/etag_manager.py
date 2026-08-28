"""scripts/rag/ingestion/etag_manager.py

ETag manager for document freshness tracking."""

from __future__ import annotations

from datetime import UTC, datetime

from db.helper import SQLiteHelper
from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/ingest.log")


class ETagManager:
    """Manages ETag/Last-Modified updates for existing documents."""

    def __init__(self, db: SQLiteHelper, doc_id: int) -> None:
        """Initialize with database helper and document ID."""
        self._db = db
        self._doc_id = doc_id

    def update(
        self,
        etag: str | None,
        last_modified: str | None,
        new_fetched_at: str,
    ) -> None:
        """Refresh ETag/Last-Modified for an existing document.

        Guards against stale overwrites: if new_fetched_at < stored fetched_at,
        the incoming data is older and the existing DB values are kept.
        """
        if not new_fetched_at:
            raise ValueError("new_fetched_at must be a non-empty string")
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
        self._update_with_freshness(etag, last_modified, new_fetched_at)
        self._log_updated()

    def _is_stale_update(self, new_fetched_at: str) -> bool:
        """Return True when the incoming data is older than stored fetched_at."""
        if not new_fetched_at:
            return False

        # Parse incoming timestamp
        try:
            new_dt = datetime.fromisoformat(new_fetched_at.replace("Z", "+00:00"))
            if new_dt.tzinfo is None:
                new_dt = new_dt.replace(tzinfo=UTC)
        except ValueError:
            raise ValueError(f"Invalid incoming timestamp: {new_fetched_at}")

        # Fetch stored timestamp
        rows = self._db.fetchall(
            "SELECT fetched_at FROM documents WHERE doc_id = ?", (self._doc_id,)
        )
        stored_fetched_at = rows[0][0] if rows else None
        if not stored_fetched_at:
            return False

        # Parse stored timestamp
        try:
            stored_dt = datetime.fromisoformat(stored_fetched_at.replace("Z", "+00:00"))
            if stored_dt.tzinfo is None:
                stored_dt = stored_dt.replace(tzinfo=UTC)
        except ValueError:
            raise ValueError(f"Invalid stored timestamp: {stored_fetched_at}")

        return new_dt < stored_dt

    def _update_with_freshness(
        self,
        etag: str | None,
        last_modified: str | None,
        fetched_at: str,
    ) -> None:
        """Overwrite ETag/Last-Modified when freshness is proven."""
        self._db.execute(
            "UPDATE documents SET etag = ?, last_modified = ?, fetched_at = ? WHERE doc_id = ?",
            (etag, last_modified, fetched_at, self._doc_id),
        )

    def _log_updated(self) -> None:
        """Log the etag update."""
        logger.info(
            "skip-path etag updated for doc_id=%d",
            self._doc_id,
            extra={"stage_name": "ingester"},
        )
