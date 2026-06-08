#!/usr/bin/env python3
"""agent/document_repo.py
Document persistence repository.
"""

import logging
from typing import Any

from db.helper import SQLiteHelper

logger = logging.getLogger(__name__)


class DocumentRepository:
    """Repository for document operations."""

    def __init__(self) -> None:
        pass

    def list_documents(self, lang: str | None = None, limit: int = 20) -> list[dict]:
        """Return registered documents as structured data.

        lang: filter by language ('ja' or 'en'); None means all.
        limit: maximum number of rows to return (default: 20).
        Each dict: url, title, lang, fetched_at, chunk_count.
        Returns [] on error or when no documents exist.
        """
        sql = (
            "SELECT d.url, d.title, d.lang, d.fetched_at,"
            " COUNT(c.chunk_id) AS n"
            " FROM documents d"
            " LEFT JOIN chunks c USING(doc_id)"
        )
        params: list[Any] = []
        if lang:
            sql += " WHERE d.lang = ?"
            params.append(lang)
        sql += " GROUP BY d.doc_id ORDER BY d.fetched_at DESC LIMIT ?"
        params.append(limit)
        try:
            with SQLiteHelper("session").open(row_factory=True) as db:
                rows = db.fetchall(sql, tuple(params))
        except Exception as e:
            logger.warning(f"list_documents failed: {e}")
            return []
        return [
            {
                "url": r["url"],
                "title": r["title"],
                "lang": r["lang"],
                "fetched_at": r["fetched_at"],
                "chunk_count": r["n"],
            }
            for r in rows
        ]

    def delete_document(self, url: str) -> bool:
        """Delete a document and its chunks from DB by URL.

        Removes chunks_vec first (no FK to chunks), then deletes the document
        record which cascades to chunks and chunks_fts via ON DELETE CASCADE.
        Returns True when found and deleted, False when not found.
        """
        try:
            with SQLiteHelper("session").open(write_mode=True) as db:
                row = db.execute(
                    "SELECT doc_id FROM documents WHERE url = ?",
                    (url,),
                ).fetchone()
                if row is None:
                    return False
                doc_id = row[0]
                db.execute(
                    "DELETE FROM chunks_vec"
                    " WHERE chunk_id IN"
                    " (SELECT chunk_id FROM chunks WHERE doc_id = ?)",
                    (doc_id,),
                )
                db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
                db.commit()
            logger.info(f"Document deleted: url={url!r} doc_id={doc_id}")
            return True
        except Exception as e:
            logger.warning(f"delete_document failed (url={url!r}): {e}")
            return False
