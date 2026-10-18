#!/usr/bin/env python3
"""scripts/mcp_servers/mdq/indexer.py

Indexing logic for Markdown files — writes to SQLite documents/chunks tables.
"""

from __future__ import annotations

import dataclasses
import fnmatch
import hashlib
import logging
import sqlite3
import time
from collections.abc import Awaitable
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


@dataclasses.dataclass
class _PathTally:
    """Mutable per-path counters for one index_paths() or refresh_paths() run.

    The counters are updated as each path is processed, so a failure partway through a
    directory keeps the counts already recorded for the files before it.
    """

    indexed: int = 0
    skipped: int = 0
    failed: int = 0


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


async def _tally_indexing(
    coro: Awaitable[None], path_str: str, tally: _PathTally
) -> None:
    """Await one indexing call and tally its outcome.

    The caller has already created coro, so a failure records one failed_count and the
    batch moves on to the next path.
    """
    try:
        await coro
    except Exception as e:  # noqa: BLE001 — a single path's indexing failure must not abort the batch; record it and continue
        logger.error("Failed to index %s: %s", path_str, e)
        tally.failed += 1
    else:
        tally.indexed += 1


async def _index_one_path(
    service: MdqService, path_str: str, tally: _PathTally
) -> None:
    """Validate and index one requested path, tallying what it produced."""
    p = Path(path_str)
    if not p.exists():
        logger.warning("Path does not exist: %s", path_str)
        tally.skipped += 1
        return
    if not authorize_path(p, service.allowed_dirs):
        raise MdqAuthorizationError(
            f"Access denied: {path_str} is outside allowed directories"
        )
    if p.is_file() and p.suffix == ".md":
        await _tally_indexing(_index_single_file(service, p), path_str, tally)
    elif p.is_dir():
        await _tally_indexing(_index_directory(service, p), path_str, tally)
    else:
        logger.warning("Skipping non-Markdown path: %s", path_str)
        tally.skipped += 1


async def index_paths(
    service: MdqService, req: IndexPathsRequest
) -> tuple[str, IndexPathsMetadata]:
    """Index a set of paths into the in-process SQLite DB."""
    logger.info("Indexing paths: %s", req.paths)
    t0 = time.perf_counter()
    tally = _PathTally()
    for path_str in req.paths:
        await _index_one_path(service, path_str, tally)
    duration_ms = (time.perf_counter() - t0) * 1000
    return "Indexing complete", IndexPathsMetadata(
        input_path_count=len(req.paths),
        indexed_count=tally.indexed,
        skipped_count=tally.skipped,
        failed_count=tally.failed,
        duration_ms=duration_ms,
    )


def _load_index_state(conn: sqlite3.Connection) -> dict[str, str]:
    """Load current index_state key/value records for staleness comparison."""
    state_rows = conn.execute("SELECT key, value FROM index_state").fetchall()
    current_state: dict[str, str] = {}
    for row in state_rows:
        current_state[row["key"]] = row["value"]
    return current_state


def _compute_dirs_to_scan(paths: list[str]) -> set[Path]:
    """Determine which directories to scan for deletion detection."""
    dirs_to_scan: set[Path] = set()
    for path_str in paths:
        p = Path(path_str)
        if p.is_dir():
            dirs_to_scan.add(p)
        elif p.is_file():
            dirs_to_scan.add(p.parent)
    return dirs_to_scan


def _detect_deleted_files(
    service: MdqService,
    conn: sqlite3.Connection,
    current_state: dict[str, str],
    dirs_to_scan: set[Path],
) -> int:
    """Detect files removed from the filesystem and delete their index entries.

    Returns the number of files removed from the index.
    """
    deleted_count = 0
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
        except Exception as e:  # noqa: BLE001 — a single directory's deletion scan failure must not abort the rest of the refresh
            logger.error("Failed to scan for deleted files in %s: %s", dir_path, e)
    return deleted_count


async def _reindex_forced(service: MdqService, path: Path, path_str: str) -> int:
    """Force mode: re-index one path regardless of index_state.

    Returns 1 when something was indexed. A directory counts as one indexed path even
    when it holds several files, which is not how incremental mode counts it.
    """
    if path.is_file() and path.suffix == ".md":
        await _index_single_file(service, path)
        return 1
    if path.is_dir():
        if _iter_indexable_files(service, path):
            await _index_directory(service, path)
            return 1
        logger.info("No indexable files found in directory: %s", path_str)
        return 0
    logger.warning("Path is not a file or directory: %s", path_str)
    return 0


