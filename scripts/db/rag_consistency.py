#!/usr/bin/env python3
"""scripts/db/rag_consistency.py — RAG index consistency verification."""

import dataclasses
import sqlite3

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


def _collect_url_counts_and_mismatches(db: SQLiteHelper) -> dict[str, dict[str, int]]:
    """Return URL-level mismatch map keyed by URL with chunk/vec/fts counts."""
    url_chunk_counts: dict[str, int] = {}
    url_chunk_rows = db.execute(
        "SELECT d.url, COUNT(c.chunk_id) FROM documents d"
        " LEFT JOIN chunks c ON d.doc_id = c.doc_id"
        " GROUP BY d.url"
    ).fetchall()
    url_chunk_counts = dict(url_chunk_rows)

    url_vec_counts: dict[str, int] = {}
    url_vec_rows = db.execute(
        "SELECT d.url, COUNT(cv.chunk_id) FROM documents d"
        " LEFT JOIN chunks c ON d.doc_id = c.doc_id"
        " LEFT JOIN chunks_vec cv ON c.chunk_id = cv.chunk_id"
        " GROUP BY d.url"
    ).fetchall()
    url_vec_counts = dict(url_vec_rows)

    url_fts_counts: dict[str, int] = {}
    url_fts_rows = db.execute(
        "SELECT d.url, COUNT(cf.rowid) FROM documents d"
        " LEFT JOIN chunks c ON d.doc_id = c.doc_id"
        " LEFT JOIN chunks_fts cf ON c.chunk_id = cf.rowid"
        " GROUP BY d.url"
    ).fetchall()
    url_fts_counts = dict(url_fts_rows)

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
    """Collect affected identifiers for each issue type (read-only; top 10 each)."""
    affected_chunk_ids: tuple[int, ...] | None = None
    affected_doc_ids: tuple[int, ...] | None = None
    affected_orphan_chunk_ids: tuple[int, ...] | None = None
    affected_orphan_urls: tuple[str, ...] | None = None
    affected_docs_without_chunks: tuple[int, ...] | None = None
    affected_chunks_without_vec: tuple[int, ...] | None = None
    affected_duplicate_chunk_indices: tuple[tuple[int, int], ...] | None = None
    affected_url_mismatches: tuple[str, ...] | None = None

    if fts_gap > 0:
        rows = db.execute(
            "SELECT chunk_id FROM chunks EXCEPT SELECT id FROM chunks_fts_docsize LIMIT 10"
        ).fetchall()
        affected_chunk_ids = tuple(r[0] for r in rows)
        doc_rows = db.execute(
            "SELECT c.doc_id FROM chunks c "
            "WHERE c.chunk_id IN (SELECT chunk_id FROM chunks EXCEPT SELECT id FROM chunks_fts_docsize) "
            "ORDER BY c.doc_id LIMIT 10"
        ).fetchall()
        affected_doc_ids = tuple(r[0] for r in doc_rows) if doc_rows else None
    if orphan_vec_count > 0:
        id_rows = db.execute(
            "SELECT chunk_id FROM chunks_vec EXCEPT SELECT chunk_id FROM chunks LIMIT 10"
        ).fetchall()
        affected_orphan_chunk_ids = tuple(r[0] for r in id_rows)
        url_rows = db.execute(
            "SELECT DISTINCT d.url FROM chunks_vec cv "
            "JOIN chunks c ON cv.chunk_id = c.chunk_id "
            "JOIN documents d ON c.doc_id = d.doc_id "
            "WHERE cv.chunk_id NOT IN (SELECT chunk_id FROM chunks) "
            "ORDER BY d.url LIMIT 10"
        ).fetchall()
        affected_orphan_urls = tuple(r[0] for r in url_rows) if url_rows else None
    if docs_without_chunks > 0:
        id_rows = db.execute(
            "SELECT doc_id FROM documents WHERE doc_id NOT IN (SELECT DISTINCT doc_id FROM chunks)"
            " ORDER BY doc_id LIMIT 10"
        ).fetchall()
        affected_docs_without_chunks = tuple(r[0] for r in id_rows)
    if chunks_without_vec > 0:
        id_rows = db.execute(
            "SELECT chunk_id FROM chunks WHERE chunk_id NOT IN (SELECT chunk_id FROM chunks_vec)"
            " ORDER BY chunk_id LIMIT 10"
        ).fetchall()
        affected_chunks_without_vec = tuple(r[0] for r in id_rows)
    if duplicate_chunk_index_count > 0:
        limited_dups = db.execute(
            "SELECT doc_id, chunk_index FROM chunks"
            " GROUP BY doc_id, chunk_index HAVING COUNT(*) > 1"
            " ORDER BY doc_id, chunk_index LIMIT 10"
        ).fetchall()
        affected_duplicate_chunk_indices = tuple((r[0], r[1]) for r in limited_dups)
    if url_level_mismatches:
        affected_url_mismatches = tuple(list(url_level_mismatches.keys())[:5])

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
    )
    return consistent


