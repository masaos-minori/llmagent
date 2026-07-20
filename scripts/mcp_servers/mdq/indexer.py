#!/usr/bin/env python3
"""mcp_servers/mdq/indexer.py

Indexing logic for Markdown files — writes to SQLite documents/chunks tables.
"""

from __future__ import annotations

import fnmatch
import hashlib
import logging
import sqlite3
import time
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

from shared.json_utils import dumps as _json_dumps

from mcp_servers.mdq.auth import authorize_path
from mcp_servers.mdq.index_delete import delete_file_from_index
from mcp_servers.mdq.mdq_models import (
    IndexPathsMetadata,
    IndexPathsRequest,
    MdqAuthorizationError,
    ParseMarkdownRequest,
    RefreshIndexRequest,
)
from mcp_servers.mdq.parser import parse_markdown

if TYPE_CHECKING:
    from mcp_servers.mdq.mdq_service import MdqService

logger = logging.getLogger(__name__)


def _matches_any_glob(rel_posix: str, patterns: list[str]) -> bool:
    """Return True if rel_posix matches any of patterns, at any path depth.

    pathlib.Path.match() was tried first and rejected: it right-aligns only
    as many path segments as the pattern has, so ".git/**" (2 segments) does
    not match ".git/objects/pack/file.pack" (4 segments) -- verified
    empirically against this module's default exclude_globs value
    ([".git/**", "__pycache__/**"]) on a real directory tree before choosing
    this implementation.

    fnmatch against the full relative path handles root-anchored occurrences
    (e.g. ".git/objects/pack/file.pack" against ".git/**") but still misses
    nested occurrences that don't start at the path root (e.g.
    "src/__pycache__/nested/a.pyc" against "__pycache__/**"). To catch both,
    fnmatch is applied against every path suffix (the substring starting at
    each path component), not just the full path.
    """
    parts = rel_posix.split("/")
    for i in range(len(parts)):
        suffix = "/".join(parts[i:])
        if any(fnmatch.fnmatch(suffix, pattern) for pattern in patterns):
            return True
    return False


def _iter_indexable_files(service: MdqService, directory: Path) -> list[Path]:
    """Return indexable files under directory per service.include_globs/exclude_globs.

    Replaces hardcoded rglob("*.md") call sites so indexing honors the
    configured include_globs / exclude_globs (config/mdq_mcp_server.toml).
    """
    include_globs = service.include_globs
    exclude_globs = service.exclude_globs
    matched: dict[str, Path] = {}
    for pattern in include_globs:
        for f in directory.rglob(pattern):
            if not f.is_file():
                continue
            rel_posix = f.relative_to(directory).as_posix()
            if _matches_any_glob(rel_posix, exclude_globs):
                continue
            matched[str(f)] = f
    return sorted(matched.values())


class RefreshSummary(TypedDict):
    """Summary of an incremental index refresh operation."""

    indexed_count: int
    skipped_count: int
    deleted_count: int
    failed_count: int
    elapsed_seconds: float


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


async def _index_single_file(service: MdqService, path: Path) -> None:
    """Index a single Markdown file into the service DB."""
    logger.info("Indexing file: %s", path)

    file_size = path.stat().st_size
    if file_size > service.max_file_chars:
        logger.warning(
            "Skipping %s: file size %d exceeds max_file_chars=%d",
            path,
            file_size,
            service.max_file_chars,
        )
        return

    try:
        sections, tags = await parse_markdown(
            service, ParseMarkdownRequest(path=str(path))
        )
    except FileNotFoundError as e:
        logger.error("Failed to parse %s: %s", path, e)
        return

    if not sections:
        logger.info("No sections found in %s", path)
        return

    tags_json = _json_dumps(tags)

    conn = service._get_db_connection()
    try:
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
    except sqlite3.Error as e:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        logger.error("Failed to write chunks for %s: %s", path, e)
    finally:
        conn.close()


async def _index_directory(service: MdqService, path: Path) -> None:
    """Recursively index all indexable files under a directory."""
    for child in _iter_indexable_files(service, path):
        await _index_single_file(service, child)


async def index_paths(
    service: MdqService, req: IndexPathsRequest
) -> tuple[str, IndexPathsMetadata]:
    """Index a set of paths into the in-process SQLite DB."""
    logger.info("Indexing paths: %s", req.paths)
    t0 = time.perf_counter()
    indexed_count = skipped_count = failed_count = 0
    for path_str in req.paths:
        p = Path(path_str)
        if not p.exists():
            logger.warning("Path does not exist: %s", path_str)
            skipped_count += 1
            continue
        if not authorize_path(p, service.allowed_dirs):
            raise MdqAuthorizationError(
                f"Access denied: {path_str} is outside allowed directories"
            )
        if p.is_file() and p.suffix == ".md":
            try:
                await _index_single_file(service, p)
            except Exception as e:
                logger.error("Failed to index %s: %s", path_str, e)
                failed_count += 1
            else:
                indexed_count += 1
        elif p.is_dir():
            try:
                await _index_directory(service, p)
            except Exception as e:
                logger.error("Failed to index %s: %s", path_str, e)
                failed_count += 1
            else:
                indexed_count += 1
        else:
            logger.warning("Skipping non-Markdown path: %s", path_str)
            skipped_count += 1
    duration_ms = (time.perf_counter() - t0) * 1000
    return "Indexing complete", IndexPathsMetadata(
        input_path_count=len(req.paths),
        indexed_count=indexed_count,
        skipped_count=skipped_count,
        failed_count=failed_count,
        duration_ms=duration_ms,
    )


async def refresh_paths(
    service: MdqService, req: RefreshIndexRequest
) -> RefreshSummary:
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
                raise MdqAuthorizationError(
                    f"Access denied: {path_str} is outside allowed directories"
                )

            # Force mode: always re-index
            if req.force:
                try:
                    if p.is_file() and p.suffix == ".md":
                        await _index_single_file(service, p)
                        indexed_count += 1
                    elif p.is_dir():
                        md_files = _iter_indexable_files(service, p)
                        if md_files:
                            await _index_directory(service, p)
                            indexed_count += 1
                        else:
                            logger.info(
                                "No indexable files found in directory: %s", path_str
                            )
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
                # For directories, scan for changes in all indexable files
                try:
                    md_files = _iter_indexable_files(service, p)
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
                current_md_files = {
                    str(f) for f in _iter_indexable_files(service, dir_path)
                }
                for path_str_key, mtime_val in list(current_state.items()):
                    if not path_str_key.startswith("mtime:"):
                        continue
                    file_path = path_str_key[6:]
                    if (
                        file_path not in current_md_files
                        and dir_path in Path(file_path).parents
                    ):
                        # File was deleted — remove from index
                        delete_file_from_index(service, conn, Path(file_path))
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