async def _reindex_forced_path(
    service: MdqService, path: Path, path_str: str, tally: _PathTally
) -> None:
    """Force mode for one requested path."""
    try:
        tally.indexed += await _reindex_forced(service, path, path_str)
    except Exception as e:  # noqa: BLE001 — a single path's forced re-index failure must not abort the batch; record it and continue
        logger.error("Failed to index %s: %s", path_str, e)
        tally.failed += 1


async def _refresh_changed_file(
    service: MdqService,
    conn: sqlite3.Connection,
    current_state: dict[str, str],
    file_path: Path,
) -> bool:
    """Re-index one file and record its mtime in index_state.

    Returns False when index_state already holds this file's mtime, in which case
    nothing is read or written. index_state is only updated after a successful re-index,
    and current_state is never refreshed, so a path listed twice in one request is
    re-indexed twice.
    """
    state_key = f"mtime:{str(file_path)}"
    current_mtime = str(file_path.stat().st_mtime_ns)
    if current_state.get(state_key) == current_mtime:
        return False
    await _index_single_file(service, file_path)
    conn.execute(
        "INSERT OR REPLACE INTO index_state (key, value) VALUES (?, ?)",
        (state_key, current_mtime),
    )
    conn.commit()
    return True


async def _refresh_file_path(
    service: MdqService,
    conn: sqlite3.Connection,
    current_state: dict[str, str],
    path: Path,
    path_str: str,
    tally: _PathTally,
) -> None:
    """Incremental mode for one Markdown file."""
    try:
        if await _refresh_changed_file(service, conn, current_state, path):
            tally.indexed += 1
        else:
            tally.skipped += 1
    except Exception as e:  # noqa: BLE001 — a single file's incremental refresh failure must not abort the batch; record it and continue
        logger.error("Failed to refresh %s: %s", path_str, e)
        tally.failed += 1


async def _refresh_directory_path(
    service: MdqService,
    conn: sqlite3.Connection,
    current_state: dict[str, str],
    path: Path,
    path_str: str,
    tally: _PathTally,
) -> None:
    """Incremental mode for one directory: every indexable file under it.

    The try/except wraps the whole loop, so a failure on one file stops the remaining
    files in this directory while keeping the counts already recorded for them.
    """
    try:
        for md_file in _iter_indexable_files(service, path):
            if await _refresh_changed_file(service, conn, current_state, md_file):
                tally.indexed += 1
            else:
                tally.skipped += 1
    except Exception as e:  # noqa: BLE001 — a single directory's incremental refresh failure must not abort the batch; record it and continue
        logger.error("Failed to refresh directory %s: %s", path_str, e)
        tally.failed += 1


async def _refresh_one_path(
    service: MdqService,
    conn: sqlite3.Connection,
    current_state: dict[str, str],
    path_str: str,
    *,
    force: bool,
    tally: _PathTally,
) -> None:
    """Validate and refresh one requested path.

    A path that is neither a Markdown file nor a directory is not counted by any
    counter in incremental mode.
    """
    p = Path(path_str)
    if not p.exists():
        logger.warning("Path does not exist: %s", path_str)
        return
    if not authorize_path(p, service.allowed_dirs):
        raise MdqAuthorizationError(
            f"Access denied: {path_str} is outside allowed directories"
        )
    if force:
        await _reindex_forced_path(service, p, path_str, tally)
    elif p.is_file() and p.suffix == ".md":
        await _refresh_file_path(service, conn, current_state, p, path_str, tally)
    elif p.is_dir():
        await _refresh_directory_path(service, conn, current_state, p, path_str, tally)


async def refresh_paths(
    service: MdqService, req: RefreshIndexRequest
) -> RefreshSummary:
    """Incrementally refresh the index for a set of paths.

    Returns structured summary with indexed_count, skipped_count, deleted_count,
    failed_count, and elapsed_seconds.
    """
    start = time.time()
    tally = _PathTally()

    conn = service._get_db_connection()
    try:
        # Load current index_state records for tracking
        current_state = _load_index_state(conn)

        # Determine which directories to scan for deletion detection
        dirs_to_scan = _compute_dirs_to_scan(req.paths)

        # Index or skip each requested path
        for path_str in req.paths:
            await _refresh_one_path(
                service, conn, current_state, path_str, force=req.force, tally=tally
            )

        # Detect deleted files within scanned directories
        deleted_count = _detect_deleted_files(
            service, conn, current_state, dirs_to_scan
        )

        elapsed = time.time() - start
        return {
            "indexed_count": tally.indexed,
            "skipped_count": tally.skipped,
            "deleted_count": deleted_count,
            "failed_count": tally.failed,
            "elapsed_seconds": round(elapsed, 3),
        }
    finally:
        conn.close()
