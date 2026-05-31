#!/usr/bin/env python3
"""
scripts/mdq_indexer.py
Markdown document indexer for the MDQ MCP server.

This script indexes Markdown documents and creates a SQLite database with:
- Document structure (headings, paths, tags)
- Chunked content with metadata
- Full-text search capabilities
"""

from __future__ import annotations

import hashlib
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any

import orjson
from mcp.mdq.models import _get_cfg
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

cfg = _get_cfg()
index_db_path = cfg.get("index_db_path", "/opt/llm/db/mdq.sqlite")
index_paths_cfg = cfg.get("index_paths", [])
refresh_index = cfg.get("refresh_index", False)

# ──────────────────────────────────────────────────────────────────────────────
# Data Models
# ──────────────────────────────────────────────────────────────────────────────


class DocumentChunk(BaseModel):
    """Represents a chunk of a Markdown document."""

    id: str
    path: str
    heading: str
    content: str
    tags: list[str]
    created_at: float
    updated_at: float


class DocumentOutline(BaseModel):
    """Represents the outline of a Markdown document."""

    path: str
    headings: list[
        dict[str, Any]
    ]  # List of heading dictionaries with level, text, etc.
    tags: list[str]


# ──────────────────────────────────────────────────────────────────────────────
# Database Setup
# ──────────────────────────────────────────────────────────────────────────────


def init_db(db_path: str) -> None:
    """Initialize the SQLite database with required tables."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create chunks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id TEXT PRIMARY KEY,
            path TEXT NOT NULL,
            heading TEXT,
            content TEXT NOT NULL,
            tags TEXT,  -- JSON array of tags
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            content_hash TEXT,
            UNIQUE(path, heading)
        )
    """)

    # Create outlines table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS outlines (
            path TEXT PRIMARY KEY,
            headings TEXT NOT NULL,  -- JSON array of headings
            tags TEXT,  -- JSON array of tags
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
    """)

    # Create FTS table for full-text search
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
            content,
            heading,
            path,
            tags,
            content='chunks',
            content_rowid='id'
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_path ON chunks(path)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_heading ON chunks(heading)")

    conn.commit()
    conn.close()


# ──────────────────────────────────────────────────────────────────────────────
# Indexing Functions
# ──────────────────────────────────────────────────────────────────────────────


def get_file_mtime(path: Path) -> float:
    """Get the modification time of a file."""
    return path.stat().st_mtime


def calculate_content_hash(content: str) -> str:
    """Calculate a hash of the content for change detection."""
    return hashlib.md5(content.encode()).hexdigest()


def index_document(path: Path, db_path: str) -> None:
    """Index a single Markdown document."""
    try:
        # Read the file
        content = path.read_text(encoding="utf-8")

        # Parse the document structure
        from mcp.mdq.parser import parse_markdown_file  # noqa: PLC0415

        file_data = parse_markdown_file(str(path))
        outline = DocumentOutline(
            path=str(path),
            headings=file_data.get("outline", []),
            tags=[],
        )

        # Create chunks from the document
        chunks = create_chunks_from_outline(path, outline, content)

        # Save to database
        save_chunks_to_db(chunks, db_path)
        save_outline_to_db(outline, db_path)

        logger.info(f"Indexed document: {path}")

    except Exception as e:
        logger.error(f"Failed to index document {path}: {e}")


def create_chunks_from_outline(
    path: Path, outline: DocumentOutline, content: str
) -> list[DocumentChunk]:
    """Create chunks from document outline."""
    chunks = []

    # For now, we'll create a simple chunk per heading
    # In the future, this could be more sophisticated with chunk splitting
    for heading in outline.headings:
        # Create a chunk ID based on path and heading
        heading_text = heading.get("text", "")
        chunk_id = f"{path}:{heading_text}"

        # Extract the content for this heading
        # This is a simplified approach - in reality, you'd want to extract
        # the actual content between this heading and the next one
        content_start = content.find(f"## {heading_text}")
        content_end = (
            content.find("## ", content_start + 1)
            if content_start != -1
            else len(content)
        )

        if content_start != -1:
            chunk_content = content[content_start:content_end].strip()
        else:
            chunk_content = content

        # Create the chunk
        chunk = DocumentChunk(
            id=chunk_id,
            path=str(path),
            heading=heading_text,
            content=chunk_content,
            tags=outline.tags,
            created_at=time.time(),
            updated_at=time.time(),
        )
        chunks.append(chunk)

    return chunks


def save_chunks_to_db(chunks: list[DocumentChunk], db_path: str) -> None:
    """Save chunks to the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for chunk in chunks:
        # Convert tags to JSON string
        tags_json = orjson.dumps(chunk.tags).decode()

        # Calculate content hash
        content_hash = calculate_content_hash(chunk.content)

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO chunks (id, path, heading, content, tags, created_at, updated_at, content_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    chunk.id,
                    chunk.path,
                    chunk.heading,
                    chunk.content,
                    tags_json,
                    chunk.created_at,
                    chunk.updated_at,
                    content_hash,
                ),
            )
        except Exception as e:
            logger.error(f"Failed to save chunk {chunk.id}: {e}")

    conn.commit()
    conn.close()


def save_outline_to_db(outline: DocumentOutline, db_path: str) -> None:
    """Save document outline to the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Convert headings and tags to JSON strings
    headings_json = orjson.dumps(outline.headings).decode()
    tags_json = orjson.dumps(outline.tags).decode()

    try:
        cursor.execute(
            """
            INSERT OR REPLACE INTO outlines (path, headings, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """,
            (outline.path, headings_json, tags_json, time.time(), time.time()),
        )
    except Exception as e:
        logger.error(f"Failed to save outline for {outline.path}: {e}")

    conn.commit()
    conn.close()


def index_paths(paths: list[str], db_path: str) -> None:
    """Index all Markdown files in the given paths."""
    for path_str in paths:
        path = Path(path_str)
        if path.is_dir():
            # Recursively find all .md files
            for md_file in path.rglob("*.md"):
                index_document(md_file, db_path)
        elif path.is_file() and path.suffix == ".md":
            index_document(path, db_path)
        else:
            logger.warning(f"Skipping non-Markdown path: {path}")


# ──────────────────────────────────────────────────────────────────────────────
# Main Execution
# ──────────────────────────────────────────────────────────────────────────────


def main() -> None:
    """Main entry point for the indexer."""
    # Initialize database
    init_db(index_db_path)

    # Index the specified paths
    if index_paths_cfg:
        logger.info(f"Indexing paths: {index_paths_cfg}")
        index_paths(index_paths_cfg, index_db_path)
    else:
        logger.info("No paths specified for indexing")

    # Check if we should refresh the index
    if refresh_index:
        logger.info("Refreshing index...")
        # This would be implemented based on your specific requirements
        # For now, we'll just log that we're refreshing
        pass

    logger.info("Indexing complete")


if __name__ == "__main__":
    main()
