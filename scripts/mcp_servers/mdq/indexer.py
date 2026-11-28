#!/usr/bin/env python3
"""scripts/mcp_servers/mdq/indexer.py

Indexing logic for Markdown files — writes to SQLite documents/chunks tables.
"""

from __future__ import annotations

import dataclasses
import logging
import sqlite3
import time
from collections.abc import Awaitable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

from shared.json_utils import dumps as _json_dumps

from mcp_servers.audit import path_identifier
from mcp_servers.mdq.auth import authorize_path
from mcp_servers.mdq.index_delete import delete_file_from_index
from mcp_servers.mdq.index_scan import iter_indexable_files
from mcp_servers.mdq.index_write import write_document_chunks
from mcp_servers.mdq.mdq_models import (
    FileOutcome,
    IndexPathsMetadata,
    IndexPathsRequest,
    MdqAuthorizationError,
    MdqServiceError,
    ParseMarkdownRequest,
    RefreshIndexRequest,
    outcome_text,
)
from mcp_servers.mdq.parser import parse_markdown

if TYPE_CHECKING:
    from mcp_servers.mdq.mdq_service import MdqService

logger = logging.getLogger(__name__)

# One wording for "this requested path is not something the indexer can read", shared by
# index_paths() and both refresh modes so the same input reports the same way.
_NON_MARKDOWN_PATH_WARNING = "Skipping non-Markdown path: %s"


class RefreshSummary(TypedDict):
    """Summary of an incremental index refresh operation.

    The original keys keep the meaning they have today; the four file-level keys name the
    unit a directory actually produces, so the same run reports the same file counts in
    both refresh modes (REQ-003). unchanged_file_count is the part of skipped_file_count
    that a refresh found unchanged, which is completed work rather than a skip to report.
    """

    indexed_count: int
    skipped_count: int
    deleted_count: int
    failed_count: int
    discovered_file_count: int
    committed_file_count: int
    skipped_file_count: int
    failed_file_count: int
    unchanged_file_count: int
    elapsed_seconds: float


@dataclasses.dataclass
class _PathTally:
    """Mutable counters for one index_paths() or refresh_paths() run.

    The first four counters keep the meaning the audit surface already reports (UNK-06);
    the four file-level counters count files, not paths. They update as each path is
    processed, so a failure partway through a directory keeps the counts already recorded.
    deleted is only ever incremented by refresh_paths(), as deleted_count.
    """

    indexed: int = 0
    skipped: int = 0
    failed: int = 0
    deleted: int = 0
    discovered_files: int = 0
    committed_files: int = 0
    skipped_files: int = 0
    failed_files: int = 0
    unchanged_files: int = 0


def _outcome_path(service: MdqService, path: Path) -> str:
    """Root-relative identifier for a DTO, so no absolute path enters an outcome record."""
    return path_identifier(str(path), service.allowed_dirs)


def _tally_file_outcome(tally: _PathTally, outcome: FileOutcome) -> None:
    """Count one file under the unit its status names (REQ-001).

    committed_files is the counter the outcome text and the all-failed decision read.
    unchanged_files is a sub-count of skipped_files: an unchanged file is a completed
    refresh, not a skip the outcome text reports as unfinished.
    """
    match outcome.status:
        case "indexed":
            tally.committed_files += 1
        case "failed":
            tally.failed_files += 1
        case "skipped_unchanged":
            tally.skipped_files += 1
            tally.unchanged_files += 1
        case _:
            tally.skipped_files += 1


def _tally_path_level(tally: _PathTally, outcomes: Sequence[FileOutcome]) -> None:
    """Roll one path's file outcomes up into the existing path-level counters.

    A directory counts once (UNK-06): indexed when any file committed, failed when every
    file failed, skipped when nothing committed.
    """
    if not outcomes:
        tally.skipped += 1
    elif all(outcome.status == "failed" for outcome in outcomes):
        tally.failed += 1
    elif any(outcome.status == "indexed" for outcome in outcomes):
        tally.indexed += 1
    else:
        tally.skipped += 1


