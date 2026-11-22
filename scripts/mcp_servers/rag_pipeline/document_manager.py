#!/usr/bin/env python3
"""scripts/mcp_servers/rag_pipeline/document_manager.py

Document management for rag_pipeline MCP service.

Dependency direction: mcp_servers.rag_pipeline.document_manager → db.helper, rag.ingestion.document_manager, shared.types
Import from here:  from mcp_servers.rag_pipeline.document_manager import DocumentManager
"""

from __future__ import annotations

import sqlite3

from db.config import DbConfig
from db.helper import SQLiteHelper
from rag.ingestion.document_manager import delete_document_chain

from mcp_servers.rag_pipeline.rag_pipeline_models import (
    DocumentItem,
)


class DocumentManager:
    """Manages document CRUD operations for rag_pipeline MCP service."""

    def __init__(
        self,
        rag_db_path: str = "",
        *,
        db_config: DbConfig | None = None,
    ) -> None:
        """Initialize with optional database path override.

        The RAG Pipeline MCP owns its own configuration file and only its own
        database, so the path and the connection settings it supplies are used
        directly; a full `DbConfig` (which requires the Session and Workflow
        paths) belongs to the process that owns all three. When neither is given
        this class resolves no configuration file and raises.
        """
        self._db_config = db_config
        self._rag_db_path = rag_db_path

    def _make_helper(self) -> SQLiteHelper:
        """Create a SQLiteHelper from the supplied path or the supplied typed config.

        This class reads no configuration file: with no path and no typed config
        there is nothing to resolve, so it raises.
        """
        if self._rag_db_path:
            return SQLiteHelper(db_path=self._rag_db_path)
        if self._db_config is None:
            raise ValueError(
                "rag_db_path is not configured: supply an explicit path or the typed "
                "configuration; this class reads no configuration file"
            )
        return SQLiteHelper("rag", db_config=self._db_config)

    def list_documents(
        self, lang: str | None = None, limit: int = 20
    ) -> list[DocumentItem]:
        """Return a paginated list of indexed documents, optionally filtered by language."""
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
        with self._make_helper().open(row_factory=True) as db:
            rows = db.fetchall(sql, tuple(params))
        return [self._to_document_item(row) for row in rows]

    @staticmethod
    def _to_document_item(row: sqlite3.Row) -> DocumentItem:
        """Convert one documents+chunks aggregate row into a DocumentItem."""
        return {
            "url": row["url"],
            "title": row["title"],
            "lang": row["lang"],
            "fetched_at": row["fetched_at"],
            "chunking_strategy": row["chunking_strategy"],
            "chunk_count": row["n"],
        }

    def delete_document(self, url: str) -> bool:
        """Delete a document and its associated chunks by URL; returns True if deleted, False if not found."""
        with self._make_helper().open(write_mode=True) as db:
            row = db.execute(
                "SELECT doc_id FROM documents WHERE url = ?", (url,)
            ).fetchone()
            if row is None:
                return False
            doc_id = row[0]
            delete_document_chain(db, doc_id)
            db.commit()
        return True
