#!/usr/bin/env python3
"""scripts/mcp_servers/mdq/indexer.py

Indexing logic for Markdown files — writes to SQLite documents/chunks tables.
"""

from __future__ import annotations

import dataclasses
import logging
import sqlite3
import time
from collections.abc import Awaitable
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

from shared.json_utils import dumps as _json_dumps

from mcp_servers.mdq.auth import authorize_path
from mcp_servers.mdq.index_delete import delete_file_from_index
from mcp_servers.mdq.index_scan import iter_indexable_files
from mcp_servers.mdq.index_write import write_document_chunks
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

# One wording for "this requested path is not something the indexer can read", shared by
# index_paths() and both refresh modes so the same input reports the same way.
_NON_MARKDOWN_PATH_WARNING = "Skipping non-Markdown path: %s"


class RefreshSummary(TypedDict):
    """Summary of an incremental index refresh operation."""

    indexed_count: int
    skipped_count: int
    deleted_count: int
    failed_count: int
    elapsed_seconds: float


@dataclasses.dataclass
class _PathTally:
    """Mutable counters for one index_paths() or refresh_paths() run.

    The counters are updated as each path is processed, so a failure partway through a
    directory keeps the counts already recorded for the files before it. deleted is only
    ever incremented by refresh_paths(), which reports it as deleted_count.
    """

    indexed: int = 0
    skipped: int = 0
    failed: int = 0
    deleted: int = 0


def _rollback_quietly(conn: sqlite3.Connection) -> None:
    """Roll back an open transaction, ignoring a second failure."""
    try:
        conn.execute("ROLLBACK")
    except sqlite3.Error:
        pass


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
        write_document_chunks(conn, service, path, sections, tags_json)
    except sqlite3.Error as e:
        _rollback_quietly(conn)
        logger.error("Failed to write chunks for %s: %s", path, e)
    finally:
        conn.close()


async def _index_directory(service: MdqService, path: Path) -> None:
    """Recursively index all indexable files under a directory."""
    for child in iter_indexable_files(service, path):
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


def _is_indexable_path(path: Path) -> bool:
    """True when the indexer can read this path: a Markdown file or a directory."""
    return (path.is_file() and path.suffix == ".md") or path.is_dir()


def _validated_indexable_path(
    service: MdqService, path_str: str, tally: _PathTally
) -> Path | None:
    """Return the path to process, or None when it is tallied as skipped.

    Shared by index_paths() and both refresh modes so the same input is counted the
    same way. A path outside allowed_dirs raises instead of being skipped: that is an
    authorization failure, not an indexable-path failure.
    """
    p = Path(path_str)
    if not p.exists():
        logger.warning("Path does not exist: %s", path_str)
        tally.skipped += 1
        return None
    if not authorize_path(p, service.allowed_dirs):
        raise MdqAuthorizationError(
            f"Access denied: {path_str} is outside allowed directories"
        )
    if not _is_indexable_path(p):
        logger.warning(_NON_MARKDOWN_PATH_WARNING, path_str)
        tally.skipped += 1
        return None
    return p


async def _index_one_path(
    service: MdqService, path_str: str, tally: _PathTally
) -> None:
    """Validate and index one requested path, tallying what it produced."""
    p = _validated_indexable_path(service, path_str, tally)
    if p is None:
        return
    if p.is_file():
        await _tally_indexing(_index_single_file(service, p), path_str, tally)
    else:
        await _tally_indexing(_index_directory(service, p), path_str, tally)


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


def _is_stale_index_key(
    path_str_key: str, current_md_files: set[str], dir_path: Path
) -> bool:
    """True when an index_state mtime key names a file under dir_path that is gone.

    Keys that are not `mtime:` entries are not file records and never match.
    """
    if not path_str_key.startswith("mtime:"):
        return False
    file_path = path_str_key[6:]
    return file_path not in current_md_files and dir_path in Path(file_path).parents


def _delete_stale_entries(
    service: MdqService,
    conn: sqlite3.Connection,
    current_state: dict[str, str],
    dir_path: Path,
    tally: _PathTally,
) -> None:
    """Delete index entries for files under dir_path that are no longer on disk.

    tally.deleted counts what was removed. A failure partway through the directory keeps
    what it already removed and records one tally.failed, so a caller can tell "nothing
    was deleted" apart from "the scan did not run".
    """
    try:
        current_md_files = {str(f) for f in iter_indexable_files(service, dir_path)}
        for path_str_key in list(current_state):
            if not _is_stale_index_key(path_str_key, current_md_files, dir_path):
                continue
            # File was deleted — remove from index
            delete_file_from_index(service, conn, Path(path_str_key[6:]))
            tally.deleted += 1
    except Exception as e:  # noqa: BLE001 — a single directory's deletion scan failure must not abort the rest of the refresh
        logger.error("Failed to scan for deleted files in %s: %s", dir_path, e)
        tally.failed += 1


def _detect_deleted_files(
    service: MdqService,
    conn: sqlite3.Connection,
    current_state: dict[str, str],
    dirs_to_scan: set[Path],
    tally: _PathTally,
) -> None:
    """Detect files removed from the filesystem and delete their index entries.

    Each directory is scanned independently, so one directory's failure does not stop the
    others.
    """
    for dir_path in dirs_to_scan:
        _delete_stale_entries(service, conn, current_state, dir_path, tally)


async def _reindex_forced(service: MdqService, path: Path, path_str: str) -> int:
    """Force mode: re-index one path regardless of index_state.

    Callers gate on _validated_indexable_path(), so path is a Markdown file or a
    directory here.
    Returns how many files were indexed: a directory contributes one per indexable file,
    which is the unit incremental mode counts in.
    """
    if path.is_file():
        await _index_single_file(service, path)
        return 1
    indexable_files = iter_indexable_files(service, path)
    if not indexable_files:
        logger.info("No indexable files found in directory: %s", path_str)
        return 0
    await _index_directory(service, path)
    return len(indexable_files)


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
    """Re-index one file and record its mtime in index_state and in current_state.

    Returns False when index_state already holds this file's mtime, in which case nothing
    is read or written. Both copies are updated only after a successful re-index, so a
    path listed twice in one request is indexed once and skipped the second time.
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
    current_state[state_key] = current_mtime
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
        for md_file in iter_indexable_files(service, path):
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

    A path that does not exist, or that is neither a Markdown file nor a directory, is
    counted as skipped in both modes, the same way index_paths() counts it: both modes
    go through _validated_indexable_path().
    """
    p = _validated_indexable_path(service, path_str, tally)
    if p is None:
        return
    if force:
        await _reindex_forced_path(service, p, path_str, tally)
    elif p.is_file():
        await _refresh_file_path(service, conn, current_state, p, path_str, tally)
    else:
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
        _detect_deleted_files(service, conn, current_state, dirs_to_scan, tally)

        elapsed = time.time() - start
        return {
            "indexed_count": tally.indexed,
            "skipped_count": tally.skipped,
            "deleted_count": tally.deleted,
            "failed_count": tally.failed,
            "elapsed_seconds": round(elapsed, 3),
        }
    finally:
        conn.close()
