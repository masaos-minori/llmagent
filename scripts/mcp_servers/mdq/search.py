#!/usr/bin/env python3
"""mcp_servers/mdq/search.py

Search functionality using FTS5 (BM25).
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
from typing import TYPE_CHECKING

from mcp_servers.mdq.mdq_models import (
    MdqConsistencyError,
    SearchDocsRequest,
    SearchResultItem,
    SearchResultResult,
)

if TYPE_CHECKING:
    from mcp_servers.mdq.mdq_service import MdqService

logger = logging.getLogger(__name__)


async def search_docs(service: MdqService, req: SearchDocsRequest) -> str:
    """Search indexed Markdown sections by query; returns formatted results."""
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(_search_docs_structured, service, req),
            timeout=service.search_timeout_sec,
        )
    except TimeoutError as e:
        raise MdqConsistencyError(
            f"Search timed out after {service.search_timeout_sec}s: {req.query!r}"
        ) from e
    if not result["results"]:
        return f"No results found for: {req.query!r}"

    # Apply result size limits (request overrides bounded by config cap)
    original_total = result["total"]
    request_results = getattr(req, "max_results_limit", None)
    config_results = service.max_results_limit
    max_results = (
        min(request_results, config_results)
        if request_results is not None
        else config_results
    )

    request_chars = getattr(req, "max_total_result_chars", None)
    config_chars = service.max_total_result_chars
    max_chars = (
        min(request_chars, config_chars) if request_chars is not None else config_chars
    )

    truncated = False
    if original_total > max_results:
        truncated = True
        result["results"] = result["results"][:max_results]

    # Enforce char limit
    if len(result["results"]) > 0:
        lines = [f"Search results for: {req.query!r} ({original_total} found)"]
        for r in result["results"]:
            line = f"{r.source_path}: {r.heading}: {r.snippet}"
            if len("\n".join(lines)) + len(line) > max_chars:
                truncated = True
                break
            lines.append(line)
        shown = len(lines) - 1  # subtract header line
        chars_used = len("\n".join(lines))
        if truncated:
            return "\n".join(lines) + (
                f"\n\n[Truncated — {original_total} results found, "
                f"{shown} shown ({chars_used}/{max_chars} chars). "
                f"Use a narrower query or get_chunk for specific sections.]"
            )
        return "\n".join(lines)

    return f"Search results for: {req.query!r} ({original_total} found)"


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
        where_clauses, params = _build_search_where(req)
        where_clause = " AND ".join(where_clauses)

        # Get FTS5 results
        fts_results: list[SearchResultItem] = []
        rows = conn.execute(
            f"""SELECT c.chunk_id, c.source_path, c.heading, c.heading_path,
                       c.start_line, c.end_line, c.token_count, c.content,
                       rank
                FROM chunks_fts f
                JOIN chunks c ON f.rowid = c.rowid
                WHERE {where_clause}
                ORDER BY rank
                LIMIT ?""",
            params + [limit],
        ).fetchall()

        fts_results = [
            SearchResultItem(
                chunk_id=row["chunk_id"],
                source_path=row["source_path"],
                heading=row["heading"],
                heading_path=row["heading_path"],
                score=float(row["rank"]) if row["rank"] is not None else 0.0,
                start_line=row["start_line"],
                end_line=row["end_line"],
                token_count=row["token_count"],
                snippet=row["content"][: service.max_snippet_chars],
            )
            for row in rows
        ]

        results = fts_results

    except sqlite3.OperationalError as e:
        if "no such table: chunks_fts" in str(e) or "corrupt" in str(e).lower():
            logger.error("MDQ FTS5 search failed: %s", e)
            raise MdqConsistencyError(f"FTS5 index inconsistency: {e}") from e
        logger.warning("MDQ FTS5 search failed: %s", e)
        results = []
    except sqlite3.Error as e:
        logger.error("MDQ database error during search: %s", e)
        raise MdqConsistencyError(f"FTS5 index inconsistency: {e}") from e
    finally:
        conn.close()

    return SearchResultResult(query=req.query, results=results, total=len(results))


def _build_search_where(req: SearchDocsRequest) -> tuple[list[str], list]:
    """Build WHERE clause and params for search."""
    where_clauses = ["chunks_fts MATCH ?"]
    params: list = [req.query]

    if req.path_prefix:
        where_clauses.append("c.source_path LIKE ?")
        params.append(f"{req.path_prefix}%")

    if req.heading_prefix:
        where_clauses.append("c.heading_path LIKE ?")
        params.append(f"{req.heading_prefix}%")

    if req.tag_filter:
        for tag in req.tag_filter:
            where_clauses.append("c.tags_json LIKE ?")
            params.append(f"%{tag}%")

    return where_clauses, params
