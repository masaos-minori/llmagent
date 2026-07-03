#!/usr/bin/env python3
"""db/rag_consistency.py — RAG index consistency verification."""

import dataclasses

from db.helper import SQLiteHelper
from db.models import RagConsistencyReport


def check_rag_consistency(
    db: SQLiteHelper, embed_failed: int = 0
) -> RagConsistencyReport:
    """Return row counts from chunks, chunks_fts, and chunks_vec for consistency verification.

    All queries are read-only. Orphan vec rows are chunk_id values in chunks_vec
    with no matching row in chunks (possible when the chunks_vec_ad trigger fails).
    """
    chunks = db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    fts = db.execute("SELECT COUNT(*) FROM chunks_fts_docsize").fetchone()[0]
    vec = db.execute("SELECT COUNT(*) FROM chunks_vec").fetchone()[0]
    orphan_vec_count = db.execute(
        "SELECT COUNT(*) FROM chunks_vec WHERE chunk_id NOT IN (SELECT chunk_id FROM chunks)"
    ).fetchone()[0]
    fts_gap = max(0, chunks - fts)
    fts_orphan_count = max(0, fts - chunks)

    # Collect affected identifiers (read-only; top 10 each)
    affected_chunk_ids: tuple[int, ...] | None = None
    affected_doc_ids: tuple[int, ...] | None = None
    affected_orphan_chunk_ids: tuple[int, ...] | None = None
    affected_orphan_urls: tuple[str, ...] | None = None
    if fts_gap > 0:
        rows = db.execute(
            "SELECT chunk_id FROM chunks"
            " WHERE chunk_id NOT IN (SELECT id FROM chunks_fts_docsize)"
            " ORDER BY chunk_id LIMIT 10"
        ).fetchall()
        affected_chunk_ids = tuple(r[0] for r in rows)
        doc_rows = db.execute(
            "SELECT c.doc_id FROM chunks c"
            " WHERE c.chunk_id NOT IN (SELECT id FROM chunks_fts_docsize)"
            " ORDER BY c.doc_id LIMIT 10"
        ).fetchall()
        affected_doc_ids = tuple(r[0] for r in doc_rows) if doc_rows else None
    if orphan_vec_count > 0:
        id_rows = db.execute(
            "SELECT chunk_id FROM chunks_vec"
            " WHERE chunk_id NOT IN (SELECT chunk_id FROM chunks)"
            " ORDER BY chunk_id LIMIT 10"
        ).fetchall()
        affected_orphan_chunk_ids = tuple(r[0] for r in id_rows)
        url_rows = db.execute(
            "SELECT DISTINCT d.url FROM chunks_vec cv"
            " LEFT JOIN chunks c ON cv.chunk_id = c.chunk_id"
            " LEFT JOIN documents d ON c.doc_id = d.doc_id"
            " WHERE c.chunk_id IS NULL AND d.url IS NOT NULL"
            " ORDER BY d.url LIMIT 10"
        ).fetchall()
        affected_orphan_urls = tuple(r[0] for r in url_rows) if url_rows else None

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
    )
    return dataclasses.replace(report, issues=tuple(summarize_issues(report)))


def is_consistent(report: RagConsistencyReport) -> bool:
    """Return True when fts_gap == 0, fts_orphan_count == 0, orphan_vec_count == 0, and vec == chunks."""
    return (
        report.fts_gap == 0
        and report.fts_orphan_count == 0
        and report.orphan_vec_count == 0
        and report.vec == report.chunks
    )


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
            f" gap={report.fts_gap}).{detail} Run '/db rag rebuild-fts' to repair."
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
            f" Run '/db rag rebuild-fts' immediately; orphan FTS entries indicate data loss risk."
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
    return issues
