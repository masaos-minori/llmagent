#!/usr/bin/env python3
"""scripts/mcp_servers/mdq/search.py

Search functionality using FTS5 (BM25).

One query boundary (plan mdqmcp002): the authorized-source predicate is applied in SQL
before `COUNT`, ranking, and `LIMIT`, so an unauthorized row can neither change a visible
count nor fill a result slot. Each search owns its own connection through `db.helper` and
is cancelled through the progress-handler stop event within the bounded drain interval. The
active-search count is capped at the existing per-server concurrency convention. A SQLite
failure is classified by cause against the closed code vocabulary, and no raw query text
reaches the response, the metadata, or the persistent log line — the hashed identifier is
used instead.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sqlite3
import threading
import time
import weakref
from pathlib import Path
from typing import TYPE_CHECKING

from db.helper import SQLiteHelper
from shared.formatters import fmt_kvlog
from shared.tool_transport_invoker import DEFAULT_PER_SERVER_CONCURRENCY

from mcp_servers.audit import hash_query_value
from mcp_servers.mdq.auth import authorize_path, canonicalized_roots
from mcp_servers.mdq.mdq_error_codes import TIMEOUT, code_for_exception
from mcp_servers.mdq.mdq_models import (
    MdqAuthorizationError,
    MdqConsistencyError,
    MdqValidationError,
    SearchDocsMetadata,
    SearchDocsRequest,
    SearchResultItem,
    SearchResultResult,
)

if TYPE_CHECKING:
    from mcp_servers.mdq.mdq_service import MdqService

logger = logging.getLogger(__name__)

# Interval the caller waits for a worker after setting the stop event (AC-4). A worker that
# does not stop inside this interval is reported as a timeout and left to release its own
# connection.
DRAIN_INTERVAL_SEC = 5.0

# Active-search limit: the existing per-server concurrency convention.
MAX_ACTIVE_SEARCHES = DEFAULT_PER_SERVER_CONCURRENCY

# `asyncio.Semaphore` binds to the event loop it first runs on, so the module-level limit is
# held as one gate per running loop rather than as a single shared semaphore.
_SEARCH_GATES: weakref.WeakKeyDictionary[
    asyncio.AbstractEventLoop, asyncio.Semaphore
] = weakref.WeakKeyDictionary()


def _active_search_gate() -> asyncio.Semaphore:
    """Return the active-search gate for the event loop the call runs on."""
    loop = asyncio.get_running_loop()
    gate = _SEARCH_GATES.get(loop)
    if gate is None:
        gate = asyncio.Semaphore(MAX_ACTIVE_SEARCHES)
        _SEARCH_GATES[loop] = gate
    return gate


def _clamp_to_config_cap(request_value: int | None, config_cap: int) -> int:
    """Resolve a request-supplied override bounded by the server's config cap.

    Mirrors the "request overrides bounded by config cap" rule applied to
    both `max_results_limit` and `max_total_result_chars`: an absent request
    value (`None`) falls back to the config cap outright; a present value is
    clamped so a request can only narrow, never widen, the cap.
    """
    if request_value is None:
        return config_cap
    return min(request_value, config_cap)


def classify_sqlite_error(
    exc: sqlite3.Error, *, interrupted: bool
) -> tuple[BaseException, bool]:
    """Map a SQLite failure on the search path to a domain error and its retryability (REQ-003).

    The returned domain error carries only the cause category, never the SQLite detail or a
    path. An interrupted statement is the timeout case; `TimeoutError` is what
    `code_for_exception()` resolves to `timeout`, so the search path raises it as the cause of
    the domain exception it reports.
    """
    if interrupted:
        return TimeoutError("search interrupted"), True

    if not isinstance(exc, sqlite3.OperationalError):
        # A sqlite3.Error that is not an OperationalError has no cause to read from its
        # message: it is an index-consistency failure, not a rejected query.
        return MdqConsistencyError("FTS5 index inconsistency"), False

    text = str(exc).lower()
    text = str(exc).lower()
    if (
        "corrupt" in text
        or "malformed" in text
        or "no such table" in text
        or "no such column" in text
    ):
        return MdqConsistencyError("FTS5 index inconsistency"), False
    if "busy" in text or "locked" in text:
        return MdqConsistencyError("FTS5 index is busy"), True
    return MdqValidationError("Invalid FTS5 query syntax"), False


async def search_docs(
    service: MdqService, req: SearchDocsRequest
) -> tuple[str, SearchDocsMetadata]:
    """Search indexed Markdown sections by query; returns formatted results."""
    t0 = time.perf_counter()
    identifier = hash_query_value(req.query)

    async with _active_search_gate():
        stop = threading.Event()
        task = asyncio.create_task(
            asyncio.to_thread(_search_docs_structured, service, req, stop)
        )
        try:
            result = await _await_with_bounded_drain(
                task, stop, identifier, service.search_timeout_sec
            )
        except TimeoutError as exc:
            raise MdqConsistencyError(
                f"Search timed out after {service.search_timeout_sec}s"
            ) from exc

    if not result["results"]:
        duration_ms = (time.perf_counter() - t0) * 1000
        return f"No results found for query {identifier}.", SearchDocsMetadata(
            query_preview=identifier,
            result_count=0,
            shown_count=0,
            truncated=False,
            total_count=0,
            duration_ms=duration_ms,
        )

    # matched_count is the authorized count the SQL predicate reported before any LIMIT was
    # applied, so it counts only rows the caller can see; it is a true total, unlike the
    # pre-fix "total" field which silently reported the post-LIMIT row count as if it were exact.
    matched_count = result["matched_count"]

    # Apply result size limits (request overrides bounded by config cap)
    max_results = _clamp_to_config_cap(req.max_results_limit, service.max_results_limit)
    max_chars = _clamp_to_config_cap(
        req.max_total_result_chars, service.max_total_result_chars
    )

    results = result["results"]
    if len(results) > max_results:
        results = results[:max_results]

    # Enforce char limit
    lines = [f"Search results for query {identifier} ({matched_count} found)"]
    for r in results:
        line = f"{r.source_path}: {r.heading}: {r.snippet}"
        if len("\n".join(lines)) + len(line) > max_chars:
            break
        lines.append(line)
    shown_count = len(lines) - 1  # subtract header line
    chars_used = len("\n".join(lines))

    # Honest reporting: only claim a bare "found" total when nothing was
    # actually hidden by limiting (SQL layer, authorization, count cap, or
    # char budget) — otherwise surface both the exact matched count and the
    # actually-shown count so the header/trailer never conflate the two.
    duration_ms = (time.perf_counter() - t0) * 1000
    if matched_count != shown_count:
        return "\n".join(lines) + (
            f"\n\n[Truncated — {matched_count} results found, "
            f"{shown_count} shown ({chars_used}/{max_chars} chars). "
            f"Use a narrower query or get_chunk for specific sections.]"
        ), SearchDocsMetadata(
            query_preview=identifier,
            result_count=matched_count,
            shown_count=shown_count,
            truncated=True,
            total_count=matched_count,
            duration_ms=duration_ms,
        )
    return "\n".join(lines), SearchDocsMetadata(
        query_preview=identifier,
        result_count=matched_count,
        shown_count=shown_count,
        truncated=False,
        total_count=matched_count,
        duration_ms=duration_ms,
    )


async def _await_with_bounded_drain(
    task: asyncio.Task[SearchResultResult],
    stop: threading.Event,
    identifier: str,
    timeout_sec: float,
) -> SearchResultResult:
    """Await one search, then cancel it through the stop event inside the bounded drain (AC-4).

    A worker that finishes before the timeout returns its result, or raises the domain error
    its cause classification produced. A worker that exceeds the timeout is asked to stop
    through the progress-handler stop event, and the caller waits for it inside
    `DRAIN_INTERVAL_SEC` so a timed-out search never carries an open connection past the
    caller. The wait is bounded: when the worker does not stop inside the interval the call is
    reported as a timeout and the worker is left to close its own connection.
    """
    done, _ = await asyncio.wait({task}, timeout=timeout_sec)
    if task in done:
        return task.result()  # re-raises the worker's classified error

    stop.set()
    drained, pending = await asyncio.wait({task}, timeout=DRAIN_INTERVAL_SEC)
    stopped = task in drained
    if stopped:
        # Consume the worker's outcome so its exception is never left unretrieved.
        try:
            task.result()
        except Exception as exc:  # noqa: BLE001 — the caller reports the timeout, not the worker detail
            stopped = isinstance(exc, TimeoutError)
    else:
        task.cancel()

    logger.info(
        fmt_kvlog(
            "mdq_search",
            query=identifier,
            code=TIMEOUT,
            outcome="cancellation",
            timeout_sec=timeout_sec,
            drain_interval_sec=DRAIN_INTERVAL_SEC,
            worker_stopped=stopped,
        )
    )
    raise TimeoutError(f"search exceeded {timeout_sec}s")


def _prefix_predicate(
    column: str, prefix: str, *, separator_boundary: bool
) -> tuple[str, list[object]]:
    """Exact prefix comparison, without `LIKE` metacharacters.

    A `%` or `_` inside the prefix is data, not a wildcard, so a filter can never broaden the
    row set beyond the literal prefix it names. With `separator_boundary` the match requires
    the prefix to be a complete path segment, which is what makes a path filter a scope rather
    than a pattern; a heading filter compares the literal prefix only.
    """
    if separator_boundary:
        return (
            f"({column} = ? OR substr({column}, 1, ?) = ?)",
            [prefix, len(prefix) + 1, prefix + os.sep],
        )
    return (
        f"({column} = ? OR substr({column}, 1, ?) = ?)",
        [prefix, len(prefix), prefix],
    )


def _build_search_where(
    service: MdqService, req: SearchDocsRequest
) -> tuple[list[str], list[object]]:
    """Build WHERE clause and params for search.

    The authorized-source predicate is part of the clause, so `COUNT`, ranking, and `LIMIT`
    all see only rows inside the canonicalized roots (REQ-001, REQ-002). An empty allowlist is
    the fail-closed case: the predicate matches no row.
    """
    roots = canonicalized_roots(service.allowed_dirs)
    params: list[object] = []
    if not roots:
        where_clauses = ["1 = 0"]
    else:
        clauses = []
        for root in roots:
            clause, root_params = _prefix_predicate(
                "c.source_path", root, separator_boundary=True
            )
            clauses.append(clause)
            params.extend(root_params)
        where_clauses = ["(" + " OR ".join(clauses) + ")"]

    where_clauses.insert(0, "chunks_fts MATCH ?")
    params.insert(0, req.query)

    if req.path_prefix:
        prefix = Path(req.path_prefix)
        if not authorize_path(prefix, service.allowed_dirs):
            raise MdqAuthorizationError(
                "Access denied: path_prefix is outside allowed directories"
            )
        clause, clause_params = _prefix_predicate(
            "c.source_path", str(prefix.resolve()), separator_boundary=True
        )
        where_clauses.append(clause)
        params.extend(clause_params)

    if req.heading_prefix:
        clause, clause_params = _prefix_predicate(
            "c.heading_path", req.heading_prefix, separator_boundary=False
        )
        where_clauses.append(clause)
        params.extend(clause_params)

    if req.tag_filter:
        for tag in req.tag_filter:
            where_clauses.append(
                "EXISTS (SELECT 1 FROM json_each(c.tags_json) WHERE value = ?)"
            )
            params.append(tag)

    return where_clauses, params


def _search_docs_structured(
    service: MdqService,
    req: SearchDocsRequest,
    stop: threading.Event | None = None,
) -> SearchResultResult:
    """Run one FTS5 search on its own connection; return the structured result.

    The connection is opened by this function through `db.helper.SQLiteHelper` with the
    supplied `db_path`, is closed here in `finally`, and is never handed to another search.
    `stop` is installed as the progress-handler predicate so a long statement is interrupted
    once the caller asks the worker to stop.
    """
    if not req.query or not req.query.strip():
        return SearchResultResult(
            query=req.query, results=[], matched_count=0, shown_count=0
        )

    identifier = hash_query_value(req.query)
    logger.info(fmt_kvlog("mdq_search", query=identifier))

    # Cap the SQL-layer fetch itself at the server's configured limit so a
    # large request `limit` cannot bypass the config cap by having the
    # database return an unbounded row set before Python-side truncation.
    effective_limit = min(req.limit or 10, service.max_results_limit)

    helper = SQLiteHelper(
        db_path=service.db_path, sqlite_busy_timeout_ms=service.sqlite_busy_timeout
    )
    matched_count = 0
    results: list[SearchResultItem] = []
    try:
        with helper.open(row_factory=True) as helper:
            if stop is not None:
                helper.interrupt_when(stop)

            where_clauses, params = _build_search_where(service, req)
            where_clause = " AND ".join(where_clauses)

            # Exact authorized count, with no LIMIT applied — used to report an honest
            # matched_count independent of effective_limit.
            matched_count_row = helper.execute(
                f"""SELECT COUNT(*) as cnt
                    FROM chunks_fts f
                    JOIN chunks c ON f.rowid = c.rowid
                    WHERE {where_clause}""",  # nosec B608 — where_clause built only from static predicate fragments in _build_search_where(); all values bound via params
                tuple(params),
            ).fetchone()
            matched_count = (
                matched_count_row["cnt"] if matched_count_row is not None else 0
            )

            # Get FTS5 results
            rows = helper.execute(
                f"""SELECT c.chunk_id, c.source_path, c.heading, c.heading_path,
                       c.start_line, c.end_line, c.token_count, c.content,
                       rank
                    FROM chunks_fts f
                    JOIN chunks c ON f.rowid = c.rowid
                    WHERE {where_clause}
                    ORDER BY rank
                    LIMIT ?""",  # nosec B608 — where_clause built only from static predicate fragments in _build_search_where(); all values bound via params
                tuple(params) + (effective_limit,),
            ).fetchall()

            results = [
                SearchResultItem(
                    chunk_id=row["chunk_id"],
                    source_path=row["source_path"],
                    heading=row["heading"],
                    heading_path=row["heading_path"],
                    score=float(row["rank"]) if row["rank"] is not None else 0.0,
                    start_line=row["start_line"],
                    end_line=row["end_line"],
                    token_count=row["token_count"],
                    snippet=row["content"][: service.max_snippet_chars],
                )
                for row in rows
            ]

    except sqlite3.Error as exc:
        domain, retryable = classify_sqlite_error(
            exc, interrupted=stop is not None and stop.is_set()
        )
        logger.warning(
            fmt_kvlog(
                "mdq_search",
                query=identifier,
                code=code_for_exception(domain),
                retryable=retryable,
            )
        )
        raise domain from exc
    finally:
        helper.close()

    return SearchResultResult(
        query=req.query,
        results=results,
        matched_count=matched_count,
        shown_count=len(results),
    )
