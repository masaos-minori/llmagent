#!/usr/bin/env python3
"""scripts/db/rag_consistency.py — RAG index consistency verification."""

import dataclasses
import sqlite3
from collections.abc import Callable, Iterable, Sequence

from db.helper import SQLiteHelper
from db.models import RagConsistencyReport


def _collect_basic_counts(db: SQLiteHelper) -> tuple[int, int, int, int, int, int]:
    """Return (chunks, fts, vec, orphan_vec_count, fts_gap, fts_orphan_count)."""
    chunks = db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    fts = db.execute("SELECT COUNT(*) FROM chunks_fts_docsize").fetchone()[0]
    vec = db.execute("SELECT COUNT(*) FROM chunks_vec").fetchone()[0]
    orphan_vec_count = db.execute(
        "SELECT COUNT(*) FROM chunks_vec WHERE chunk_id NOT IN (SELECT chunk_id FROM chunks)"
    ).fetchone()[0]
    fts_gap = max(0, chunks - fts)
    fts_orphan_count = max(0, fts - chunks)
    return chunks, fts, vec, orphan_vec_count, fts_gap, fts_orphan_count


def _collect_document_checks(db: SQLiteHelper) -> tuple[int, int, int]:
    """Return (docs_without_chunks, chunks_without_vec, duplicate_chunk_index_count)."""
    docs_without_chunks = db.execute(
        "SELECT COUNT(*) FROM documents WHERE doc_id NOT IN (SELECT DISTINCT doc_id FROM chunks)"
    ).fetchone()[0]
    chunks_without_vec = db.execute(
        "SELECT COUNT(*) FROM chunks WHERE chunk_id NOT IN (SELECT chunk_id FROM chunks_vec)"
    ).fetchone()[0]
    dup_chunk_indices = db.execute(
        "SELECT doc_id, chunk_index FROM chunks"
        " GROUP BY doc_id, chunk_index HAVING COUNT(*) > 1"
    ).fetchall()
    duplicate_chunk_index_count = len(dup_chunk_indices)
    return docs_without_chunks, chunks_without_vec, duplicate_chunk_index_count


def _safe_url_count_query(db: SQLiteHelper, sql: str) -> dict[str, int]:
    """Run a (url, count) query; return {} on failure (indicates DB corruption)."""
    try:
        rows = db.execute(sql).fetchall()
        return dict(rows)
    except Exception:  # noqa: BLE001, S110 — read-only query; failure indicates DB corruption
        return {}


def _collect_url_counts_and_mismatches(db: SQLiteHelper) -> dict[str, dict[str, int]]:
    """Return URL-level mismatch map keyed by URL with chunk/vec/fts counts."""
    url_chunk_counts = _safe_url_count_query(
        db,
        "SELECT d.url, COUNT(c.chunk_id) FROM documents d"
        " LEFT JOIN chunks c ON d.doc_id = c.doc_id"
        " GROUP BY d.url",
    )
    url_vec_counts = _safe_url_count_query(
        db,
        "SELECT d.url, COUNT(cv.chunk_id) FROM documents d"
        " LEFT JOIN chunks c ON d.doc_id = c.doc_id"
        " LEFT JOIN chunks_vec cv ON c.chunk_id = cv.chunk_id"
        " GROUP BY d.url",
    )
    url_fts_counts = _safe_url_count_query(
        db,
        "SELECT d.url, COUNT(cf.rowid) FROM documents d"
        " LEFT JOIN chunks c ON d.doc_id = c.doc_id"
        " LEFT JOIN chunks_fts cf ON c.chunk_id = cf.rowid"
        " GROUP BY d.url",
    )

    url_level_mismatches: dict[str, dict[str, int]] = {}
    all_urls = (
        set(url_chunk_counts.keys())
        | set(url_vec_counts.keys())
        | set(url_fts_counts.keys())
    )
    for url in all_urls:
        chunk_count = url_chunk_counts.get(url, 0)
        vec_count = url_vec_counts.get(url, 0)
        fts_count = url_fts_counts.get(url, 0)
        if (
            chunk_count != vec_count
            or chunk_count != fts_count
            or vec_count != fts_count
        ):
            url_level_mismatches[url] = {
                "chunk_count": chunk_count,
                "vec_count": vec_count,
                "fts_count": fts_count,
            }
    return url_level_mismatches


