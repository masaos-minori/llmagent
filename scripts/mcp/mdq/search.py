#!/usr/bin/env python3
"""mcp/mdq/search.py
Search functionality using FTS5.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mcp.mdq.models import SearchDocsRequest

if TYPE_CHECKING:
    from mcp.mdq.service import MdqService

logger = logging.getLogger(__name__)


async def search_docs(service: MdqService, req: SearchDocsRequest) -> str:
    """Search indexed Markdown sections by query; returns formatted results."""
    result = _search_docs_structured(service, req)
    if not result["results"]:
        return f"No results found for: {req.query!r}"
    lines = [f"Search results for: {req.query!r} ({result['total']} found)"]
    for i, r in enumerate(result["results"], 1):
        lines.append(f"{i}. {r}")
    return "\n".join(lines)


def _search_docs_structured(service: MdqService, req: SearchDocsRequest) -> dict:
    """Run FTS5 search; return structured result dict."""
    if not req.query or not req.query.strip():
        return {"query": req.query, "results": [], "total": 0}

    logger.info("MDQ search query: %s", req.query)

    limit = getattr(req, "limit", 10) or 10

    conn = service._get_db_connection()
    try:
        if req.path_prefix:
            rows = conn.execute(
                """SELECT s.file_path, s.heading, s.content
                   FROM sections_fts f
                   JOIN sections s ON f.rowid = s.id
                   WHERE sections_fts MATCH ?
                   AND s.file_path LIKE ?
                   ORDER BY rank
                   LIMIT ?""",
                (req.query, f"{req.path_prefix}%", limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT s.file_path, s.heading, s.content
                   FROM sections_fts f
                   JOIN sections s ON f.rowid = s.id
                   WHERE sections_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (req.query, limit),
            ).fetchall()

        results = []
        for row in rows:
            results.append(
                f"[{row['file_path']}] {row['heading']}: {row['content'][:150]}"
            )
    except Exception as e:
        logger.warning("MDQ FTS5 search failed: %s", e)
        results = []
    finally:
        conn.close()

    return {"query": req.query, "results": results, "total": len(results)}
