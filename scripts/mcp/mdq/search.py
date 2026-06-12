#!/usr/bin/env python3
"""mcp/mdq/search.py
Search functionality using FTS5.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from rag.models import SearchDocsResult

from mcp.mdq.models import SearchDocsRequest

if TYPE_CHECKING:
    from mcp.mdq.service import MdqService

logger = logging.getLogger(__name__)


async def search_docs(service: MdqService, req: SearchDocsRequest) -> str:
    """Search indexed Markdown sections by query; returns formatted results."""
    result = _search_docs_structured(service, req)
    if not result.results:
        return f"No results found for: {req.query!r}"
    lines = [f"Search results for: {req.query!r} ({result.total} found)"]
    for i, r in enumerate(result.results, 1):
        lines.append(f"{i}. {r}")
    return "\n".join(lines)


def _search_docs_structured(
    service: MdqService, req: SearchDocsRequest
) -> SearchDocsResult:
    """Run FTS5 search; return SearchDocsResult DTO."""
    if not req.query or not req.query.strip():
        return SearchDocsResult(query=req.query, results=[], total=0)
    try:
        import sqlite3  # noqa: PLC0415

        conn = sqlite3.connect(service.db_path)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT content FROM sections_fts WHERE sections_fts MATCH ? LIMIT ?",
                (req.query, getattr(req, "limit", 10)),
            ).fetchall()
            results = [str(r["content"]) for r in rows]
        finally:
            conn.close()
    except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
        logger.warning("MDQ FTS5 search failed: %s", e)
        results = []
    return SearchDocsResult(query=req.query, results=results, total=len(results))
