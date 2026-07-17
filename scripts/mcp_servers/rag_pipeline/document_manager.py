#!/usr/bin/env python3
"""mcp_servers/rag_pipeline/document_manager.py

Document management for rag_pipeline MCP service.

Dependency direction: mcp_servers.rag_pipeline.document_manager → db.helper, shared.types
Import from here:  from mcp_servers.rag_pipeline.document_manager import DocumentManager
"""

from __future__ import annotations

from db.helper import SQLiteHelper

from mcp_servers.rag_pipeline.models import (
    DocumentItem,
)


class DocumentManager:
    """Manages document CRUD operations for rag_pipeline MCP service."""

    def __init__(self, rag_db_path: str = "") -> None:
        self._rag_db_path = rag_db_path

    def _make_helper(self) -> SQLiteHelper:
        if self._rag_db_path:
            return SQLiteHelper(db_path=self._rag_db_path)
        return SQLiteHelper("rag")

    def list_documents(
        self, lang: str | None = None, limit: int = 20
    ) -> list[DocumentItem]:
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
        return [
            {
                "url": r["url"],
                "title": r["title"],
                "lang": r["lang"],
                "fetched_at": r["fetched_at"],
                "chunking_strategy": r["chunking_strategy"],
                "chunk_count": r["n"],
            }
            for r in rows
        ]

    def delete_document(self, url: str) -> bool:
        with self._make_helper().open(write_mode=True) as db:
            row = db.execute(
                "SELECT doc_id FROM documents WHERE url = ?", (url,)
            ).fetchone()
            if row is None:
                return False
            doc_id = row[0]
            db.execute(
                "DELETE FROM chunks_vec WHERE chunk_id IN (SELECT chunk_id FROM chunks WHERE doc_id = ?)",
                (doc_id,),
            )
            db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
            db.commit()
        return True
