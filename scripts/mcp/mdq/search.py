#!/usr/bin/env python3
"""
mcp/mdq/search.py
Search functionality for Markdown Context Compression Engine.
"""

from __future__ import annotations

import logging
import sqlite3

import orjson
from shared.config_loader import get_config

from mcp.mdq.indexer import Indexer

logger = logging.getLogger(__name__)


def search_chunks(
    query: str,
    limit: int | None = 10,
    mode: str | None = "hybrid",
    path_prefix: str | None = None,
    tag_filter: list[str] | None = None,
    heading_prefix: str | None = None,
) -> list[dict]:
    """Search for chunks matching the query."""
    try:
        # Get the database path
        cfg = get_config("mdq_mcp_server")
        db_path = str(cfg.get("db_path", "/opt/llm/db/mdq.sqlite"))

        indexer = Indexer(db_path)
        effective_limit = limit if limit is not None else 10

        # Build the search query based on mode
        if mode == "bm25":
            return _search_bm25(
                indexer, query, effective_limit, path_prefix, tag_filter, heading_prefix
            )
        elif mode == "grep":
            return _search_grep(
                indexer, query, effective_limit, path_prefix, tag_filter, heading_prefix
            )
        elif mode == "hybrid":
            # Combine BM25 and grep results
            bm25_results = _search_bm25(
                indexer,
                query,
                effective_limit * 2,
                path_prefix,
                tag_filter,
                heading_prefix,
            )
            grep_results = _search_grep(
                indexer,
                query,
                effective_limit * 2,
                path_prefix,
                tag_filter,
                heading_prefix,
            )
            # Combine and deduplicate results
            all_results = bm25_results + grep_results
            # Remove duplicates while preserving order
            seen = set()
            unique_results = []
            for result in all_results:
                if result["chunk_id"] not in seen:
                    seen.add(result["chunk_id"])
                    unique_results.append(result)
            return unique_results[:effective_limit]
        else:
            # Default to BM25
            return _search_bm25(
                indexer, query, effective_limit, path_prefix, tag_filter, heading_prefix
            )
    except Exception as e:
        logger.error(f"Error in search_chunks: {e}")
        return []


def _search_bm25(
    indexer: Indexer,
    query: str,
    limit: int,
    path_prefix: str | None,
    tag_filter: list[str] | None,
    heading_prefix: str | None,
) -> list[dict]:
    """Perform BM25 search using FTS."""
    try:
        with sqlite3.connect(indexer.db_path) as conn:
            # Build the base query
            base_query = """
                SELECT c.chunk_id, d.source_path, c.heading_path,
                       c.content, c.token_count, c.tags,
                       fts.rank as score
                FROM md_chunks c
                JOIN md_documents d ON c.doc_id = d.doc_id
                JOIN md_chunks_fts fts ON c.chunk_id = fts.rowid
                WHERE fts MATCH ?
            """

            # Add filters
            params: list[str | int] = [query]

            if path_prefix:
                base_query += " AND d.source_path LIKE ?"
                params.append(f"{path_prefix}%")

            if heading_prefix:
                base_query += " AND c.heading_path LIKE ?"
                params.append(f"{heading_prefix}%")

            if tag_filter:
                # Convert tags to a format that can be matched
                tag_conditions = " OR ".join(["c.tags LIKE ?" for _ in tag_filter])
                base_query += f" AND ({tag_conditions})"
                params.extend([f"%{tag}%" for tag in tag_filter])

            # Add ordering and limit
            base_query += " ORDER BY fts.rank LIMIT ?"
            params.append(limit)

            cursor = conn.execute(base_query, params)

            results = []
            for row in cursor.fetchall():
                (
                    chunk_id,
                    source_path,
                    heading_path,
                    content,
                    token_count,
                    tags,
                    score,
                ) = row

                # Parse tags
                try:
                    parsed_tags = orjson.loads(tags) if tags else []
                except Exception:
                    parsed_tags = []

                # Create snippet (first 100 characters)
                snippet = content[:100] + "..." if len(content) > 100 else content

                results.append(
                    {
                        "chunk_id": chunk_id,
                        "source_path": source_path,
                        "heading_path": heading_path,
                        "score": float(score),
                        "snippet": snippet,
                        "token_count": token_count,
                        "tags": parsed_tags,
                    }
                )

            return results
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
) -> list[dict]:
    """Perform grep-style search."""
    try:
        with sqlite3.connect(indexer.db_path) as conn:
            # Build the base query
            base_query = """
                SELECT c.chunk_id, d.source_path, c.heading_path,
                       c.content, c.token_count, c.tags
                FROM md_chunks c
                JOIN md_documents d ON c.doc_id = d.doc_id
                WHERE c.content LIKE ?
            """

            # Add filters
            params: list[str | int] = [f"%{query}%"]

            if path_prefix:
                base_query += " AND d.source_path LIKE ?"
                params.append(f"{path_prefix}%")

            if heading_prefix:
                base_query += " AND c.heading_path LIKE ?"
                params.append(f"{heading_prefix}%")

            if tag_filter:
                # Convert tags to a format that can be matched
                tag_conditions = " OR ".join(["c.tags LIKE ?" for _ in tag_filter])
                base_query += f" AND ({tag_conditions})"
                params.extend([f"%{tag}%" for tag in tag_filter])

            # Add ordering and limit
            base_query += " LIMIT ?"
            params.append(limit)

            cursor = conn.execute(base_query, params)

            results = []
            for row in cursor.fetchall():
                chunk_id, source_path, heading_path, content, token_count, tags = row

                # Parse tags
                try:
                    parsed_tags = orjson.loads(tags) if tags else []
                except Exception:
                    parsed_tags = []

                # Create snippet (first 100 characters)
                snippet = content[:100] + "..." if len(content) > 100 else content

                results.append(
                    {
                        "chunk_id": chunk_id,
                        "source_path": source_path,
                        "heading_path": heading_path,
                        "score": 0.0,  # No score for grep search
                        "snippet": snippet,
                        "token_count": token_count,
                        "tags": parsed_tags,
                    }
                )

            return results
    except Exception as e:
        logger.error(f"Error in grep search: {e}")
        return []
