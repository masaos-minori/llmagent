#!/usr/bin/env python3
"""scripts/mcp_servers/mdq/index_write.py

Write-side SQL for the mdq indexer — one document's rows, replaced atomically.

Mirrors index_delete.py: index_delete owns removing a file's rows, this module owns
replacing them inside one BEGIN IMMEDIATE transaction. Chunk ID generation and the
token estimate that fill the chunk columns live here too. The caller
(mcp_servers.mdq.indexer) owns the connection: it rolls back on a sqlite3.Error and
closes it.

Dependency direction: index_write → models
Import from here:  from mcp_servers.mdq.index_write import write_document_chunks
"""

from __future__ import annotations

import hashlib
import sqlite3
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp_servers.mdq.mdq_models import ParsedSection
    from mcp_servers.mdq.mdq_service import MdqService


def generate_chunk_id(
    normalized_path: str, heading_path: str, ordinal: int, content_hash: str
) -> str:
    """Generate a stable chunk ID from normalized path, heading path, ordinal, and content hash.

    Stable across re-indexing of unchanged content. Uses | as delimiter to reduce
    collision risk with paths containing colons.
    normalized_path should be Path(path).resolve().as_posix().
    """
    return hashlib.sha256(
        f"{normalized_path}|{heading_path}|{ordinal}|{content_hash}".encode()
    ).hexdigest()


def _estimate_token_count(text: str) -> int:
    """Approximate token count via a chars-per-token-~4 heuristic.

    This is not an exact tokenizer count -- no live tokenizer endpoint is available
    inside mcp_servers/mdq without adding a new network dependency. Consistent in
    spirit with shared/token_estimation.py's own ratio-based approach, but without
    its chat-category/network dependencies.
    """
    return max(1, len(text) // 4)


def write_document_chunks(
    conn: sqlite3.Connection,
    service: MdqService,
    path: Path,
    sections: list[ParsedSection],
    tags_json: str,
) -> None:
    """Replace one document's rows in a single BEGIN IMMEDIATE transaction.

    The caller owns the connection: it rolls back on a sqlite3.Error and closes it.
    """
    doc_id = hashlib.sha256(str(path).encode()).hexdigest()
    now = path.stat().st_mtime_ns
    indexed_at = time.time()
    normalized_path = path.resolve().as_posix()
    file_content_hash = hashlib.sha256((str(path) + str(now)).encode()).hexdigest()

    conn.execute("BEGIN IMMEDIATE")
    # Delete old chunks and upsert document atomically
    conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
    conn.execute(
        "INSERT OR REPLACE INTO documents (doc_id, source_path, mtime_ns, size_bytes, content_hash, indexed_at) VALUES (?, ?, ?, ?, ?, ?)",
        (
            doc_id,
            str(path),
            now,
            path.stat().st_size,
            file_content_hash,
            indexed_at,
        ),
    )

    for section in sections:
        if len(section["content"]) > service.max_chunk_chars:
            section["content"] = section["content"][: service.max_chunk_chars]
        content_hash = hashlib.sha256(section["content"].encode()).hexdigest()
        normalized_content = " ".join(section["content"].split())
        char_count = len(section["content"])
        token_count = _estimate_token_count(section["content"])
        chunk_id = generate_chunk_id(
            normalized_path,
            section.get("heading_path", ""),
            section.get("ordinal", 0),
            content_hash,
        )

        # Insert chunk with new schema
        conn.execute(
            "INSERT INTO chunks (chunk_id, doc_id, source_path, heading, heading_path, heading_level, ordinal, content, normalized_content, start_line, end_line, char_count, token_count, content_hash, tags_json, indexed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                chunk_id,
                doc_id,
                str(path),
                section["heading"],
                section.get("heading_path", ""),
                section.get("heading_level", 0),
                section.get("ordinal", 0),
                section["content"],
                normalized_content,
                section["start_line"],
                section["end_line"],
                char_count,
                token_count,
                content_hash,
                tags_json,
                indexed_at,
            ),
        )

    conn.execute("COMMIT")
