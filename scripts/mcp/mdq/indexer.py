#!/usr/bin/env python3
"""mcp/mdq/indexer.py
Indexing logic for Markdown files — writes to SQLite documents/chunks tables.
"""

from __future__ import annotations

import hashlib
import logging
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

from mcp.mdq.auth import authorize_path
from mcp.mdq.models import IndexPathsRequest, ParsedSection, ParseMarkdownRequest, RefreshIndexRequest
from mcp.mdq.parser import parse_markdown

if TYPE_CHECKING:
    from mcp.mdq.service import MdqService

logger = logging.getLogger(__name__)


async def _index_single_file(service: MdqService, path: Path) -> None:
    """Index a single Markdown file into the service DB."""
    logger.info("Indexing file: %s", path)

    try:
        sections = await parse_markdown(service, ParseMarkdownRequest(path=str(path)))
    except FileNotFoundError as e:
        logger.error("Failed to parse %s: %s", path, e)
        return

    if not sections:
        logger.info("No sections found in %s", path)
        return

    conn = service._get_db_connection()
    try:
        doc_id = hashlib.sha256(str(path).encode()).hexdigest()
        now = path.stat().st_mtime_ns

        # Delete old chunks for this document
        conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))

        for section in sections:
            content_hash = hashlib.sha256(section["content"].encode()).hexdigest()
            normalized_content = " ".join(section["content"].split())
            char_count = len(section["content"])

            # Upsert document
            conn.execute(
                "INSERT OR REPLACE INTO documents (doc_id, source_path, mtime_ns, size_bytes, content_hash, indexed_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    doc_id,
                    str(path),
                    now,
                    path.stat().st_size,
                    content_hash,
                    path.stat().st_mtime,
                ),
            )

            # Insert chunk with new schema
            conn.execute(
                "INSERT INTO chunks (chunk_id, doc_id, source_path, heading, heading_path, heading_level, ordinal, content, normalized_content, start_line, end_line, char_count, token_count, content_hash, tags_json, indexed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    hashlib.sha256(
                        f"{doc_id}:{section['heading']}:{section['start_line']}".encode()
                    ).hexdigest(),
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
                    None,
                    content_hash,
                    "",
                    path.stat().st_mtime,
                ),
            )

            # Generate summaries for large chunks if enabled
            if service.summary_cache_enabled:
                _generate_summaries(service, conn, doc_id, sections)

            conn.commit()
    except sqlite3.Error as e:
        logger.error("Failed to write chunks for %s: %s", path, e)
    finally:
        conn.close()


async def _index_directory(service: MdqService, path: Path) -> None:
    """Recursively index all Markdown files under a directory."""
    for child in sorted(path.rglob("*.md")):
        if child.is_file():
            await _index_single_file(service, child)


async def index_paths(service: MdqService, req: IndexPathsRequest) -> str:
    """Index a set of paths into the in-process SQLite DB."""
    logger.info("Indexing paths: %s", req.paths)
    for path_str in req.paths:
        p = Path(path_str)
        if not p.exists():
            logger.warning("Path does not exist: %s", path_str)
            continue
        if not authorize_path(p, service.allowed_dirs):
            logger.warning("Path denied: %s (outside allowed dirs)", path_str)
            continue
        if p.is_file() and p.suffix == ".md":
            await _index_single_file(service, p)
        elif p.is_dir():
            await _index_directory(service, p)
        else:
            logger.warning("Skipping non-Markdown path: %s", path_str)
    return "Indexing complete"