def _query_ids[T](db: SQLiteHelper, sql: str) -> tuple[T, ...]:
    """Return the first column of a top-10 identifier query."""
    return tuple(row[0] for row in db.execute(sql).fetchall())


def _query_ids_or_none[T](db: SQLiteHelper, sql: str) -> tuple[T, ...] | None:
    """_query_ids() for a query whose empty result means the issue does not exist."""
    return _query_ids(db, sql) or None


def _query_pairs(db: SQLiteHelper, sql: str) -> tuple[tuple[int, int], ...]:
    """Return the first two columns of a top-10 identifier query."""
    return tuple((row[0], row[1]) for row in db.execute(sql).fetchall())


def _collect_affected_identifiers(
    db: SQLiteHelper,
    *,
    fts_gap: int,
    orphan_vec_count: int,
    docs_without_chunks: int,
    chunks_without_vec: int,
    duplicate_chunk_index_count: int,
    url_level_mismatches: dict[str, dict[str, int]],
) -> tuple[
    tuple[int, ...] | None,
    tuple[int, ...] | None,
    tuple[int, ...] | None,
    tuple[str, ...] | None,
    tuple[int, ...] | None,
    tuple[int, ...] | None,
    tuple[tuple[int, int], ...] | None,
    tuple[str, ...] | None,
]:
    """Collect affected identifiers for each issue type (read-only; top 10 each).

    The four always-run queries report None when they find no rows, because an empty
    result means that issue does not exist. The guarded queries only run when a count
    already says the issue exists, so they keep their result as written.
    """
    affected_chunk_ids: tuple[int, ...] | None = _query_ids_or_none(
        db,
        "SELECT chunk_id FROM chunks EXCEPT SELECT id FROM chunks_fts_docsize LIMIT 10",
    )
    affected_doc_ids: tuple[int, ...] | None = _query_ids_or_none(
        db,
        "SELECT c.doc_id FROM chunks c "
        "WHERE c.chunk_id IN (SELECT chunk_id FROM chunks EXCEPT SELECT id FROM chunks_fts_docsize) "
        "ORDER BY c.doc_id LIMIT 10",
    )
    affected_orphan_chunk_ids: tuple[int, ...] | None = _query_ids_or_none(
        db,
        "SELECT chunk_id FROM chunks_vec EXCEPT SELECT chunk_id FROM chunks LIMIT 10",
    )
    affected_orphan_urls: tuple[str, ...] | None = _query_ids_or_none(
        db,
        "SELECT DISTINCT d.url FROM chunks_vec cv "
        "JOIN chunks c ON cv.chunk_id = c.chunk_id "
        "JOIN documents d ON c.doc_id = d.doc_id "
        "WHERE cv.chunk_id NOT IN (SELECT chunk_id FROM chunks) "
        "ORDER BY d.url LIMIT 10",
    )
    affected_docs_without_chunks: tuple[int, ...] | None = (
        _query_ids(
            db,
            "SELECT doc_id FROM documents WHERE doc_id NOT IN (SELECT DISTINCT doc_id FROM chunks)"
            " ORDER BY doc_id LIMIT 10",
        )
        if docs_without_chunks > 0
        else None
    )
    affected_chunks_without_vec: tuple[int, ...] | None = (
        _query_ids(
            db,
            "SELECT chunk_id FROM chunks WHERE chunk_id NOT IN (SELECT chunk_id FROM chunks_vec)"
            " ORDER BY chunk_id LIMIT 10",
        )
        if chunks_without_vec > 0
        else None
    )
    affected_duplicate_chunk_indices: tuple[tuple[int, int], ...] | None = (
        _query_pairs(
            db,
            "SELECT doc_id, chunk_index FROM chunks"
            " GROUP BY doc_id, chunk_index HAVING COUNT(*) > 1"
            " ORDER BY doc_id, chunk_index LIMIT 10",
        )
        if duplicate_chunk_index_count > 0
        else None
    )
    affected_url_mismatches: tuple[str, ...] | None = (
        tuple(list(url_level_mismatches.keys())[:5]) if url_level_mismatches else None
    )

    return (
        affected_chunk_ids,
        affected_doc_ids,
        affected_orphan_chunk_ids,
        affected_orphan_urls,
        affected_docs_without_chunks,
        affected_chunks_without_vec,
        affected_duplicate_chunk_indices,
        affected_url_mismatches,
    )


