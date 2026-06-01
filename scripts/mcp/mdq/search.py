#!/usr/bin/env python3
"""mcp/mdq/search.py
Search functionality for Markdown Context Compression Engine.
"""

from __future__ import annotations

import logging
import sqlite3
from typing import Any

import orjson
from shared.config_loader import get_config

from mcp.mdq.indexer import Indexer

logger = logging.getLogger(__name__)

_ChunkResult = dict[str, Any]


def _parse_tags(raw: str | None) -> list[str]:
    """Return the deserialized tag list, or [] on missing/invalid JSON."""
    if not raw:
        return []
    try:
        return orjson.loads(raw)  # type: ignore[no-any-return]
    except Exception:
        return []


def _make_chunk_result(
    chunk_id: str,
    source_path: str,
    heading_path: str,
    content: str,
    token_count: int,
    raw_tags: str | None,
    score: float,
) -> _ChunkResult:
    """Build the standard result dict for one chunk row."""
    snippet = content[:100] + "..." if len(content) > 100 else content
    return {
        "chunk_id": chunk_id,
        "source_path": source_path,
        "heading_path": heading_path,
        "score": score,
        "snippet": snippet,
        "token_count": token_count,
        "tags": _parse_tags(raw_tags),
    }


def search_chunks(
    query: str,
    limit: int | None = 10,
    mode: str | None = "hybrid",
    path_prefix: str | None = None,
    tag_filter: list[str] | None = None,
    heading_prefix: str | None = None,
) -> list[_ChunkResult]:
    """Search for chunks matching the query."""
    try:
        cfg = get_config("mdq_mcp_server")
        db_path = str(cfg.get("db_path", "/opt/llm/db/mdq.sqlite"))
        indexer = Indexer(db_path)
        n = limit if limit is not None else 10

        if mode == "bm25":
            return _search_bm25(
                indexer,
                query,
                n,
                path_prefix,
                tag_filter,
                heading_prefix,
            )
        if mode == "grep":
            return _search_grep(
                indexer,
                query,
                n,
                path_prefix,
                tag_filter,
                heading_prefix,
            )
        if mode == "hybrid":
            bm25 = _search_bm25(
                indexer,
                query,
                n * 2,
                path_prefix,
                tag_filter,
                heading_prefix,
            )
            grep = _search_grep(
                indexer,
                query,
                n * 2,
                path_prefix,
                tag_filter,
                heading_prefix,
            )
            seen: set[str] = set()
            merged: list[_ChunkResult] = []
            for r in bm25 + grep:
                if r["chunk_id"] not in seen:
                    seen.add(r["chunk_id"])
                    merged.append(r)
            return merged[:n]
        # Default: BM25
        return _search_bm25(indexer, query, n, path_prefix, tag_filter, heading_prefix)
    except Exception as e:
        logger.error(f"Error in search_chunks: {e}")
        return []


def _apply_filters(
    sql: str,
    params: list[str | int],
    path_prefix: str | None,
    heading_prefix: str | None,
    tag_filter: list[str] | None,
) -> tuple[str, list[str | int]]:
    """Append optional filter clauses and return the updated (sql, params) pair."""
    if path_prefix:
        sql += " AND d.source_path LIKE ?"
        params.append(f"{path_prefix}%")
    if heading_prefix:
        sql += " AND c.heading_path LIKE ?"
        params.append(f"{heading_prefix}%")
    if tag_filter:
        conditions = " OR ".join(["c.tags LIKE ?" for _ in tag_filter])
        sql += f" AND ({conditions})"
        params.extend([f"%{tag}%" for tag in tag_filter])
    return sql, params


def _search_bm25(
    indexer: Indexer,
    query: str,
    limit: int,
    path_prefix: str | None,
    tag_filter: list[str] | None,
    heading_prefix: str | None,
) -> list[_ChunkResult]:
    """Perform BM25 search using FTS."""
    try:
        sql = """
            SELECT c.chunk_id, d.source_path, c.heading_path,
                   c.content, c.token_count, c.tags, fts.rank as score
            FROM md_chunks c
            JOIN md_documents d ON c.doc_id = d.doc_id
            JOIN md_chunks_fts fts ON c.chunk_id = fts.rowid
            WHERE fts MATCH ?
        """
        params: list[str | int] = [query]
        sql, params = _apply_filters(
            sql,
            params,
            path_prefix,
            heading_prefix,
            tag_filter,
        )
        sql += " ORDER BY fts.rank LIMIT ?"
        params.append(limit)

        with sqlite3.connect(indexer.db_path) as conn:
            rows = conn.execute(sql, params).fetchall()
        return [
            _make_chunk_result(cid, sp, hp, cnt, tc, tags, float(score))
            for cid, sp, hp, cnt, tc, tags, score in rows
        ]
    except Exception as e:
        logger.error(f"Error in BM25 search: {e}")
        return []


def _search_grep(
    indexer: Indexer,
    query: str,
    limit: int,
    path_prefix: str | None,
    tag_filter: list[str] | None,
    heading_prefix: str | None,
) -> list[_ChunkResult]:
    """Perform grep-style (LIKE) search; score is always 0.0."""
    try:
        sql = """
            SELECT c.chunk_id, d.source_path, c.heading_path,
                   c.content, c.token_count, c.tags
            FROM md_chunks c
            JOIN md_documents d ON c.doc_id = d.doc_id
            WHERE c.content LIKE ?
        """
        params: list[str | int] = [f"%{query}%"]
        sql, params = _apply_filters(
            sql,
            params,
            path_prefix,
            heading_prefix,
            tag_filter,
        )
        sql += " LIMIT ?"
        params.append(limit)

        with sqlite3.connect(indexer.db_path) as conn:
            rows = conn.execute(sql, params).fetchall()
        return [
            _make_chunk_result(cid, sp, hp, cnt, tc, tags, 0.0)
            for cid, sp, hp, cnt, tc, tags in rows
        ]
    except Exception as e:
        logger.error(f"Error in grep search: {e}")
        return []