def _all_files_failed(tally: _PathTally) -> bool:
    """True when the run recorded file failures and committed nothing (REQ-003).

    A run with no files at all — an empty directory, a nonexistent path — is a skip.
    """
    return tally.committed_files == 0 and tally.failed_files > 0


def _all_files_failed_error(tally: _PathTally) -> MdqServiceError:
    """Build the all-files-failed tool error from counts only, never from a path."""
    return MdqServiceError(
        f"Indexing failed: {tally.failed_files} of {tally.discovered_files} "
        "discovered files failed"
    )


def _rollback_quietly(conn: sqlite3.Connection) -> None:
    """Roll back an open transaction, ignoring a second failure."""
    try:
        conn.execute("ROLLBACK")
    except sqlite3.Error:
        pass


async def _index_single_file(service: MdqService, path: Path) -> FileOutcome:
    """Index one Markdown file and report what actually happened to it.

    The DTO is the only signal the callers tally from, so every branch returns one instead
    of returning `None` and letting the caller read "no exception" as success (REQ-001).

    The path is re-authorized and re-statted here rather than trusting the earlier scan
    decision: a file that disappeared or left the authorized roots between the scan and the
    read is reported as a file outcome instead of being indexed (REQ-005).
    """
    logger.info("Indexing file: %s", path)

    if not authorize_path(path, service.allowed_dirs):
        # The identifier is what an unauthorized path looks like in an outcome, so the
        # refusal text carries no absolute path either.
        raise MdqAuthorizationError(
            f"Access denied: {_outcome_path(service, path)} is outside allowed directories"
        )

    outcome_path = _outcome_path(service, path)

    try:
        file_size = path.stat().st_size
    except FileNotFoundError:
        logger.error("File disappeared before it could be read: %s", path)
        return FileOutcome(
            path=outcome_path, status="failed", reason_code="file_disappeared"
        )

    # The gate measures bytes on disk; character counts are a separate measure the DTO
    # carries, so a multi-byte file is not gated by its decoded length (REQ-004).
    if file_size > service.max_file_bytes:
        logger.warning(
            "Skipping %s: file size %d bytes exceeds max_file_bytes=%d",
            path,
            file_size,
            service.max_file_bytes,
        )
        return FileOutcome(
            path=outcome_path, status="skipped_size_limit", reason_code="size_limit"
        )

    try:
        sections, tags, frontmatter_warning = await parse_markdown(
            service, ParseMarkdownRequest(path=str(path))
        )
    except FileNotFoundError as e:
        logger.error("Failed to parse %s: %s", path, e)
        return FileOutcome(
            path=outcome_path, status="failed", reason_code="file_disappeared"
        )

    if not sections:
        logger.info("No sections found in %s", path)
        return FileOutcome(
            path=outcome_path,
            status="skipped_no_content",
            reason_code="no_content",
            **frontmatter_warning,
        )

    tags_json = _json_dumps(tags)

    conn = service._get_db_connection()
    try:
        write_document_chunks(conn, service, path, sections, tags_json)
    except sqlite3.Error as e:
        _rollback_quietly(conn)
        logger.error("Failed to write chunks for %s: %s", path, e)
        return FileOutcome(
            path=outcome_path, status="failed", reason_code="write_failure"
        )
    finally:
        conn.close()

    return FileOutcome(path=outcome_path, status="indexed", **frontmatter_warning)


async def _index_single_file_path(
    service: MdqService, path: Path, tally: _PathTally
) -> list[FileOutcome]:
    """Index one file and tally it as a discovered file before the call is awaited.

    Counting the file before the call is what keeps a file whose call raises counted as a
    failed file instead of dropping out of the counts (AC-1).
    """
    tally.discovered_files += 1
    try:
        outcome = await _index_single_file(service, path)
    except Exception:
        # The call-side failure is recorded here so the caller that logs the path-level
        # failure does not have to know how many files were already visited.
        tally.failed_files += 1
        raise
    _tally_file_outcome(tally, outcome)
    return [outcome]


