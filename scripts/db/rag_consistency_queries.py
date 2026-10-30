#!/usr/bin/env python3
"""scripts/db/rag_consistency_queries.py — read-only SQL probes for RAG index consistency.

Probe layer for db/rag_consistency.py. This module owns every query the consistency
report is built from:
  _collect_basic_counts / _collect_document_checks: table-level row and orphan counts
  _safe_url_count_query / _collect_url_counts_and_mismatches: per-URL chunk/vec/fts counts
  _query_ids_or_none / _query_pairs: top-10 identifier readers
  _collect_affected_identifiers: the affected-identifier set for each consistency rule
  _check_read_smoke_test: one COUNT(*) read per required RAG table
  _check_fk_consistency / _check_embedding_dimension / _check_schema_recognition /
  _check_corpus_meta: the fatal-class probes added for RAGCORPUS001

Extracted from rag_consistency.py so that module keeps report assembly, the `_CHECKS`
rule registry, and issue rendering only. Each query is read-only: it returns None or an
empty mapping when the guard says the issue is absent, and sqlite3.Error is left for
check_rag_consistency() to record as a diagnostic error.
"""

import sqlite3

from db.helper import SQLiteHelper


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


def _query_ids_or_none[T](db: SQLiteHelper, sql: str) -> tuple[T, ...] | None:
    """Return the first column of a top-10 identifier query, or None when it finds no rows.

    An empty result means the issue does not exist, so callers never receive an empty tuple.
    """
    return tuple(row[0] for row in db.execute(sql).fetchall()) or None


def _query_pairs(db: SQLiteHelper, sql: str) -> tuple[tuple[int, int], ...]:
    """Return the first two columns of a top-10 identifier query."""
    return tuple((row[0], row[1]) for row in db.execute(sql).fetchall())


def _collect_affected_identifiers(
    db: SQLiteHelper,
    *,
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

    Every query reports None when it finds no rows, so an absent issue has one
    representation regardless of which guard skipped its query. The guarded
    queries only run when a count already says the issue exists.
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
        _query_ids_or_none(
            db,
            "SELECT doc_id FROM documents WHERE doc_id NOT IN (SELECT DISTINCT doc_id FROM chunks)"
            " ORDER BY doc_id LIMIT 10",
        )
        if docs_without_chunks > 0
        else None
    )
    affected_chunks_without_vec: tuple[int, ...] | None = (
        _query_ids_or_none(
            db,
            "SELECT chunk_id FROM chunks WHERE chunk_id NOT IN (SELECT chunk_id FROM chunks_vec)"
            " ORDER BY chunk_id LIMIT 10",
        )
        if chunks_without_vec > 0
        else None
    )
    affected_duplicate_chunk_indices: tuple[tuple[int, int], ...] | None = (
        (
            _query_pairs(
                db,
                "SELECT doc_id, chunk_index FROM chunks"
                " GROUP BY doc_id, chunk_index HAVING COUNT(*) > 1"
                " ORDER BY doc_id, chunk_index LIMIT 10",
            )
            or None
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


def _check_fk_consistency(db: SQLiteHelper) -> int:
    """Return the number of chunk rows whose doc_id has no matching documents row.

    0 means the chunks->documents foreign key is intact. Lets sqlite3.Error
    propagate so check_rag_consistency records a missing-table read as a
    diagnostic error (caught by the schema-recognition check).
    """
    count: int = db.execute(
        "SELECT COUNT(*) FROM chunks WHERE doc_id NOT IN (SELECT doc_id FROM documents)"
    ).fetchone()[0]
    return count


def _check_embedding_dimension(db: SQLiteHelper, expected_dims: int) -> bool:
    """Return True when stored embedding vectors match the configured dimension.

    A vec0 vector is stored as float32, so the byte length divided by 4 is the
    dimension. An empty chunks_vec has nothing to contradict the config and is
    therefore clean.
    """
    row = db.execute("SELECT length(embedding) FROM chunks_vec LIMIT 1").fetchone()
    if row is None or row[0] is None:
        return True
    dim_bytes: int = row[0]
    return (dim_bytes // 4) == expected_dims


def _check_schema_recognition(db: SQLiteHelper) -> bool:
    """Return True when every expected RAG table is present.

    A missing required table means the schema shape is unrecognised, which is the
    fatal class check_rag_consistency guards against. Mirrors the required-table
    set of _check_read_smoke_test.
    """
    expected_tables = ("documents", "chunks", "chunks_vec", "chunks_fts_docsize")
    present = {
        name
        for name, type_ in db.execute(
            "SELECT name, type FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    return all(table in present for table in expected_tables)


def _check_corpus_meta(db: SQLiteHelper) -> bool:
    """Return True when the single-row rag_corpus_meta table is well formed.

    Presence of exactly one row with a non-null corpus_id marks a verifiable
    corpus generation. A missing or multi-row table is the unverifiable-generation
    fatal class; a missing table is reported as False rather than raised so
    check_rag_consistency can apply the ledger-based pre-migration tolerance.
    """
    try:
        row_count = db.execute("SELECT COUNT(*) FROM rag_corpus_meta").fetchone()[0]
    except sqlite3.Error:
        return False
    if row_count != 1:
        return False
    corpus_id = db.execute("SELECT corpus_id FROM rag_corpus_meta LIMIT 1").fetchone()[
        0
    ]
    return corpus_id is not None
