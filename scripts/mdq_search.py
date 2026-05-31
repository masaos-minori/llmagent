#!/usr/bin/env python3
"""
scripts/mdq_search.py
Search functionality for the MDQ MCP server.

This script provides functions to search indexed Markdown documents
using full-text search capabilities.
"""

from __future__ import annotations

import sqlite3

import orjson
from mcp.mdq.models import _get_cfg

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

cfg = _get_cfg()
index_db_path = cfg.get("index_db_path", "/opt/llm/db/mdq.sqlite")


# ──────────────────────────────────────────────────────────────────────────────
# Search Functions
# ──────────────────────────────────────────────────────────────────────────────


def search_docs(
    query: str, path_filter: str | None = None, tag_filter: str | None = None
) -> str:
    """Search for relevant Markdown document sections based on a query."""
    conn = sqlite3.connect(index_db_path)
    cursor = conn.cursor()

    # Build the search query
    search_conditions = []
    search_params = [f"%{query}%"]

    if path_filter:
        search_conditions.append("path LIKE ?")
        search_params.append(f"%{path_filter}%")

    if tag_filter:
        search_conditions.append("tags LIKE ?")
        search_params.append(f"%{tag_filter}%")

    # Base query
    base_query = """
        SELECT id, path, heading, content, tags, created_at, updated_at
        FROM chunks
    """

    # Add WHERE clause if needed
    if search_conditions:
        where_clause = " AND ".join(search_conditions)
        base_query += f" WHERE {where_clause}"

    # Add FTS search
    fts_query = """
        SELECT chunks.id, chunks.path, chunks.heading, chunks.content, chunks.tags, chunks.created_at, chunks.updated_at
        FROM chunks_fts
        JOIN chunks ON chunks_fts.rowid = chunks.id
        WHERE chunks_fts MATCH ?
    """

    # Combine with additional filters
    if search_conditions:
        fts_query += f" AND {where_clause}"

    # Execute the query
    try:
        cursor.execute(fts_query, [query] + search_params)
        results = cursor.fetchall()

        # Format results
        formatted_results = []
        for row in results:
            chunk_id, path, heading, content, tags_json, created_at, updated_at = row
            tags = orjson.loads(tags_json) if tags_json else []
            formatted_results.append(
                {
                    "id": chunk_id,
                    "path": path,
                    "heading": heading,
                    "content_preview": content[:200] + "..."
                    if len(content) > 200
                    else content,
                    "tags": tags,
                    "created_at": created_at,
                    "updated_at": updated_at,
                }
            )

        return orjson.dumps(formatted_results).decode()
    except Exception as e:
        raise ValueError(f"Search error: {e}")
    finally:
        conn.close()


def get_chunk(chunk_id: str) -> str:
    """Retrieve a specific Markdown document chunk by its ID."""
    conn = sqlite3.connect(index_db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, path, heading, content, tags, created_at, updated_at
            FROM chunks
            WHERE id = ?
        """,
            (chunk_id,),
        )

        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Chunk with ID {chunk_id} not found")

        chunk_id, path, heading, content, tags_json, created_at, updated_at = row
        tags = orjson.loads(tags_json) if tags_json else []

        result = {
            "id": chunk_id,
            "path": path,
            "heading": heading,
            "content": content,
            "tags": tags,
            "created_at": created_at,
            "updated_at": updated_at,
        }

        return orjson.dumps(result).decode()
    except Exception as e:
        raise ValueError(f"Error retrieving chunk {chunk_id}: {e}")
    finally:
        conn.close()


def outline(path: str) -> str:
    """Get the outline of a Markdown document."""
    conn = sqlite3.connect(index_db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT headings, tags
            FROM outlines
            WHERE path = ?
        """,
            (path,),
        )

        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Outline for path {path} not found")

        headings_json, tags_json = row
        headings = orjson.loads(headings_json) if headings_json else []
        tags = orjson.loads(tags_json) if tags_json else []

        result = {"path": path, "headings": headings, "tags": tags}

        return orjson.dumps(result).decode()
    except Exception as e:
        raise ValueError(f"Error retrieving outline for {path}: {e}")
    finally:
        conn.close()