async def _index_directory(
    service: MdqService, path: Path, tally: _PathTally
) -> list[FileOutcome]:
    """Recursively index all indexable files under a directory, one DTO per file.

    Every discovered file is reported, including the ones that were skipped or failed, so
    a directory is counted as the files it produced rather than as one indexed path
    (REQ-003). A file whose call raises aborts the rest of this directory, which is the
    behavior the refresh-mode characterization pins.
    """
    outcomes: list[FileOutcome] = []
    for child in iter_indexable_files(service, path):
        outcomes.extend(await _index_single_file_path(service, child, tally))
    return outcomes


async def _tally_indexing(
    coro: Awaitable[Sequence[FileOutcome]], path_str: str, tally: _PathTally
) -> None:
    """Await one requested path's indexing call and roll its outcomes up per path.

    The file-level counters are tallied where each file is processed, so a call that raises
    partway through a directory keeps the counts of the files it already visited and
    records one failed path here.
    """
    try:
        outcomes = await coro
    except Exception as e:  # noqa: BLE001 — a single path's indexing failure must not abort the batch; record it and continue
        logger.error("Failed to index %s: %s", path_str, e)
        tally.failed += 1
        return
    _tally_path_level(tally, outcomes)


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
    coro = (
        _index_single_file_path(service, p, tally)
        if p.is_file()
        else _index_directory(service, p, tally)
    )
    await _tally_indexing(coro, path_str, tally)