def _check_read_smoke_test(db: SQLiteHelper) -> bool:
    """Verify each required RAG table can be read without raising."""
    required_tables = [
        "documents",
        "chunks",
        "chunks_fts_docsize",
        "chunks_vec",
    ]
    for table in required_tables:
        try:
            db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()  # nosec B608 — table names are hardcoded constants from required_tables, not user-controlled
        except sqlite3.Error:
            return False
    return True


def check_rag_consistency(
    db: SQLiteHelper, embed_failed: int = 0
) -> RagConsistencyReport:
    """Return row counts from chunks, chunks_fts, and chunks_vec for consistency verification.

    All queries are read-only. Orphan vec rows are chunk_id values in chunks_vec
    with no matching row in chunks (possible when the chunks_vec_ad trigger fails).
    """
    diagnostic_errors = []

    # Initialize default values
    chunks = fts = vec = orphan_vec_count = fts_gap = fts_orphan_count = 0
    docs_without_chunks = chunks_without_vec = duplicate_chunk_index_count = 0
    url_level_mismatches = {}
    (
        affected_chunk_ids,
        affected_doc_ids,
        affected_orphan_chunk_ids,
        affected_orphan_urls,
        affected_docs_without_chunks,
        affected_chunks_without_vec,
        affected_duplicate_chunk_indices,
        affected_url_mismatches,
    ) = (None,) * 8

    try:
        chunks, fts, vec, orphan_vec_count, fts_gap, fts_orphan_count = (
            _collect_basic_counts(db)
        )
    except sqlite3.Error as e:
        diagnostic_errors.append(f"Basic counts collection failed: {e}")

    try:
        docs_without_chunks, chunks_without_vec, duplicate_chunk_index_count = (
            _collect_document_checks(db)
        )
    except sqlite3.Error as e:
        diagnostic_errors.append(f"Document checks collection failed: {e}")

    try:
        url_level_mismatches = _collect_url_counts_and_mismatches(db)
    except sqlite3.Error as e:
        diagnostic_errors.append(f"URL mismatch collection failed: {e}")

    try:
        (
            affected_chunk_ids,
            affected_doc_ids,
            affected_orphan_chunk_ids,
            affected_orphan_urls,
            affected_docs_without_chunks,
            affected_chunks_without_vec,
            affected_duplicate_chunk_indices,
            affected_url_mismatches,
        ) = _collect_affected_identifiers(
            db,
            fts_gap=fts_gap,
            orphan_vec_count=orphan_vec_count,
            docs_without_chunks=docs_without_chunks,
            chunks_without_vec=chunks_without_vec,
            duplicate_chunk_index_count=duplicate_chunk_index_count,
            url_level_mismatches=url_level_mismatches,
        )
    except sqlite3.Error as e:
        diagnostic_errors.append(f"Affected identifiers collection failed: {e}")

    report = RagConsistencyReport(
        chunks=chunks,
        fts=fts,
        vec=vec,
        orphan_vec_count=orphan_vec_count,
        fts_gap=fts_gap,
        fts_orphan_count=fts_orphan_count,
        embed_failed=embed_failed,
        read_smoke_test_ok=_check_read_smoke_test(db),
        affected_chunk_ids=affected_chunk_ids,
        affected_doc_ids=affected_doc_ids,
        affected_orphan_chunk_ids=affected_orphan_chunk_ids,
        affected_orphan_urls=affected_orphan_urls,
        documents_without_chunks_count=docs_without_chunks,
        chunks_without_vec_count=chunks_without_vec,
        duplicate_chunk_index_count=duplicate_chunk_index_count,
        url_level_mismatches=url_level_mismatches if url_level_mismatches else None,
        affected_docs_without_chunks=affected_docs_without_chunks,
        affected_chunks_without_vec=affected_chunks_without_vec,
        affected_duplicate_chunk_indices=affected_duplicate_chunk_indices,
        affected_url_mismatches=affected_url_mismatches,
        diagnostic_errors=tuple(diagnostic_errors) if diagnostic_errors else None,
    )
    return dataclasses.replace(report, issues=tuple(summarize_issues(report)))