def summarize_issues(report: RagConsistencyReport) -> list[str]:
    """Return severity-prefixed descriptions of consistency issues with repair guidance."""
    issues: list[str] = []
    if report.fts_gap > 0:
        detail = ""
        if report.affected_doc_ids:
            ids = ", ".join(str(i) for i in report.affected_doc_ids[:10])
            truncated = " ..." if len(report.affected_doc_ids) == 10 else ""
            detail = f" Affected doc_ids: [{ids}{truncated}]."
        elif report.affected_chunk_ids:
            ids = ", ".join(str(i) for i in report.affected_chunk_ids[:10])
            truncated = " ..." if len(report.affected_chunk_ids) == 10 else ""
            detail = f" Affected chunk_ids: [{ids}{truncated}]."
        issues.append(
            f"[WARNING] FTS gap detected (chunks={report.chunks}, fts={report.fts},"
            f" gap={report.fts_gap}).{detail} Run '/session rag-rebuild-fts' to repair."
        )
    if report.fts_orphan_count > 0:
        detail = ""
        if report.affected_orphan_chunk_ids:
            ids = ", ".join(str(i) for i in report.affected_orphan_chunk_ids[:10])
            truncated = " ..." if len(report.affected_orphan_chunk_ids) == 10 else ""
            detail = f" Affected chunk_ids: [{ids}{truncated}]."
        elif report.affected_orphan_urls:
            urls = ", ".join(report.affected_orphan_urls[:5])
            truncated = " ..." if len(report.affected_orphan_urls) == 10 else ""
            detail = f" Affected URLs: [{urls}{truncated}]."
        elif not report.affected_chunk_ids:
            detail = " Chunk-level identifiers unavailable (FTS orphans have no parent chunk rows)."
        issues.append(
            f"[CRITICAL] FTS index has more entries than chunks"
            f" (fts={report.fts}, chunks={report.chunks}).{detail}"
            f" Run '/session rag-rebuild-fts' immediately; orphan FTS entries indicate data loss risk."
        )
    if report.orphan_vec_count > 0:
        detail = ""
        if report.affected_orphan_urls:
            urls = ", ".join(report.affected_orphan_urls[:5])
            truncated = " ..." if len(report.affected_orphan_urls) == 10 else ""
            detail = f" Affected URLs: [{urls}{truncated}]."
        elif report.affected_orphan_chunk_ids:
            ids = ", ".join(str(i) for i in report.affected_orphan_chunk_ids[:10])
            detail = f" Affected chunk_ids: [{ids}]."
        issues.append(
            f"[CRITICAL] Orphan vec rows detected (count={report.orphan_vec_count}).{detail}"
            f" Re-run ingestion with 'ingester.py --force' for affected URLs."
        )
    if report.vec != report.chunks:
        detail = ""
        if report.affected_orphan_urls:
            urls = ", ".join(report.affected_orphan_urls[:5])
            truncated = " ..." if len(report.affected_orphan_urls) == 10 else ""
            detail = f" Affected URLs: [{urls}{truncated}]."
        elif report.affected_orphan_chunk_ids:
            ids = ", ".join(str(i) for i in report.affected_orphan_chunk_ids[:10])
            detail = f" Affected chunk_ids: [{ids}]."
        issues.append(
            f"[WARNING] Vector count mismatch (chunks={report.chunks}, vec={report.vec}).{detail}"
            f" Re-run ingestion with 'ingester.py --force' for affected URLs."
        )
    if report.documents_without_chunks_count > 0:
        ids = (
            ", ".join(str(i) for i in report.affected_docs_without_chunks[:10])
            if report.affected_docs_without_chunks
            else ""
        )
        detail = (
            f" Affected doc_ids: [{ids}]."
            if report.affected_docs_without_chunks
            else ""
        )
        issues.append(
            f"[WARNING] Documents without chunks detected (count={report.documents_without_chunks_count}).{detail}"
            f" Re-run ingestion for affected documents."
        )
    if report.chunks_without_vec_count > 0:
        ids = (
            ", ".join(str(i) for i in report.affected_chunks_without_vec[:10])
            if report.affected_chunks_without_vec
            else ""
        )
        detail = (
            f" Affected chunk_ids: [{ids}]."
            if report.affected_chunks_without_vec
            else ""
        )
        issues.append(
            f"[CRITICAL] Chunks without vector rows detected (count={report.chunks_without_vec_count}).{detail}"
            f" Re-run ingestion with 'ingester.py --force' for affected chunks."
        )
    if report.duplicate_chunk_index_count > 0:
        pairs = (
            ", ".join(
                f"({d},{c})" for d, c in report.affected_duplicate_chunk_indices[:10]
            )
            if report.affected_duplicate_chunk_indices
            else ""
        )
        detail = (
            f" Affected (doc_id, chunk_index): [{pairs}]."
            if report.affected_duplicate_chunk_indices
            else ""
        )
        issues.append(
            f"[CRITICAL] Duplicate chunk_index values detected (count={report.duplicate_chunk_index_count}).{detail}"
            f" Check ingestion logic; duplicate chunk indices indicate data corruption risk."
        )
    if report.url_level_mismatches:
        urls = ", ".join(list(report.url_level_mismatches.keys())[:5])
        truncated = " ..." if len(report.url_level_mismatches) == 5 else ""
        detail = f" Affected URLs: [{urls}{truncated}]."
        issues.append(
            f"[WARNING] URL-level inconsistency detected (mismatched URLs={len(report.url_level_mismatches)}).{detail}"
            f" Re-run ingestion for affected URLs."
        )
    return issues
