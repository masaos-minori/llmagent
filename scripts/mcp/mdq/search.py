#!/usr/bin/env python3
"""mcp/mdq/search.py
Search functionality using FTS5 and optional embedding/hybrid search.
"""

from __future__ import annotations

import logging
import sqlite3
from typing import TYPE_CHECKING

from mcp.mdq.models import SearchDocsRequest, SearchResultItem, SearchResultResult

if TYPE_CHECKING:
    from mcp.mdq.service import MdqService

logger = logging.getLogger(__name__)

# RRF constant for hybrid search merge
_RRF_K = 60


async def search_docs(service: MdqService, req: SearchDocsRequest) -> str:
    """Search indexed Markdown sections by query; returns formatted results."""
    result = _search_docs_structured(service, req)
    if not result["results"]:
        return f"No results found for: {req.query!r}"

    # Apply result size limits
    total = result["total"]
    max_results = getattr(req, "max_results_limit", None) or service.max_results_limit
    max_chars = (
        getattr(req, "max_total_result_chars", None) or service.max_total_result_chars
    )

    truncated = False
    if total > max_results:
        truncated = True
        result["results"] = result["results"][:max_results]
        total = max_results

    # Enforce char limit
    if len(result["results"]) > 0:
        lines = [f"Search results for: {req.query!r} ({total} found)"]
        for r in result["results"]:
            line = f"{r.source_path}: {r.heading}: {r.snippet}"
            if len("\n".join(lines)) + len(line) > max_chars:
                truncated = True
                break
            lines.append(line)
        if truncated:
            return (
                "\n".join(lines) + f"\n\n[Truncated — total chars exceeded {max_chars}]"
            )
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

    # Determine search mode
    mode = getattr(req, "mode", None) or "bm25"

    conn = service._get_db_connection()
    try:
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

        where_clause = " AND ".join(where_clauses)

        # Get FTS5 results
        fts_results: list[SearchResultItem] = []
        rows = conn.execute(
            f"""SELECT c.chunk_id, c.source_path, c.heading, c.heading_path,
                       c.start_line, c.end_line, c.token_count, c.content,
                       rank
                FROM chunks_fts f
                JOIN chunks c ON f.rowid = c.id
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
                snippet=row["content"][:150],
            )
            for row in rows
        ]

        # Hybrid search: also run vector search and merge with RRF
        if mode == "hybrid" and service.use_embedding:
            vector_results = _search_vector(service, conn, req)
            results = _merge_hybrid(fts_results, vector_results)
        else:
            results = fts_results

    except sqlite3.OperationalError as e:
        if "no such table: chunks_fts" in str(e) or "corrupt" in str(e).lower():
            logger.error("MDQ FTS5 search failed: %s", e)
            from mcp.mdq.models import MdqConsistencyError

            raise MdqConsistencyError(f"FTS5 index inconsistency: {e}") from e
        logger.warning("MDQ FTS5 search failed: %s", e)
        results = []
    except sqlite3.Error as e:
        logger.error("MDQ database error during search: %s", e)
        from mcp.mdq.models import MdqConsistencyError

        raise MdqConsistencyError(f"FTS5 index inconsistency: {e}") from e
    finally:
        conn.close()

    return SearchResultResult(query=req.query, results=results, total=len(results))


def _search_vector(
    service: MdqService, conn: sqlite3.Connection, req: SearchDocsRequest
) -> list[SearchResultItem]:
    """Run vector similarity search on the vector table."""
    # Placeholder: actual embedding generation and search would require an LLM API call
    # For now, return empty results — hybrid search requires embedding model integration
    logger.info("MDQ hybrid search mode requested but embeddings not yet implemented")
    return []


def _merge_hybrid(
    fts_results: list[SearchResultItem], vector_results: list[SearchResultItem]
) -> list[SearchResultItem]:
    """Merge FTS5 and vector results using Reciprocal Rank Fusion (RRF)."""
    if not fts_results and not vector_results:
        return []

    # Build rank maps from each source
    rank_map: dict[str, float] = {}

    for i, r in enumerate(fts_results):
        rank_map[r.chunk_id] = rank_map.get(r.chunk_id, 0) + 1.0 / (_RRF_K + (i + 1))

    for i, r in enumerate(vector_results):
        rank_map[r.chunk_id] = rank_map.get(r.chunk_id, 0) + 1.0 / (_RRF_K + (i + 1))

    # Sort by combined RRF score
    merged = sorted(rank_map.items(), key=lambda x: x[1], reverse=True)

    # Build result items with merged scores
    results: list[SearchResultItem] = []
    for chunk_id, rrf_score in merged:
        # Find original item from either source
        item = None
        for r in fts_results + vector_results:
            if r.chunk_id == chunk_id:
                item = r
                break
        if item:
            item.score = rrf_score  # type: ignore[assignment]
            results.append(item)

    return results