def is_consistent(report: RagConsistencyReport) -> bool:
    """Return True when all consistency checks pass."""
    consistent: bool = (
        report.fts_gap == 0
        and report.fts_orphan_count == 0
        and report.orphan_vec_count == 0
        and report.vec == report.chunks
        and report.documents_without_chunks_count == 0
        and report.chunks_without_vec_count == 0
        and report.duplicate_chunk_index_count == 0
        and not report.url_level_mismatches
        and not report.diagnostic_errors
        and report.read_smoke_test_ok
    )
    return consistent


_FTS_ORPHAN_NO_IDS_CLAUSE = (
    " Chunk-level identifiers unavailable (FTS orphans have no parent chunk rows)."
)


def _ids_clause(
    values: Sequence[int] | None,
    label: str,
    *,
    limit: int,
    mark_at: int | None,
) -> str:
    """Render " Affected <label>: [1, 2 ...]." for an identifier tuple, or "" when empty.

    mark_at is the length that earns the trailing " ..." marker; None never marks.
    The callers do not agree on either value, so each one states both explicitly.
    """
    if not values:
        return ""
    rendered = ", ".join(str(value) for value in values[:limit])
    marker = " ..." if mark_at is not None and len(values) == mark_at else ""
    return f" Affected {label}: [{rendered}{marker}]."


def _urls_clause(
    values: Iterable[str] | None, *, limit: int, mark_at: int | None
) -> str:
    """Render " Affected URLs: [...]." for a URL sequence or mapping, or "" when empty.

    A mapping contributes its keys, which is how url_level_mismatches is reported.
    """
    urls = tuple(values or ())
    if not urls:
        return ""
    rendered = ", ".join(urls[:limit])
    marker = " ..." if mark_at is not None and len(urls) == mark_at else ""
    return f" Affected URLs: [{rendered}{marker}]."


def _fts_gap_issue(report: RagConsistencyReport) -> str | None:
    """FTS rows are missing for chunks that are in the chunk table."""
    if report.fts_gap <= 0:
        return None
    detail = _ids_clause(
        report.affected_doc_ids, "doc_ids", limit=10, mark_at=10
    ) or _ids_clause(report.affected_chunk_ids, "chunk_ids", limit=10, mark_at=10)
    return (
        f"[WARNING] FTS gap detected (chunks={report.chunks}, fts={report.fts},"
        f" gap={report.fts_gap}).{detail} Run '/session rag-rebuild-fts' to repair."
    )


def _fts_orphan_issue(report: RagConsistencyReport) -> str | None:
    """The FTS index holds more entries than the chunk table, which indicates data loss."""
    if report.fts_orphan_count <= 0:
        return None
    detail = (
        _ids_clause(report.affected_orphan_chunk_ids, "chunk_ids", limit=10, mark_at=10)
        or _urls_clause(report.affected_orphan_urls, limit=5, mark_at=10)
        or ("" if report.affected_chunk_ids else _FTS_ORPHAN_NO_IDS_CLAUSE)
    )
    return (
        f"[CRITICAL] FTS index has more entries than chunks"
        f" (fts={report.fts}, chunks={report.chunks}).{detail}"
        f" Run '/session rag-rebuild-fts' immediately; orphan FTS entries indicate data loss risk."
    )


