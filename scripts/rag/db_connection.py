"""scripts/rag/db_connection.py

Extracted from scripts/rag/pipeline.py — augment() DB connection management.

Provides RagDatabaseConnection context manager wrapping the SQLiteHelper
open/close lifecycle currently inline in augment(), reducing pipeline.py
complexity and isolating database connection handling.
"""

import logging
import sqlite3

from db.helper import SQLiteHelper

logger = logging.getLogger(__name__)


class RagDatabaseConnection:
    """Context manager for RAG pipeline database connections.

    Wraps SQLiteHelper(...).open(row_factory=True) construction and ensures
    deterministic resource cleanup via __enter__/__exit__.
    """

    def __init__(
        self,
        rag_db_path: str | None = None,
        sqlite_vec_so: str = "/opt/llm/sqlite-vec/vec0.so",
        sqlite_timeout: int = 5,
        sqlite_busy_timeout_ms: int = 5000,
    ) -> None:
        self._rag_db_path = rag_db_path
        self._sqlite_vec_so = sqlite_vec_so
        self._sqlite_timeout = sqlite_timeout
        self._sqlite_busy_timeout_ms = sqlite_busy_timeout_ms
        self._db: SQLiteHelper | None = None

    def __enter__(self) -> SQLiteHelper:
        """Open the database connection."""
        try:
            if self._rag_db_path:
                self._db = SQLiteHelper(
                    db_path=self._rag_db_path,
                    sqlite_vec_so=self._sqlite_vec_so,
                    sqlite_timeout=self._sqlite_timeout,
                    sqlite_busy_timeout_ms=self._sqlite_busy_timeout_ms,
                ).open(row_factory=True)
            else:
                self._db = SQLiteHelper().open(row_factory=True)
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
            raise RuntimeError(f"DB open failed (RAG unavailable): {e}") from e
        return self._db

    def __exit__(
        self,
        exc_type: object,
        exc_val: object,
        exc_tb: object,
    ) -> None:
        """Close the database connection."""
        if self._db is not None:
            self._db.close()
            self._db = None
