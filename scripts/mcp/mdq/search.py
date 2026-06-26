#!/usr/bin/env python3
"""mcp/mdq/search.py
Search functionality using FTS5.
"""

from __future__ import annotations

import logging
import sqlite3
from typing import TYPE_CHECKING

from mcp.mdq.models import SearchDocsRequest, SearchResultItem, SearchResultResult

if TYPE_CHECKING:
    from mcp.mdq.service import MdqService

logger = logging.getLogger(__name__)


async def search_docs(service: MdqService, req: SearchDocsRequest) -> str:
    """Search indexed Markdown sections by query; returns formatted results."""
    result = _search_docs_structured(service, req)
    if not result["results"]:
        return f"No results found for: {req.query!r}"

    # Apply result size limits
    total = result["total"]
    max_results = getattr(req, "max_results_limit", None) or service.max_results_limit
    max_chars = getattr(req, "max_total_result_chars", None) or service.max_total_result_chars

    truncated = False
    if total > max_results:
        truncated = True
        result["results"] = result["results"][:max_results]
        total = max_results

    # Enforce char limit
    if len(result["results"]) > 0:
        lines = [f"Search results for: {req.query!r} ({total} found)"]
        for r in result["results"]:
            line = f"{r.file_path}: {r.heading}: {r.content[:150]}"
            if len("\n".join(lines)) + len(line) > max_chars:
                truncated = True
                break
            lines.append(line)
        if truncated:
            return "\n".join(lines) + f"\n\n[Truncated — total chars exceeded {max_chars}]"
        return "\n".join(lines)

    return f"Search results for: {req.query!r} ({total} found)"


def _search_docs_structured(
    service: MdqService, req: SearchDocsRequest
) -> SearchResultResult:
    """Run FTS5 search; return structured result."""
    if not req.query or not req.query.strip():
        return SearchResultResult(query=req.query, results=[], total=0)

    logger.info("MDQ search query: %s", req.query)

    limit = getattr(req, "limit", 10) or 10

    conn = service._get_db_connection()
    try:
        if req.path_prefix:
            rows = conn.execute(
                """SELECT c.source_path, c.heading, c.content
                   FROM chunks_fts f
                   JOIN chunks c ON f.rowid = c.chunk_id
                   WHERE chunks_fts MATCH ?
                   AND c.source_path LIKE ?
                   ORDER BY rank
                   LIMIT ?""",
                (req.query, f"{req.path_prefix}%", limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT c.source_path, c.heading, c.content
                   FROM chunks_fts f
                   JOIN chunks c ON f.rowid = c.chunk_id
                   WHERE chunks_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (req.query, limit),
            ).fetchall()

        results = [
            SearchResultItem(
                file_path=row["source_path"],
                heading=row["heading"],
                content=row["content"],
            )
            for row in rows
        ]
    except sqlite3.Error as e:
        logger.warning("MDQ FTS5 search failed: %s", e)
        results = []
    finally:
        conn.close()

    return SearchResultResult(query=req.query, results=results, total=len(results))