def _orphan_vec_issue(report: RagConsistencyReport) -> str | None:
    """chunks_vec holds rows whose chunk_id has no chunk row."""
    if report.orphan_vec_count <= 0:
        return None
    detail = _urls_clause(
        report.affected_orphan_urls, limit=5, mark_at=10
    ) or _ids_clause(
        report.affected_orphan_chunk_ids, "chunk_ids", limit=10, mark_at=None
    )
    return (
        f"[CRITICAL] Orphan vec rows detected (count={report.orphan_vec_count}).{detail}"
        f" Re-run ingestion with 'ingester.py --force' for affected URLs."
    )


def _vector_mismatch_issue(report: RagConsistencyReport) -> str | None:
    """chunks_vec and chunks hold a different number of rows."""
    if report.vec == report.chunks:
        return None
    detail = _urls_clause(
        report.affected_orphan_urls, limit=5, mark_at=10
    ) or _ids_clause(
        report.affected_orphan_chunk_ids, "chunk_ids", limit=10, mark_at=None
    )
    return (
        f"[WARNING] Vector count mismatch (chunks={report.chunks}, vec={report.vec}).{detail}"
        f" Re-run ingestion with 'ingester.py --force' for affected URLs."
    )


def _documents_without_chunks_issue(report: RagConsistencyReport) -> str | None:
    """A document row has no chunk rows."""
    if report.documents_without_chunks_count <= 0:
        return None
    detail = _ids_clause(
        report.affected_docs_without_chunks, "doc_ids", limit=10, mark_at=None
    )
    return (
        f"[WARNING] Documents without chunks detected (count={report.documents_without_chunks_count}).{detail}"
        f" Re-run ingestion for affected documents."
    )


def _chunks_without_vec_issue(report: RagConsistencyReport) -> str | None:
    """A chunk row has no vector row."""
    if report.chunks_without_vec_count <= 0:
        return None
    detail = _ids_clause(
        report.affected_chunks_without_vec, "chunk_ids", limit=10, mark_at=None
    )
    return (
        f"[CRITICAL] Chunks without vector rows detected (count={report.chunks_without_vec_count}).{detail}"
        f" Re-run ingestion with 'ingester.py --force' for affected chunks."
    )


def _duplicate_chunk_index_issue(report: RagConsistencyReport) -> str | None:
    """The same (doc_id, chunk_index) pair appears more than once."""
    if report.duplicate_chunk_index_count <= 0:
        return None
    pairs = report.affected_duplicate_chunk_indices
    detail = (
        f" Affected (doc_id, chunk_index): [{', '.join(f'({d},{c})' for d, c in pairs[:10])}]."
        if pairs
        else ""
    )
    return (
        f"[CRITICAL] Duplicate chunk_index values detected (count={report.duplicate_chunk_index_count}).{detail}"
        f" Check ingestion logic; duplicate chunk indices indicate data corruption risk."
    )


def _url_mismatch_issue(report: RagConsistencyReport) -> str | None:
    """At least one URL has a different number of chunk, vec, and fts rows."""
    if not report.url_level_mismatches:
        return None
    detail = _urls_clause(report.url_level_mismatches, limit=5, mark_at=5)
    return (
        f"[WARNING] URL-level inconsistency detected (mismatched URLs={len(report.url_level_mismatches)}).{detail}"
        f" Re-run ingestion for affected URLs."
    )


_ISSUE_BUILDERS: tuple[Callable[[RagConsistencyReport], str | None], ...] = (
    _fts_gap_issue,
    _fts_orphan_issue,
    _orphan_vec_issue,
    _vector_mismatch_issue,
    _documents_without_chunks_issue,
    _chunks_without_vec_issue,
    _duplicate_chunk_index_issue,
    _url_mismatch_issue,
)


def summarize_issues(report: RagConsistencyReport) -> list[str]:
    """Return severity-prefixed descriptions of consistency issues with repair guidance.

    Each builder in _ISSUE_BUILDERS returns one message or None, and the tuple order is
    the order the repair guidance assumes: FTS first, then vector rows, then the
    document-level checks, then the URL-level check.
    """
    return [issue for issue in (build(report) for build in _ISSUE_BUILDERS) if issue]
