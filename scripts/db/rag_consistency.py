#!/usr/bin/env python3
"""scripts/db/rag_consistency.py — RAG index consistency verification."""

import dataclasses
import sqlite3
from collections.abc import Callable, Iterable, Sequence

from db.helper import SQLiteHelper
from db.models import RagConsistencyReport
from db.rag_consistency_queries import (
    _check_read_smoke_test,
    _collect_affected_identifiers,
    _collect_basic_counts,
    _collect_document_checks,
    _collect_url_counts_and_mismatches,
)


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

    # _safe_url_count_query() records each per-query failure itself, so this stage
    # has no sqlite3.Error left to report.
    url_level_mismatches = _collect_url_counts_and_mismatches(db)

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
    """Return True when every rule in the `_CHECKS` group is clean.

    `_CHECKS` is defined below with the issue builders: it is the one place each
    consistency condition is stated, and `summarize_issues()` reads the same rules.
    """
    return all(check.clean(report) for check in _CHECKS)


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


def _fts_gap_issue(report: RagConsistencyReport) -> str:
    """FTS rows are missing for chunks that are in the chunk table."""
    detail = _ids_clause(
        report.affected_doc_ids, "doc_ids", limit=10, mark_at=10
    ) or _ids_clause(report.affected_chunk_ids, "chunk_ids", limit=10, mark_at=10)
    return (
        f"[WARNING] FTS gap detected (chunks={report.chunks}, fts={report.fts},"
        f" gap={report.fts_gap}).{detail} Run '/session rag-rebuild-fts' to repair."
    )


def _fts_orphan_issue(report: RagConsistencyReport) -> str:
    """The FTS index holds more entries than the chunk table, which indicates data loss."""
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


def _orphan_vec_issue(report: RagConsistencyReport) -> str:
    """chunks_vec holds rows whose chunk_id has no chunk row."""
    detail = _urls_clause(
        report.affected_orphan_urls, limit=5, mark_at=10
    ) or _ids_clause(
        report.affected_orphan_chunk_ids, "chunk_ids", limit=10, mark_at=None
    )
    return (
        f"[CRITICAL] Orphan vec rows detected (count={report.orphan_vec_count}).{detail}"
        f" Re-run ingestion with 'ingester.py --force' for affected URLs."
    )


def _vector_mismatch_issue(report: RagConsistencyReport) -> str:
    """chunks_vec and chunks hold a different number of rows."""
    detail = _urls_clause(
        report.affected_orphan_urls, limit=5, mark_at=10
    ) or _ids_clause(
        report.affected_orphan_chunk_ids, "chunk_ids", limit=10, mark_at=None
    )
    return (
        f"[WARNING] Vector count mismatch (chunks={report.chunks}, vec={report.vec}).{detail}"
        f" Re-run ingestion with 'ingester.py --force' for affected URLs."
    )


def _documents_without_chunks_issue(report: RagConsistencyReport) -> str:
    """A document row has no chunk rows."""
    detail = _ids_clause(
        report.affected_docs_without_chunks, "doc_ids", limit=10, mark_at=None
    )
    return (
        f"[WARNING] Documents without chunks detected (count={report.documents_without_chunks_count}).{detail}"
        f" Re-run ingestion for affected documents."
    )


def _chunks_without_vec_issue(report: RagConsistencyReport) -> str:
    """A chunk row has no vector row."""
    detail = _ids_clause(
        report.affected_chunks_without_vec, "chunk_ids", limit=10, mark_at=None
    )
    return (
        f"[CRITICAL] Chunks without vector rows detected (count={report.chunks_without_vec_count}).{detail}"
        f" Re-run ingestion with 'ingester.py --force' for affected chunks."
    )


def _duplicate_chunk_index_issue(report: RagConsistencyReport) -> str:
    """The same (doc_id, chunk_index) pair appears more than once."""
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


def _url_mismatch_issue(report: RagConsistencyReport) -> str:
    """At least one URL has a different number of chunk, vec, and fts rows."""
    mismatches = report.url_level_mismatches or {}
    detail = _urls_clause(mismatches, limit=5, mark_at=5)
    return (
        f"[WARNING] URL-level inconsistency detected (mismatched URLs={len(mismatches)}).{detail}"
        f" Re-run ingestion for affected URLs."
    )


@dataclasses.dataclass(frozen=True)
class _ConsistencyCheck:
    """One consistency rule: the predicate that says it is clean, and its message.

    `is_consistent()` and `summarize_issues()` both iterate `_CHECKS`, so each rule is
    stated once. An issue builder runs only when its own predicate reports the rule
    unclean, which is why the builders no longer guard their own conditions.
    `issue` is None for the two rules whose state the caller already reads from the
    report fields and that have no repair guidance to add.
    """

    clean: Callable[[RagConsistencyReport], bool]
    issue: Callable[[RagConsistencyReport], str] | None = None


_CHECKS: tuple[_ConsistencyCheck, ...] = (
    _ConsistencyCheck(lambda report: report.fts_gap == 0, _fts_gap_issue),
    _ConsistencyCheck(lambda report: report.fts_orphan_count == 0, _fts_orphan_issue),
    _ConsistencyCheck(lambda report: report.orphan_vec_count == 0, _orphan_vec_issue),
    _ConsistencyCheck(
        lambda report: report.vec == report.chunks, _vector_mismatch_issue
    ),
    _ConsistencyCheck(
        lambda report: report.documents_without_chunks_count == 0,
        _documents_without_chunks_issue,
    ),
    _ConsistencyCheck(
        lambda report: report.chunks_without_vec_count == 0,
        _chunks_without_vec_issue,
    ),
    _ConsistencyCheck(
        lambda report: report.duplicate_chunk_index_count == 0,
        _duplicate_chunk_index_issue,
    ),
    _ConsistencyCheck(
        lambda report: not report.url_level_mismatches, _url_mismatch_issue
    ),
    _ConsistencyCheck(lambda report: not report.diagnostic_errors),
    _ConsistencyCheck(lambda report: report.read_smoke_test_ok),
)


def summarize_issues(report: RagConsistencyReport) -> list[str]:
    """Return severity-prefixed descriptions of the `_CHECKS` rules that are not clean.

    The tuple order is the order the repair guidance assumes: FTS first, then vector
    rows, then the document-level checks, then the URL-level check.
    """
    issues: list[str] = []
    for check in _CHECKS:
        if check.issue is None or check.clean(report):
            continue
        issues.append(check.issue(report))
    return issues
