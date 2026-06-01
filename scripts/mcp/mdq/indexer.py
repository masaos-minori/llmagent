#!/usr/bin/env python3
"""mcp/mdq/indexer.py
Indexer for Markdown Context Compression Engine.
"""

from __future__ import annotations

import hashlib
import logging
import os
import sqlite3

import orjson
from shared.config_loader import get_config

from mcp.mdq.parser import parse_markdown_file

logger = logging.getLogger(__name__)


class Indexer:
    """Indexer for Markdown documents."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or self._get_db_path()
        self._init_db()

    def _get_db_path(self) -> str:
        """Get the database path from configuration."""
        cfg = get_config("mdq_mcp_server")
        return str(cfg.get("db_path", "/opt/llm/db/mdq.sqlite"))

    def _init_db(self) -> None:
        """Initialize the database schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS md_documents (
                        doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_path TEXT UNIQUE NOT NULL,
                        title TEXT,
                        mtime REAL,
                        etag_hash TEXT,
                        lang TEXT,
                        doc_hash TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS md_chunks (
                        chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        doc_id INTEGER NOT NULL,
                        heading_path TEXT,
                        heading_level INTEGER,
                        section_title TEXT,
                        tags TEXT,
                        token_count INTEGER,
                        char_count INTEGER,
                        content TEXT,
                        normalized_content TEXT,
                        anchor TEXT,
                        chunk_order INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (doc_id) REFERENCES md_documents (doc_id) ON DELETE CASCADE
                    )
                """)
                conn.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS md_chunks_fts USING fts5(
                        content,
                        normalized_content,
                        tokenize='porter unicode61'
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON md_chunks(doc_id)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunks_heading_path ON md_chunks(heading_path)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunks_chunk_order ON md_chunks(chunk_order)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_documents_source_path ON md_documents(source_path)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_documents_mtime ON md_documents(mtime)
                """)
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def _get_file_hash(self, file_path: str) -> str:
        """Calculate the hash of a file."""
        try:
            with open(file_path, "rb") as f:
                file_hash = hashlib.md5()
                while chunk := f.read(8192):
                    file_hash.update(chunk)
                return file_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating file hash for {file_path}: {e}")
            return ""

    def _get_file_mtime(self, file_path: str) -> float:
        """Get the modification time of a file."""
        try:
            return os.path.getmtime(file_path)
        except Exception as e:
            logger.error(f"Error getting file mtime for {file_path}: {e}")
            return 0.0

    def index_paths(self, paths: list[str]) -> list[str]:
        """Index a list of paths."""
        indexed_paths = []
        for path in paths:
            if os.path.isdir(path):
                # Index all .md files in the directory
                for root, _, files in os.walk(path):
                    for file in files:
                        if file.endswith((".md", ".markdown", ".mdx")):
                            file_path = os.path.join(root, file)
                            self._index_file(file_path)
                            indexed_paths.append(file_path)
            elif os.path.isfile(path) and path.endswith((".md", ".markdown", ".mdx")):
                # Index the single file
                self._index_file(path)
                indexed_paths.append(path)
        return indexed_paths

    def _index_file(self, file_path: str) -> None:
        """Index a single Markdown file."""
        try:
            # Get file metadata
            mtime = self._get_file_mtime(file_path)
            file_hash = self._get_file_hash(file_path)

            # Check if file already exists in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT doc_id, mtime, doc_hash FROM md_documents
                    WHERE source_path = ?
                """,
                    (file_path,),
                )
                result = cursor.fetchone()

                if result:
                    doc_id, existing_mtime, existing_hash = result
                    # Check if file has changed
                    if existing_mtime == mtime and existing_hash == file_hash:
                        logger.debug(f"File {file_path} unchanged, skipping indexing")
                        return  # File hasn't changed, skip re-indexing

                    # Update existing document
                    conn.execute(
                        """
                        UPDATE md_documents
                        SET mtime = ?, doc_hash = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE doc_id = ?
                    """,
                        (mtime, file_hash, doc_id),
                    )
                else:
                    # Insert new document
                    cursor = conn.execute(
                        """
                        INSERT INTO md_documents (source_path, mtime, doc_hash, created_at, updated_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                        (file_path, mtime, file_hash),
                    )
                    doc_id = cursor.lastrowid

            # Parse the file
            file_data = parse_markdown_file(file_path)
            title = file_data.get("title", "")

            # Update document title
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE md_documents
                    SET title = ?
                    WHERE doc_id = ?
                """,
                    (title, doc_id),
                )

            # Get existing chunks for this document
            existing_chunks = {}
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT chunk_id, heading_path FROM md_chunks
                    WHERE doc_id = ?
                """,
                    (doc_id,),
                )
                for row in cursor.fetchall():
                    existing_chunks[row[1]] = row[0]  # heading_path -> chunk_id

            # Process content into chunks
            content = file_data.get("content", "")
            headings = file_data.get("outline", [])

            # Split content into chunks based on headings
            chunks = self._split_content_by_headings(content, headings)

            # Insert or update chunks
            with sqlite3.connect(self.db_path) as conn:
                for i, chunk_data in enumerate(chunks):
                    heading_path = chunk_data.get("heading_path", "")
                    content_text = chunk_data.get("content", "")
                    section_title = chunk_data.get("section_title", "")
                    heading_level = chunk_data.get("heading_level", 0)
                    tags = chunk_data.get("tags", [])
                    token_count = chunk_data.get("token_count", 0)
                    char_count = len(content_text)
                    anchor = chunk_data.get("anchor", "")

                    # Normalize content for FTS search
                    normalized_content = self._normalize_content(content_text)

                    if heading_path in existing_chunks:
                        # Update existing chunk
                        chunk_id = existing_chunks[heading_path]
                        conn.execute(
                            """
                            UPDATE md_chunks
                            SET heading_path = ?, heading_level = ?, section_title = ?,
                                tags = ?, token_count = ?, char_count = ?, content = ?,
                                normalized_content = ?, anchor = ?, chunk_order = ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE chunk_id = ?
                        """,
                            (
                                heading_path,
                                heading_level,
                                section_title,
                                orjson.dumps(tags).decode(),
                                token_count,
                                char_count,
                                content_text,
                                normalized_content,
                                anchor,
                                i,
                                chunk_id,
                            ),
                        )
                    else:
                        # Insert new chunk
                        conn.execute(
                            """
                            INSERT INTO md_chunks
                            (doc_id, heading_path, heading_level, section_title, tags,
                             token_count, char_count, content, normalized_content, anchor, chunk_order)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                doc_id,
                                heading_path,
                                heading_level,
                                section_title,
                                orjson.dumps(tags).decode(),
                                token_count,
                                char_count,
                                content_text,
                                normalized_content,
                                anchor,
                                i,
                            ),
                        )

                        # Get the new chunk_id
                        cursor = conn.execute("SELECT last_insert_rowid()")
                        chunk_id = cursor.fetchone()[0]

                        # Insert into FTS table
                        conn.execute(
                            """
                            INSERT INTO md_chunks_fts (content, normalized_content)
                            VALUES (?, ?)
                        """,
                            (content_text, normalized_content),
                        )

                        # Insert into FTS table with rowid
                        conn.execute(
                            """
                            INSERT INTO md_chunks_fts (rowid, content, normalized_content)
                            VALUES (?, ?, ?)
                        """,
                            (chunk_id, content_text, normalized_content),
                        )

            logger.info(f"Indexed file: {file_path}")
        except Exception as e:
            logger.error(f"Error indexing file {file_path}: {e}")
            raise

    def _split_content_by_headings(
        self,
        content: str,
        headings: list[dict],
    ) -> list[dict]:
        """Split content into chunks based on headings."""
        chunks = []
        lines = content.split("\n")

        # Create a mapping of heading positions to their content
        heading_positions = {}
        for heading in headings:
            heading_positions[heading["line_number"]] = heading

        # Split content into sections
        current_section: list[str] = []
        current_heading = None
        current_heading_line = 0

        for i, line in enumerate(lines):
            # Check if this line is a heading
            heading_match = None
            for heading in headings:
                if heading["line_number"] == i + 1:
                    heading_match = heading
                    break

            if heading_match:
                # If we have a previous section, save it
                if current_section and current_heading:
                    chunk_content = "\n".join(current_section)
                    chunks.append(
                        {
                            "heading_path": current_heading["heading_path"],
                            "heading_level": current_heading["heading_level"],
                            "section_title": current_heading["heading_title"],
                            "content": chunk_content,
                            "tags": [],
                            "token_count": len(chunk_content.split()),
                            "anchor": f"heading-{current_heading_line}",
                        },
                    )

                # Start new section
                current_section = [line]
                current_heading = heading_match
                current_heading_line = i + 1
            else:
                # Add line to current section
                current_section.append(line)

        # Save the last section
        if current_section and current_heading:
            chunk_content = "\n".join(current_section)
            chunks.append(
                {
                    "heading_path": current_heading["heading_path"],
                    "heading_level": current_heading["heading_level"],
                    "section_title": current_heading["heading_title"],
                    "content": chunk_content,
                    "tags": [],
                    "token_count": len(chunk_content.split()),
                    "anchor": f"heading-{current_heading_line}",
                },
            )

        return chunks

    def _normalize_content(self, content: str) -> str:
        """Normalize content for FTS search."""
        # Simple normalization - in a real implementation, this would use
        # language-specific normalization (e.g., Sudachi for Japanese)
        return content.lower().strip()

    def get_chunk(self, chunk_id: int) -> dict | None:
        """Get a chunk by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT chunk_id, doc_id, heading_path, heading_level, section_title,
                           tags, token_count, char_count, content, normalized_content,
                           anchor, chunk_order
                    FROM md_chunks
                    WHERE chunk_id = ?
                """,
                    (chunk_id,),
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "chunk_id": row[0],
                        "doc_id": row[1],
                        "heading_path": row[2],
                        "heading_level": row[3],
                        "section_title": row[4],
                        "tags": orjson.loads(row[5]) if row[5] else [],
                        "token_count": row[6],
                        "char_count": row[7],
                        "content": row[8],
                        "normalized_content": row[9],
                        "anchor": row[10],
                        "chunk_order": row[11],
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting chunk {chunk_id}: {e}")
            return None

    def refresh_paths(self, paths: list[str]) -> list[str]:
        """Refresh the index for a list of paths."""
        # This is a simplified implementation - in a real implementation,
        # this would check for changes and update only modified files
        return self.index_paths(paths)

    def get_stats(self) -> dict:
        """Get statistics about the index."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM md_documents
                """)
                doc_count = cursor.fetchone()[0]

                cursor = conn.execute("""
                    SELECT COUNT(*) FROM md_chunks
                """)
                chunk_count = cursor.fetchone()[0]

                cursor = conn.execute("""
                    SELECT MAX(updated_at) FROM md_documents
                """)
                latest_update = cursor.fetchone()[0] or "Never"

                # Get FTS table size
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM md_chunks_fts
                """)
                fts_size = cursor.fetchone()[0]

                return {
                    "document_count": doc_count,
                    "chunk_count": chunk_count,
                    "latest_update": latest_update,
                    "fts_size": fts_size,
                }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {
                "document_count": 0,
                "chunk_count": 0,
                "latest_update": "Never",
                "fts_size": 0,
            }

    def grep_chunks(self, pattern: str, paths: list[str] | None = None) -> list[dict]:
        """Search chunks with a regex pattern."""
        try:
            # This is a simplified implementation - in a real implementation,
            # this would use the FTS table with regex support
            results = []
            with sqlite3.connect(self.db_path) as conn:
                if paths:
                    # Filter by specific paths
                    placeholders = ",".join("?" * len(paths))
                    cursor = conn.execute(
                        f"""
                        SELECT c.chunk_id, d.source_path, c.heading_path, c.content
                        FROM md_chunks c
                        JOIN md_documents d ON c.doc_id = d.doc_id
                        WHERE d.source_path IN ({placeholders})
                    """,
                        paths,
                    )
                else:
                    # Search all chunks
                    cursor = conn.execute("""
                        SELECT c.chunk_id, d.source_path, c.heading_path, c.content
                        FROM md_chunks c
                        JOIN md_documents d ON c.doc_id = d.doc_id
                    """)

                for row in cursor.fetchall():
                    chunk_id, source_path, heading_path, content = row
                    if pattern in content:
                        results.append(
                            {
                                "chunk_id": chunk_id,
                                "source_path": source_path,
                                "heading_path": heading_path,
                                "content": content[:100] + "..."
                                if len(content) > 100
                                else content,
                            },
                        )
            return results
        except Exception as e:
            logger.error(f"Error in grep_chunks: {e}")
            return []