async def refresh_paths(service: MdqService, req: RefreshIndexRequest) -> dict:
    """Incrementally refresh the index for a set of paths.

    Returns structured summary with indexed_count, skipped_count, deleted_count,
    failed_count, and elapsed_seconds.
    """
    import time  # noqa: PLC0415

    start = time.time()
    indexed_count = 0
    skipped_count = 0
    deleted_count = 0
    failed_count = 0

    conn = service._get_db_connection()
    try:
        # Load current index_state records for tracking
        state_rows = conn.execute("SELECT key, value FROM index_state").fetchall()
        current_state: dict[str, str] = {}
        for row in state_rows:
            current_state[row["key"]] = row["value"]

        # Track paths that exist on filesystem to detect deletions
        tracked_paths: set[str] = set()

        # Determine which directories to scan for deletion detection
        dirs_to_scan: set[Path] = set()
        for path_str in req.paths:
            p = Path(path_str)
            if p.is_dir():
                dirs_to_scan.add(p)
            elif p.is_file():
                dirs_to_scan.add(p.parent)

        # Index or skip each requested path
        for path_str in req.paths:
            p = Path(path_str)
            if not p.exists():
                logger.warning("Path does not exist: %s", path_str)
                continue
            if not authorize_path(p, service.allowed_dirs):
                logger.warning("Path denied: %s (outside allowed dirs)", path_str)
                continue

            # Force mode: always re-index
            if req.force:
                try:
                    if p.is_file() and p.suffix == ".md":
                        await _index_single_file(service, p)
                        indexed_count += 1
                    elif p.is_dir():
                        md_files = [f for f in sorted(p.rglob("*.md")) if f.is_file()]
                        if md_files:
                            await _index_directory(service, p)
                            indexed_count += 1
                        else:
                            logger.info("No .md files found in directory: %s", path_str)
                    else:
                        logger.warning("Path is not a file or directory: %s", path_str)
                except Exception as e:
                    logger.error("Failed to index %s: %s", path_str, e)
                    failed_count += 1
                continue

            # Incremental mode: compare metadata
            if p.is_file() and p.suffix == ".md":
                state_key = f"mtime:{str(p)}"
                current_mtime = str(p.stat().st_mtime_ns)
                if current_state.get(state_key) == current_mtime:
                    skipped_count += 1
                    continue

                # File changed — re-index
                try:
                    await _index_single_file(service, p)
                    # Update state after indexing
                    conn.execute(
                        "INSERT OR REPLACE INTO index_state (key, value) VALUES (?, ?)",
                        (state_key, current_mtime),
                    )
                    conn.commit()
                    indexed_count += 1
                except Exception as e:
                    logger.error("Failed to refresh %s: %s", path_str, e)
                    failed_count += 1

            elif p.is_dir():
                # For directories, scan for changes in all .md files
                try:
                    md_files = [f for f in sorted(p.rglob("*.md")) if f.is_file()]
                    for md_file in md_files:
                        state_key = f"mtime:{str(md_file)}"
                        current_mtime = str(md_file.stat().st_mtime_ns)
                        if current_state.get(state_key) == current_mtime:
                            skipped_count += 1
                            continue

                        # File changed — re-index
                        await _index_single_file(service, md_file)
                        conn.execute(
                            "INSERT OR REPLACE INTO index_state (key, value) VALUES (?, ?)",
                            (state_key, current_mtime),
                        )
                        conn.commit()
                        indexed_count += 1
                except Exception as e:
                    logger.error("Failed to refresh directory %s: %s", path_str, e)
                    failed_count += 1

            tracked_paths.add(str(p))

        # Detect deleted files within scanned directories
        for dir_path in dirs_to_scan:
            try:
                current_md_files = set(
                    str(f) for f in dir_path.rglob("*.md") if f.is_file()
                )
                for path_str_key, mtime_val in list(current_state.items()):
                    if not path_str_key.startswith("mtime:"):
                        continue
                    file_path = path_str_key[6:]
                    if (
                        file_path not in current_md_files
                        and dir_path in Path(file_path).parents
                    ):
                        # File was deleted — remove from index
                        _delete_file_from_index(service, conn, Path(file_path))
                        deleted_count += 1
            except Exception as e:
                logger.error("Failed to scan for deleted files in %s: %s", dir_path, e)

        elapsed = time.time() - start
        return {
            "indexed_count": indexed_count,
            "skipped_count": skipped_count,
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "elapsed_seconds": round(elapsed, 3),
        }
    finally:
        conn.close()


def _delete_file_from_index(
    service: MdqService, conn: sqlite3.Connection, path: Path
) -> None:
    """Remove a file's chunks and index_state records from the database."""
    import hashlib  # noqa: PLC0415

    doc_id = hashlib.sha256(str(path).encode()).hexdigest()
    # Drop FTS5 triggers before deleting chunks to avoid SQL logic error
    conn.execute("DROP TRIGGER IF EXISTS chunks_ad")
    conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
    conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
    conn.execute(
        "DELETE FROM index_state WHERE key LIKE ?",
        (f"mtime:{str(path)}%",),
    )
    # Recreate FTS5 triggers
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks "
        "BEGIN DELETE FROM chunks_fts WHERE rowid = old.rowid; END"
    )
    conn.commit()


def _generate_summaries(
    service: MdqService, conn: sqlite3.Connection, doc_id: str, sections: list[ParsedSection]
) -> None:
    """Generate summaries for large chunks if enabled."""
    for section in sections:
        content_hash = hashlib.sha256(section["content"].encode()).hexdigest()
        if len(section["content"]) > service.summary_threshold:
            conn.execute(
                "INSERT OR REPLACE INTO chunk_summaries (chunk_id, summary, summary_model, content_hash, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                (
                    hashlib.sha256(
                        f"{doc_id}:{section['heading']}:{section['start_line']}".encode()
                    ).hexdigest(),
                    section["content"][: service.summary_threshold],
                    service.summary_model,
                    content_hash,
                ),
            )
