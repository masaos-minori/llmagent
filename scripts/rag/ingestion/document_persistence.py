#!/usr/bin/env python3
"""scripts/rag/ingestion/document_persistence.py

Isolate document CRUD operations from ingester.py into DocumentStore class.

DocumentStore owns the lang validation and document row insertion logic —
these are persistence concerns.
"""

import sqlite3

from db.helper import SQLiteHelper
from rag.ingestion.document_manager import DocumentManager

# Accepted lang values enforced by the documents.lang CHECK constraint
_VALID_LANGS: frozenset[str] = frozenset({"en", "ja"})


class DocumentStore:
    """Manage document rows in SQLite: create, lookup, and replace."""

    def __init__(
        self,
        db: SQLiteHelper,
        doc_mgr: DocumentManager,
    ) -> None:
        """Initialize with DocumentManager and DB settings."""
        self._db = db
        self._doc_mgr = doc_mgr

    def validate_lang(self, lang: str) -> bool:
        """Return True when lang is a valid value."""
        return lang in _VALID_LANGS

    def get_or_create(
        self,
        db: SQLiteHelper,
        url: str,
        title: str,
        lang: str,
        force: bool,
        *,
        etag: str | None = None,
        last_modified: str | None = None,
        chunking_strategy: str = "text",
        fetched_at: str,
    ) -> tuple[int | None, bool, bool]:
        """Register a URL in documents and return its doc_id and whether replacement is needed.
        Returns (None, True) if already registered and skip=True.
        """
        if not self.validate_lang(lang):
            raise ValueError(
                f"unsupported lang value: {lang!r} (must be one of {sorted(_VALID_LANGS)})",
            )
        existing_row = db.execute(
            "SELECT doc_id FROM documents WHERE url = ?",
            (url,),
        ).fetchone()
        if existing_row:
            existing_doc_id: int = existing_row[0]
            doc_id, skip, replace = self._doc_mgr.handle_existing_document(
                url,
                existing_doc_id,
                force,
                etag,
                last_modified,
                fetched_at,
                lambda u: u.startswith("file://"),
            )
            if skip:
                return None, True, False
            if replace:
                return existing_doc_id, False, True
            return existing_doc_id, False, False
        return None, False, False

    def insert(
        self,
        db: SQLiteHelper,
        url: str,
        title: str,
        lang: str,
        etag: str | None,
        last_modified: str | None,
        chunking_strategy: str,
        fetched_at: str,
    ) -> sqlite3.Cursor:
        """Insert a document row and return the cursor."""
        cursor: sqlite3.Cursor = db.execute(
            "INSERT INTO documents"
            " (url, title, lang, etag, last_modified, chunking_strategy, fetched_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (url, title, lang, etag, last_modified, chunking_strategy, fetched_at),
        )
        return cursor