async def index_paths(
    service: MdqService, req: IndexPathsRequest
) -> tuple[str, IndexPathsMetadata]:
    """Index a set of paths into the in-process SQLite DB.

    A run in which every file failed reports the tool error rather than a text the caller
    would read as a completed run (REQ-003).
    """
    logger.info("Indexing paths: %s", req.paths)
    t0 = time.perf_counter()
    tally = _PathTally()
    for path_str in req.paths:
        await _index_one_path(service, path_str, tally)
    if _all_files_failed(tally):
        raise _all_files_failed_error(tally)
    duration_ms = (time.perf_counter() - t0) * 1000
    return (
        outcome_text(
            committed_files=tally.committed_files,
            discovered_files=tally.discovered_files,
            skipped_files=tally.skipped_files,
            failed_files=tally.failed_files,
            skipped_paths=tally.skipped,
            failed_paths=tally.failed,
        ),
        IndexPathsMetadata(
            input_path_count=len(req.paths),
            indexed_count=tally.indexed,
            skipped_count=tally.skipped,
            failed_count=tally.failed,
            discovered_file_count=tally.discovered_files,
            committed_file_count=tally.committed_files,
            skipped_file_count=tally.skipped_files,
            failed_file_count=tally.failed_files,
            duration_ms=duration_ms,
        ),
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


def _tally_path_level_from_status(tally: _PathTally, outcome: FileOutcome) -> None:
    """Count one file under the path-level counter its status names.

    Both refresh modes already count files at this level and keep doing so (UNK-06); only
    index mode rolls a directory up into one path entry. A skipped or failed file is never
    counted as indexed here either, which is what a swallowed write failure used to do
    (REQ-001).
    """
    if outcome.status == "indexed":
        tally.indexed += 1
    elif outcome.status == "failed":
        tally.failed += 1
    else:
        tally.skipped += 1


async def _reindex_forced(
    service: MdqService, path: Path, path_str: str, tally: _PathTally
) -> list[FileOutcome]:
    """Force mode: re-index one path regardless of index_state.

    Callers gate on _validated_indexable_path(), so path is a Markdown file or a
    directory here. Both modes report files as the unit: the returned list is one entry
    per file the path produced, with its status (REQ-003).
    """
    if path.is_file():
        return await _index_single_file_path(service, path, tally)
    outcomes = await _index_directory(service, path, tally)
    if not outcomes:
        logger.info("No indexable files found in directory: %s", path_str)
    return outcomes


async def _reindex_forced_path(
    service: MdqService, path: Path, path_str: str, tally: _PathTally
) -> None:
    """Force mode for one requested path."""
    try:
        outcomes = await _reindex_forced(service, path, path_str, tally)
    except Exception as e:  # noqa: BLE001 — a single path's forced re-index failure must not abort the batch; record it and continue
        logger.error("Failed to index %s: %s", path_str, e)
        tally.failed += 1
        return
    for outcome in outcomes:
        _tally_path_level_from_status(tally, outcome)


async def _refresh_changed_file(
    service: MdqService,
    conn: sqlite3.Connection,
    current_state: dict[str, str],
    file_path: Path,
) -> FileOutcome:
    """Re-index one file and advance index_state only when the write committed.

    The index_state row and the in-memory copy move forward only on the `indexed` status,
    so a skipped or failed file keeps the mtime the index already recorded and the next run
    reads the file again (REQ-002). Both copies are updated only after a successful
    re-index, so a path listed twice in one request is indexed once and skipped the second
    time. The mtime is read here, after the scan that listed the file, so a file that
    disappeared in between is reported as a failed file instead of indexed (REQ-005).
    """
    outcome_path = _outcome_path(service, file_path)
    state_key = f"mtime:{str(file_path)}"
    try:
        current_mtime = str(file_path.stat().st_mtime_ns)
    except FileNotFoundError:
        logger.error("File disappeared before it could be refreshed: %s", file_path)
        return FileOutcome(
            path=outcome_path, status="failed", reason_code="file_disappeared"
        )

    if current_state.get(state_key) == current_mtime:
        return FileOutcome(
            path=outcome_path, status="skipped_unchanged", reason_code="unchanged"
        )

    outcome = await _index_single_file(service, file_path)
    if outcome.status != "indexed":
        return outcome

    conn.execute(
        "INSERT OR REPLACE INTO index_state (key, value) VALUES (?, ?)",
        (state_key, current_mtime),
    )
    conn.commit()
    current_state[state_key] = current_mtime
    return outcome


async def _refresh_file_path(
    service: MdqService,
    conn: sqlite3.Connection,
    current_state: dict[str, str],
    path: Path,
    path_str: str,
    tally: _PathTally,
) -> None:
    """Incremental mode for one Markdown file."""
    tally.discovered_files += 1
    try:
        outcome = await _refresh_changed_file(service, conn, current_state, path)
    except Exception as e:  # noqa: BLE001 — a single file's incremental refresh failure must not abort the batch; record it and continue
        logger.error("Failed to refresh %s: %s", path_str, e)
        tally.failed += 1
        tally.failed_files += 1
        return
    _tally_file_outcome(tally, outcome)
    _tally_path_level_from_status(tally, outcome)


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
            tally.discovered_files += 1
            try:
                outcome = await _refresh_changed_file(
                    service, conn, current_state, md_file
                )
            except Exception:
                # The file that raised is one failed file; the path-level failure is
                # recorded by the handler below.
                tally.failed_files += 1
                raise
            _tally_file_outcome(tally, outcome)
            _tally_path_level_from_status(tally, outcome)
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

    Returns structured summary with the path-level counters, the file-level counters, and
    elapsed_seconds. A run in which every file failed reports the tool error rather than a
    summary the caller would read as a completed run (REQ-003).
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

        if _all_files_failed(tally):
            raise _all_files_failed_error(tally)

        elapsed = time.time() - start
        return {
            "indexed_count": tally.indexed,
            "skipped_count": tally.skipped,
            "deleted_count": tally.deleted,
            "failed_count": tally.failed,
            "discovered_file_count": tally.discovered_files,
            "committed_file_count": tally.committed_files,
            "skipped_file_count": tally.skipped_files,
            "failed_file_count": tally.failed_files,
            "unchanged_file_count": tally.unchanged_files,
            "elapsed_seconds": round(elapsed, 3),
        }
    finally:
        conn.close()
