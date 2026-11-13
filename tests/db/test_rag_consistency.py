"""tests/test_rag_consistency.py
Regression tests for check_rag_consistency(), is_consistent(), and summarize_issues()
in db/maintenance.py.
"""

from __future__ import annotations

import re
import sqlite3
from typing import Any

import pytest
from db.models import RagConsistencyReport
from db.rag_consistency import check_rag_consistency, is_consistent, summarize_issues
from db.schema_sql import build_rag_schema_sql

# ── In-memory SQLite helper ───────────────────────────────────────────────────


class _FakeSQLiteHelper:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def fetchall(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        return self.conn.execute(sql, params).fetchall()

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self.conn.execute(sql, params)

    def commit(self) -> None:
        self.conn.commit()


# ── Schema (derived from the canonical DDL SSOT; chunks_vec replaced with a
# plain table carrying a valid 1024-dim embedding BLOB, so the fixture builds
# and the embedding probe runs without the vec0 extension; UNK-01 compares
# virtual tables by name only) ────────────────────────────────────────────────

#: Concrete embedding dimension for fixtures. Must match get_embedding_dims()
#: (Qwen3, 1024) so the embedding probe passes on populated fixtures.
EMBED_DIMS = 1024

_VEC0_PLAIN_SUBSTITUTES: dict[str, str] = {
    "chunks_vec": "CREATE TABLE chunks_vec (chunk_id INTEGER PRIMARY KEY, embedding BLOB)",
}

_VEC0_STMT_RE = re.compile(
    r"CREATE VIRTUAL TABLE IF NOT EXISTS (\w+) USING vec0\(.*?\n    \)",
    re.DOTALL,
)


def _fallback_from_canonical(ddl: str) -> str:
    """Canonical DDL with each vec0 virtual table replaced by a plain-table
    stand-in. The fingerprint compares virtual tables by name only (UNK-01), so
    the stand-ins satisfy the shape gate without the sqlite-vec extension."""

    def sub(m: re.Match[str]) -> str:
        name = m.group(1)
        if name not in _VEC0_PLAIN_SUBSTITUTES:
            raise AssertionError(f"no plain stand-in defined for vec0 table {name!r}")
        return _VEC0_PLAIN_SUBSTITUTES[name]

    return _VEC0_STMT_RE.sub(sub, ddl)


_RAG_SCHEMA = _fallback_from_canonical(build_rag_schema_sql(EMBED_DIMS))


def _make_rag_db() -> _FakeSQLiteHelper:
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        _RAG_SCHEMA
    )  # executescript handles trigger bodies with semicolons
    conn.commit()
    return _FakeSQLiteHelper(conn)


def _insert_doc(db: _FakeSQLiteHelper) -> int:
    cur = db.execute(
        "INSERT INTO documents (url, title, lang, fetched_at) VALUES (?, ?, 'en',"
        " '2026-01-01T00:00:00Z')",
        ("https://example.com/doc", "Test Doc"),
    )
    db.commit()
    assert cur.lastrowid is not None
    return cur.lastrowid


def _insert_chunk(db: _FakeSQLiteHelper, doc_id: int, content: str) -> int:
    """Insert a chunk with the next free chunk_index for its document.

    The canonical schema enforces UNIQUE(doc_id, chunk_index); tests that need
    a duplicate index insert explicitly.
    """
    next_index = db.execute(
        "SELECT COALESCE(MAX(chunk_index) + 1, 0) FROM chunks WHERE doc_id = ?",
        (doc_id,),
    ).fetchone()[0]
    cur = db.execute(
        "INSERT INTO chunks (doc_id, content, chunk_index) VALUES (?, ?, ?)",
        (doc_id, content, next_index),
    )
    db.commit()
    assert cur.lastrowid is not None
    return cur.lastrowid


def _insert_vec(db: _FakeSQLiteHelper, chunk_id: int) -> None:
    """Insert a vec row with a valid 1024-dim (4096-byte) float32 embedding BLOB.

    The embedding probe reads length(embedding) // 4; a valid blob keeps healthy
    fixtures verified instead of raising on a missing column. Commits stay with
    the callers, matching the raw INSERT calls this helper replaces.
    """
    db.execute(
        "INSERT INTO chunks_vec (chunk_id, embedding) VALUES (?, ?)",
        (chunk_id, bytes(1024 * 4)),
    )


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestCollectUrlCountsAndMismatchesErrorHandling:
    """Characterization tests for the per-query try/except fallback in
    _collect_url_counts_and_mismatches — previously uncovered."""

    def test_missing_fts_table_falls_back_to_zero_fts_count(self) -> None:
        from db.rag_consistency_queries import _collect_url_counts_and_mismatches

        db = _make_rag_db()
        doc_id = _insert_doc(db)
        _insert_chunk(db, doc_id, "hello world")
        db.execute("DROP TABLE chunks_fts")
        db.commit()

        result = _collect_url_counts_and_mismatches(db)

        assert result["https://example.com/doc"]["chunk_count"] == 1
        assert result["https://example.com/doc"]["fts_count"] == 0

    def test_missing_documents_table_returns_empty_mismatches(self) -> None:
        from db.rag_consistency_queries import _collect_url_counts_and_mismatches

        db = _make_rag_db()
        db.execute("DROP TABLE documents")
        db.commit()

        result = _collect_url_counts_and_mismatches(db)

        assert result == {}


class TestRagConsistency:
    def test_consistency_report_counts_match(self) -> None:
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "hello world")
        _insert_vec(db, chunk_id)
        db.commit()

        report = check_rag_consistency(db)  # type: ignore[arg-type]  # _FakeSQLiteHelper is structurally compatible: exposes execute() and commit()
        assert report.chunks == 1
        assert report.fts == 1
        assert report.vec == 1
        assert report.orphan_vec_count == 0
        assert report.fts_gap == 0
        assert report.fts_orphan_count == 0
        assert isinstance(report, RagConsistencyReport)
        assert is_consistent(report)
        assert summarize_issues(report) == []

    def test_is_consistent_false_on_diagnostic_errors(self) -> None:
        from db.models import RagConsistencyReport

        report = RagConsistencyReport(
            chunks=1,
            fts=1,
            vec=1,
            orphan_vec_count=0,
            fts_gap=0,
            fts_orphan_count=0,
            embed_failed=0,
            issues=(),
            diagnostic_errors=("Test error",),
        )
        assert not is_consistent(report)

        db = _make_rag_db()
        _insert_vec(db, 99999)
        db.commit()

        report = check_rag_consistency(db)  # type: ignore[arg-type]  # _FakeSQLiteHelper is structurally compatible: exposes execute() and commit()
        assert report.orphan_vec_count == 1
        assert not is_consistent(report)
        issues = summarize_issues(report)
        assert any("Orphan vec" in i for i in issues)

    def test_fts_gap_after_clean_delete(self) -> None:
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "text to delete")
        _insert_vec(db, chunk_id)
        db.execute("DELETE FROM chunks WHERE chunk_id = ?", (chunk_id,))
        db.execute("DELETE FROM chunks_vec WHERE chunk_id = ?", (chunk_id,))
        db.commit()

        report = check_rag_consistency(db)  # type: ignore[arg-type]  # _FakeSQLiteHelper is structurally compatible: exposes execute() and commit()
        assert report.chunks == 0
        assert report.fts == 0
        assert report.fts_gap == 0
        assert not is_consistent(report)
        assert report.documents_without_chunks_count > 0

    def test_fts_gap_detected_after_broken_delete(self) -> None:
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "orphaned fts row")
        # Simulate broken trigger: manually remove FTS entry without touching chunks
        db.execute(
            "INSERT INTO chunks_fts (chunks_fts, rowid, content) VALUES ('delete', ?, ?)",
            (chunk_id, "orphaned fts row"),
        )
        db.commit()

        report = check_rag_consistency(db)  # type: ignore[arg-type]  # _FakeSQLiteHelper is structurally compatible: exposes execute() and commit()
        assert report.chunks == 1
        assert report.fts == 0
        assert report.fts_gap == 1
        assert not is_consistent(report)
        issues = summarize_issues(report)
        assert any("FTS gap" in i for i in issues)

    def test_consistency_after_force_reinsert(self) -> None:
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "reinsert content")
        _insert_vec(db, chunk_id)
        db.commit()

        # Force-reinsert: delete order vec → chunks → documents
        db.execute("DELETE FROM chunks_vec WHERE chunk_id = ?", (chunk_id,))
        db.execute("DELETE FROM chunks WHERE chunk_id = ?", (chunk_id,))
        db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        db.commit()

        # Re-insert
        doc_id2 = _insert_doc(db)
        chunk_id2 = _insert_chunk(db, doc_id2, "reinsert content")
        _insert_vec(db, chunk_id2)
        db.commit()

        report = check_rag_consistency(db)  # type: ignore[arg-type]  # _FakeSQLiteHelper is structurally compatible: exposes execute() and commit()
        assert report.chunks == 1
        assert report.fts == 1
        assert report.vec == 1
        assert is_consistent(report)


class TestRagConsistencySeverity:
    def test_fts_orphan_detected_when_fts_exceeds_chunks(self) -> None:
        # Simulate stale FTS entries (fts > chunks): insert chunk then delete only the
        # chunks row without updating the FTS index.
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "stale fts content")
        # Remove from chunks without triggering the ad trigger (bypass cascade)
        db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        # FTS entry still exists but chunk is gone (ON DELETE CASCADE removed the row,
        # but the ad trigger ran correctly). Re-insert FTS entry manually to simulate drift.
        db.execute(
            "INSERT INTO chunks_fts (rowid, content) VALUES (?, ?)",
            (chunk_id + 1000, "ghost entry"),
        )
        db.commit()

        report = check_rag_consistency(db)  # type: ignore[arg-type]
        assert report.fts > report.chunks
        assert report.fts_orphan_count > 0
        assert not is_consistent(report)
        issues = summarize_issues(report)
        assert any(
            "[CRITICAL]" in i and "FTS index has more entries" in i for i in issues
        )

    def test_summarize_issues_fts_gap_has_warning_prefix(self) -> None:
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "gap test")
        db.execute(
            "INSERT INTO chunks_fts (chunks_fts, rowid, content) VALUES ('delete', ?, ?)",
            (chunk_id, "gap test"),
        )
        db.commit()

        issues = summarize_issues(check_rag_consistency(db))  # type: ignore[arg-type]
        assert any("[WARNING]" in i and "FTS gap" in i for i in issues)

    def test_summarize_issues_orphan_vec_has_critical_prefix(self) -> None:
        db = _make_rag_db()
        _insert_vec(db, 99999)
        db.commit()

        issues = summarize_issues(check_rag_consistency(db))  # type: ignore[arg-type]
        assert any("[CRITICAL]" in i and "Orphan vec" in i for i in issues)

    def test_summarize_issues_fts_gap_includes_rebuild_guidance(self) -> None:
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "rebuild guidance test")
        db.execute(
            "INSERT INTO chunks_fts (chunks_fts, rowid, content) VALUES ('delete', ?, ?)",
            (chunk_id, "rebuild guidance test"),
        )
        db.commit()

        issues = summarize_issues(check_rag_consistency(db))  # type: ignore[arg-type]
        assert any("/session rag-rebuild-fts" in i for i in issues)

    def test_summarize_issues_orphan_vec_includes_force_guidance(self) -> None:
        db = _make_rag_db()
        _insert_vec(db, 88888)
        db.commit()

        issues = summarize_issues(check_rag_consistency(db))  # type: ignore[arg-type]
        assert any("--force" in i for i in issues)

    def test_fts_gap_includes_doc_ids(self) -> None:
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "doc id test")
        db.execute(
            "INSERT INTO chunks_fts (chunks_fts, rowid, content) VALUES ('delete', ?, ?)",
            (chunk_id, "doc id test"),
        )
        db.commit()

        report = check_rag_consistency(db)  # type: ignore[arg-type]
        assert report.fts_gap == 1
        assert report.affected_doc_ids is not None
        assert doc_id in report.affected_doc_ids
        assert report.affected_chunk_ids is not None
        assert chunk_id in report.affected_chunk_ids

    def test_fts_orphan_no_doc_ids_available(self) -> None:
        # Simulate stale FTS entries (fts > chunks): insert chunk then delete only the
        # chunks row without updating the FTS index.
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "stale fts content")
        # Remove from chunks without triggering the ad trigger (bypass cascade)
        db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        # FTS entry still exists but chunk is gone (ON DELETE CASCADE removed the row,
        # but the ad trigger ran correctly). Re-insert FTS entry manually to simulate drift.
        db.execute(
            "INSERT INTO chunks_fts (rowid, content) VALUES (?, ?)",
            (chunk_id + 1000, "ghost entry"),
        )
        db.commit()

        report = check_rag_consistency(db)  # type: ignore[arg-type]
        assert report.fts_orphan_count > 0
        # affected_doc_ids is None because chunks and documents rows are gone
        assert report.affected_doc_ids is None

    def test_vec_chunk_mismatch_detected(self) -> None:
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        _insert_chunk(db, doc_id, "vec mismatch")
        # Insert into chunks but not chunks_vec
        db.commit()

        report = check_rag_consistency(db)  # type: ignore[arg-type]
        assert report.chunks == 1
        assert report.vec == 0
        assert report.vec != report.chunks
        assert not is_consistent(report)
        issues = summarize_issues(report)
        assert any("Vector count mismatch" in i for i in issues)

    def test_vec_chunk_mismatch_includes_repair_guidance(self) -> None:
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        _insert_chunk(db, doc_id, "vec mismatch repair")
        db.commit()

        report = check_rag_consistency(db)  # type: ignore[arg-type]
        issues = summarize_issues(report)
        assert any("ingester.py --force" in i for i in issues)

    def test_fts_orphan_does_not_report_fts_gap_doc_ids(self) -> None:
        """FTS orphan_count > 0 with fts_gap == 0 should not include 'Affected doc_ids' in issue string."""
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "stale fts content")
        db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        db.execute(
            "INSERT INTO chunks_fts (rowid, content) VALUES (?, ?)",
            (chunk_id + 1000, "ghost entry"),
        )
        db.commit()

        report = check_rag_consistency(db)  # type: ignore[arg-type]
        assert report.fts_orphan_count > 0
        assert report.fts_gap == 0
        assert report.affected_doc_ids is None
        issues = summarize_issues(report)
        fts_orphan_issue = next(
            (
                i
                for i in issues
                if "[CRITICAL]" in i and "FTS index has more entries" in i
            ),
            None,
        )
        assert fts_orphan_issue is not None
        assert "Affected doc_ids" not in fts_orphan_issue

    def test_summarize_issues_never_references_removed_db_command(self) -> None:
        """Drift guard: no summarize_issues() output may reference a removed '/db'-prefixed command."""
        all_issues: list[str] = []

        # fts_gap > 0
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "drift guard fts gap")
        db.execute(
            "INSERT INTO chunks_fts (chunks_fts, rowid, content) VALUES ('delete', ?, ?)",
            (chunk_id, "drift guard fts gap"),
        )
        db.commit()
        all_issues += summarize_issues(check_rag_consistency(db))  # type: ignore[arg-type]

        # fts_orphan_count > 0
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "drift guard fts orphan")
        db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        db.execute(
            "INSERT INTO chunks_fts (rowid, content) VALUES (?, ?)",
            (chunk_id + 1000, "ghost entry"),
        )
        db.commit()
        all_issues += summarize_issues(check_rag_consistency(db))  # type: ignore[arg-type]

        # orphan_vec_count > 0
        db = _make_rag_db()
        _insert_vec(db, 77777)
        db.commit()
        all_issues += summarize_issues(check_rag_consistency(db))  # type: ignore[arg-type]

        # vec != chunks
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        _insert_chunk(db, doc_id, "drift guard vec mismatch")
        db.commit()
        all_issues += summarize_issues(check_rag_consistency(db))  # type: ignore[arg-type]

        # Each scenario contributes at least one issue string (some scenarios also trigger
        # a secondary "Vector count mismatch" issue as a side effect of the fixture not
        # populating chunks_vec, e.g. the fts_gap/fts_orphan setups) — a scenario silently
        # producing zero issues would indicate check_rag_consistency() stopped detecting it.
        assert len(all_issues) >= 4, (
            "expected at least one issue string per triggered scenario"
        )
        assert not any("/db " in i for i in all_issues)
        assert not any("/db rag" in i for i in all_issues)


class TestNewConsistencyChecks:
    def test_documents_without_chunks_detected(self) -> None:
        """Documents that exist without any chunks should be flagged."""
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        # Don't insert any chunks for this document

        report = check_rag_consistency(db)  # type: ignore[arg-type]
        assert report.documents_without_chunks_count == 1
        assert report.affected_docs_without_chunks is not None
        assert doc_id in report.affected_docs_without_chunks
        assert not is_consistent(report)
        issues = summarize_issues(report)
        assert any("[WARNING]" in i and "Documents without chunks" in i for i in issues)

    def test_chunks_without_vectors_detected(self) -> None:
        """Chunks that lack corresponding vector rows should be flagged."""
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "text without vector")
        # Don't insert into chunks_vec

        report = check_rag_consistency(db)  # type: ignore[arg-type]
        assert report.chunks_without_vec_count == 1
        assert report.affected_chunks_without_vec is not None
        assert chunk_id in report.affected_chunks_without_vec
        assert not is_consistent(report)
        issues = summarize_issues(report)
        assert any("[CRITICAL]" in i and "Chunks without vector" in i for i in issues)

    def test_duplicate_chunk_index_detected(self) -> None:
        """Duplicate chunk_index values within the same document should be flagged.

        The canonical UNIQUE(doc_id, chunk_index) makes duplicates uninsertable
        and the fingerprint gate refuses a rag schema without that UNIQUE
        (REQ-003), so the duplicate probe runs on a legacy (pre-UNIQUE) schema
        directly and the classification path runs on a synthetic report.
        """
        from db.rag_consistency_queries import _collect_document_checks

        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE documents (doc_id INTEGER PRIMARY KEY)")
        conn.execute(
            "CREATE TABLE chunks (chunk_id INTEGER PRIMARY KEY, doc_id INTEGER,"
            " content TEXT, chunk_index INTEGER)"
        )
        conn.execute("CREATE TABLE chunks_vec (chunk_id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO documents VALUES (1)")
        conn.execute(
            "INSERT INTO chunks (doc_id, content, chunk_index) VALUES"
            " (1, 'first chunk', 1), (1, 'second chunk', 1)"
        )
        legacy = _FakeSQLiteHelper(conn)
        _docs_without_chunks, _chunks_without_vec, duplicate_count = (
            _collect_document_checks(legacy)
        )
        assert duplicate_count == 1

        report = _report(
            duplicate_chunk_index_count=1,
            affected_duplicate_chunk_indices=((1, 1),),
        )
        assert not is_consistent(report)
        issues = summarize_issues(report)
        assert any("[CRITICAL]" in i and "Duplicate chunk_index" in i for i in issues)

    def test_url_level_mismatches_detected(self) -> None:
        """URLs with mismatched chunk/vector/FTS counts should be flagged."""
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        _insert_chunk(db, doc_id, "url mismatch test")
        # Don't insert into chunks_vec — creates chunk_count != vec_count

        report = check_rag_consistency(db)  # type: ignore[arg-type]
        assert report.url_level_mismatches is not None
        assert len(report.url_level_mismatches) > 0
        assert "Affected URLs" in str(summarize_issues(report))

    def test_existing_checks_still_work(self) -> None:
        """Existing checks should still work after adding new ones."""
        db = _make_rag_db()
        _insert_vec(db, 99999)
        db.commit()
        report = check_rag_consistency(db)  # type: ignore[arg-type]
        assert report.orphan_vec_count == 1
        assert not is_consistent(report)

        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "fts gap test")
        db.execute(
            "INSERT INTO chunks_fts (chunks_fts, rowid, content) VALUES ('delete', ?, ?)",
            (chunk_id, "fts gap test"),
        )
        db.commit()
        report = check_rag_consistency(db)  # type: ignore[arg-type]
        assert report.fts_gap == 1
        assert not is_consistent(report)

    def test_is_consistent_false_on_new_failures(self) -> None:
        """is_consistent() should return False when any new check fails."""
        db = _make_rag_db()
        _insert_doc(db)
        report = check_rag_consistency(db)  # type: ignore[arg-type]
        assert not is_consistent(report)

    def test_is_consistent_true_when_all_pass(self) -> None:
        """is_consistent() should return True when all checks pass."""
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "consistent test")
        _insert_vec(db, chunk_id)
        db.commit()

        report = check_rag_consistency(db)  # type: ignore[arg-type]
        assert is_consistent(report)
        assert report.documents_without_chunks_count == 0
        assert report.chunks_without_vec_count == 0
        assert report.duplicate_chunk_index_count == 0
        assert not report.url_level_mismatches

    def test_url_mismatch_includes_repair_guidance(self) -> None:
        """URL-level mismatch issue should include repair guidance."""
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        _insert_chunk(db, doc_id, "url repair guidance test")
        # Don't insert into chunks_vec — creates chunk_count != vec_count

        issues = summarize_issues(check_rag_consistency(db))  # type: ignore[arg-type]
        assert any("ingester.py --force" in i for i in issues)

    def test_new_fields_have_defaults(self) -> None:
        """New fields should have default values for backward compatibility."""
        from db.models import RagConsistencyReport

        report = RagConsistencyReport(
            chunks=1,
            fts=1,
            vec=1,
            orphan_vec_count=0,
            fts_gap=0,
            fts_orphan_count=0,
            embed_failed=0,
            affected_chunk_ids=None,
            affected_doc_ids=None,
            affected_orphan_chunk_ids=None,
            affected_orphan_urls=None,
        )
        assert report.documents_without_chunks_count == 0
        assert report.chunks_without_vec_count == 0
        assert report.duplicate_chunk_index_count == 0
        assert report.url_level_mismatches is None


# ── Characterization tests for the identifier detail rendering ────────────────
#
# summarize_issues() renders each issue from a different identifier source, and the
# truncation markers are not uniform: doc_ids/chunk_ids cut at 10 and mark at 10,
# orphan URLs cut at 5 but mark only at 10, and the new-check identifiers never
# mark. These pin the exact text of the branches the suite left uncovered.


def _report(**overrides: Any) -> RagConsistencyReport:
    """Return a report whose only issue is what *overrides* introduces.

    vec mirrors chunks unless overridden, so the vector-mismatch issue stays silent
    in tests that target a different check.
    """
    base: dict[str, Any] = {
        "chunks": 0,
        "fts": 0,
        "orphan_vec_count": 0,
        "fts_gap": 0,
        "fts_orphan_count": 0,
        "read_smoke_test_ok": True,
    }
    base.update(overrides)
    base.setdefault("vec", base["chunks"])
    return RagConsistencyReport(**base)


def _only_issue(report: RagConsistencyReport) -> str:
    """Return the single issue *report* produces."""
    issues = summarize_issues(report)
    assert len(issues) == 1
    return issues[0]


class TestFtsGapIssueDetail:
    """doc_ids win; chunk_ids are the fallback; both mark at exactly 10."""

    def test_doc_ids_take_precedence(self) -> None:
        report = _report(
            chunks=3, fts=2, fts_gap=1, affected_doc_ids=(7,), affected_chunk_ids=(1, 3)
        )

        assert _only_issue(report) == (
            "[WARNING] FTS gap detected (chunks=3, fts=2, gap=1). Affected doc_ids: [7]. "
            "Run '/session rag-rebuild-fts' to repair."
        )

    def test_chunk_ids_are_used_when_doc_ids_are_unavailable(self) -> None:
        report = _report(chunks=3, fts=2, fts_gap=1, affected_chunk_ids=(1, 3))

        assert _only_issue(report) == (
            "[WARNING] FTS gap detected (chunks=3, fts=2, gap=1). Affected chunk_ids: [1, 3]. "
            "Run '/session rag-rebuild-fts' to repair."
        )

    def test_ten_identifiers_add_the_ellipsis(self) -> None:
        report = _report(
            chunks=11, fts=1, fts_gap=10, affected_doc_ids=tuple(range(1, 11))
        )

        assert _only_issue(report) == (
            "[WARNING] FTS gap detected (chunks=11, fts=1, gap=10). "
            "Affected doc_ids: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10 ...]. "
            "Run '/session rag-rebuild-fts' to repair."
        )

    def test_nine_identifiers_do_not_add_the_ellipsis(self) -> None:
        report = _report(
            chunks=10, fts=1, fts_gap=9, affected_doc_ids=tuple(range(1, 10))
        )

        assert _only_issue(report) == (
            "[WARNING] FTS gap detected (chunks=10, fts=1, gap=9). "
            "Affected doc_ids: [1, 2, 3, 4, 5, 6, 7, 8, 9]. "
            "Run '/session rag-rebuild-fts' to repair."
        )

    def test_no_identifiers_render_no_affected_clause(self) -> None:
        report = _report(chunks=3, fts=2, fts_gap=1)

        assert _only_issue(report) == (
            "[WARNING] FTS gap detected (chunks=3, fts=2, gap=1). "
            "Run '/session rag-rebuild-fts' to repair."
        )


class TestFtsOrphanIssueDetail:
    """Three identifier sources, then a static clause when none are available."""

    _TAIL = (
        " Run '/session rag-rebuild-fts' immediately; "
        "orphan FTS entries indicate data loss risk."
    )

    def test_orphan_chunk_ids(self) -> None:
        report = _report(
            chunks=2, fts=3, fts_orphan_count=1, affected_orphan_chunk_ids=(4, 5)
        )

        assert _only_issue(report) == (
            "[CRITICAL] FTS index has more entries than chunks (fts=3, chunks=2). "
            "Affected chunk_ids: [4, 5]." + self._TAIL
        )

    def test_orphan_urls_are_used_when_chunk_ids_are_unavailable(self) -> None:
        report = _report(
            chunks=2,
            fts=3,
            fts_orphan_count=1,
            affected_orphan_urls=("https://a", "https://b"),
        )

        assert _only_issue(report) == (
            "[CRITICAL] FTS index has more entries than chunks (fts=3, chunks=2). "
            "Affected URLs: [https://a, https://b]." + self._TAIL
        )

    def test_seven_urls_are_cut_at_five_without_the_ellipsis(self) -> None:
        """The URL list is cut at 5 while the marker looks for 10: a latent mismatch."""
        urls = tuple(f"https://u{i}" for i in range(7))
        report = _report(chunks=2, fts=3, fts_orphan_count=1, affected_orphan_urls=urls)

        assert _only_issue(report) == (
            "[CRITICAL] FTS index has more entries than chunks (fts=3, chunks=2). "
            "Affected URLs: [https://u0, https://u1, https://u2, https://u3, https://u4]."
            + self._TAIL
        )

    def test_ten_urls_add_the_ellipsis(self) -> None:
        urls = tuple(f"https://u{i}" for i in range(10))
        report = _report(chunks=2, fts=3, fts_orphan_count=1, affected_orphan_urls=urls)

        assert _only_issue(report) == (
            "[CRITICAL] FTS index has more entries than chunks (fts=3, chunks=2). "
            "Affected URLs: [https://u0, https://u1, https://u2, https://u3, https://u4 ...]."
            + self._TAIL
        )

    def test_static_clause_when_no_identifier_is_available(self) -> None:
        report = _report(chunks=2, fts=3, fts_orphan_count=1)

        assert _only_issue(report) == (
            "[CRITICAL] FTS index has more entries than chunks (fts=3, chunks=2). "
            "Chunk-level identifiers unavailable (FTS orphans have no parent chunk rows)."
            + self._TAIL
        )

    def test_available_chunk_ids_suppress_the_static_clause(self) -> None:
        """affected_chunk_ids is only consulted to decide whether the fallback text is true."""
        report = _report(chunks=2, fts=3, fts_orphan_count=1, affected_chunk_ids=(1, 2))

        assert _only_issue(report) == (
            "[CRITICAL] FTS index has more entries than chunks (fts=3, chunks=2)."
            + self._TAIL
        )


class TestOrphanVecAndVectorMismatchDetail:
    """Both share the URL-first / chunk_ids-fallback shape, and neither marks truncation."""

    def test_orphan_vec_prefers_urls(self) -> None:
        report = _report(
            orphan_vec_count=2,
            affected_orphan_urls=("https://a", "https://b"),
            affected_orphan_chunk_ids=(4, 5),
        )

        assert _only_issue(report) == (
            "[CRITICAL] Orphan vec rows detected (count=2). "
            "Affected URLs: [https://a, https://b]. "
            "Re-run ingestion with 'ingester.py --force' for affected URLs."
        )

    def test_orphan_vec_urls_cut_at_five_and_mark_at_ten(self) -> None:
        urls = tuple(f"https://u{i}" for i in range(10))
        report = _report(orphan_vec_count=10, affected_orphan_urls=urls)

        assert _only_issue(report) == (
            "[CRITICAL] Orphan vec rows detected (count=10). "
            "Affected URLs: [https://u0, https://u1, https://u2, https://u3, https://u4 ...]. "
            "Re-run ingestion with 'ingester.py --force' for affected URLs."
        )

    def test_orphan_vec_chunk_ids_never_mark_truncation(self) -> None:
        report = _report(
            orphan_vec_count=10, affected_orphan_chunk_ids=tuple(range(1, 11))
        )

        assert _only_issue(report) == (
            "[CRITICAL] Orphan vec rows detected (count=10). "
            "Affected chunk_ids: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]. "
            "Re-run ingestion with 'ingester.py --force' for affected URLs."
        )

    def test_vector_mismatch_prefers_urls(self) -> None:
        report = _report(chunks=2, vec=1, affected_orphan_urls=("https://a",))

        assert _only_issue(report) == (
            "[WARNING] Vector count mismatch (chunks=2, vec=1). Affected URLs: [https://a]. "
            "Re-run ingestion with 'ingester.py --force' for affected URLs."
        )

    def test_vector_mismatch_falls_back_to_chunk_ids(self) -> None:
        report = _report(chunks=2, vec=1, affected_orphan_chunk_ids=(4, 5))

        assert _only_issue(report) == (
            "[WARNING] Vector count mismatch (chunks=2, vec=1). Affected chunk_ids: [4, 5]. "
            "Re-run ingestion with 'ingester.py --force' for affected URLs."
        )

    def test_vector_mismatch_without_identifiers(self) -> None:
        report = _report(chunks=2, vec=1)

        assert _only_issue(report) == (
            "[WARNING] Vector count mismatch (chunks=2, vec=1). "
            "Re-run ingestion with 'ingester.py --force' for affected URLs."
        )


class TestNewCheckIssueDetails:
    """The document-level checks render identifiers without any truncation marker."""

    def test_documents_without_chunks(self) -> None:
        report = _report(
            documents_without_chunks_count=2, affected_docs_without_chunks=(4, 5)
        )

        assert _only_issue(report) == (
            "[WARNING] Documents without chunks detected (count=2). Affected doc_ids: [4, 5]. "
            "Re-run ingestion for affected documents."
        )

    def test_documents_without_chunks_without_identifiers(self) -> None:
        report = _report(documents_without_chunks_count=2)

        assert _only_issue(report) == (
            "[WARNING] Documents without chunks detected (count=2). "
            "Re-run ingestion for affected documents."
        )

    def test_chunks_without_vec(self) -> None:
        report = _report(chunks_without_vec_count=1, affected_chunks_without_vec=(9,))

        assert _only_issue(report) == (
            "[CRITICAL] Chunks without vector rows detected (count=1). Affected chunk_ids: [9]. "
            "Re-run ingestion with 'ingester.py --force' for affected chunks."
        )

    def test_chunks_without_vec_without_identifiers(self) -> None:
        report = _report(chunks_without_vec_count=1)

        assert _only_issue(report) == (
            "[CRITICAL] Chunks without vector rows detected (count=1). "
            "Re-run ingestion with 'ingester.py --force' for affected chunks."
        )

    def test_duplicate_chunk_indices_render_pairs(self) -> None:
        report = _report(
            duplicate_chunk_index_count=2,
            affected_duplicate_chunk_indices=((1, 1), (2, 3)),
        )

        assert _only_issue(report) == (
            "[CRITICAL] Duplicate chunk_index values detected (count=2). "
            "Affected (doc_id, chunk_index): [(1,1), (2,3)]. "
            "Check ingestion logic; duplicate chunk indices indicate data corruption risk."
        )

    def test_duplicate_chunk_indices_without_identifiers(self) -> None:
        report = _report(duplicate_chunk_index_count=2)

        assert _only_issue(report) == (
            "[CRITICAL] Duplicate chunk_index values detected (count=2). "
            "Check ingestion logic; duplicate chunk indices indicate data corruption risk."
        )


class TestUrlMismatchIssueDetail:
    """url_level_mismatches is a mapping: the keys are the affected URLs."""

    @staticmethod
    def _mismatches(count: int) -> dict[str, dict[str, int]]:
        return {
            f"https://u{i}": {"chunk_count": 1, "vec_count": 1, "fts_count": 1}
            for i in range(count)
        }

    def test_four_urls_render_without_the_ellipsis(self) -> None:
        report = _report(url_level_mismatches=self._mismatches(4))

        assert _only_issue(report) == (
            "[WARNING] URL-level inconsistency detected (mismatched URLs=4). "
            "Affected URLs: [https://u0, https://u1, https://u2, https://u3]. "
            "Re-run ingestion for affected URLs."
        )

    def test_exactly_five_urls_mark_truncation(self) -> None:
        report = _report(url_level_mismatches=self._mismatches(5))

        assert _only_issue(report) == (
            "[WARNING] URL-level inconsistency detected (mismatched URLs=5). "
            "Affected URLs: [https://u0, https://u1, https://u2, https://u3, https://u4 ...]. "
            "Re-run ingestion for affected URLs."
        )

    def test_empty_mapping_produces_no_issue(self) -> None:
        assert summarize_issues(_report(url_level_mismatches={})) == []


class TestIssueOrder:
    """Every issue is emitted in the fixed order the repair guidance assumes."""

    def test_all_eight_issues_in_order(self) -> None:
        report = _report(
            chunks=5,
            fts=4,
            vec=3,
            orphan_vec_count=1,
            fts_gap=1,
            fts_orphan_count=1,
            documents_without_chunks_count=1,
            chunks_without_vec_count=1,
            duplicate_chunk_index_count=1,
            url_level_mismatches={
                "https://u0": {"chunk_count": 1, "vec_count": 1, "fts_count": 1}
            },
        )

        assert [issue.split(" (")[0] for issue in summarize_issues(report)] == [
            "[WARNING] FTS gap detected",
            "[CRITICAL] FTS index has more entries than chunks",
            "[CRITICAL] Orphan vec rows detected",
            "[WARNING] Vector count mismatch",
            "[WARNING] Documents without chunks detected",
            "[CRITICAL] Chunks without vector rows detected",
            "[CRITICAL] Duplicate chunk_index values detected",
            "[WARNING] URL-level inconsistency detected",
        ]

    def test_consistent_report_produces_no_issues(self) -> None:
        assert summarize_issues(_report(chunks=2, fts=2, vec=2)) == []


class TestCollectionFailureDiagnostics:
    """A missing table is recorded per collection stage instead of aborting the report."""

    @staticmethod
    def _db_without(*tables: str) -> _FakeSQLiteHelper:
        db = _make_rag_db()
        for table in tables:
            db.execute(f"DROP TABLE {table}")
        db.commit()
        return db

    def test_missing_chunks_table_raises_fingerprint_refusal(self) -> None:
        """REQ-003: a rag database missing a canonical table raises, not reports."""
        db = self._db_without("chunks")

        with pytest.raises(RuntimeError, match="missing table 'chunks'"):
            check_rag_consistency(db)  # type: ignore[arg-type]

    def test_missing_documents_table_leaves_url_mismatches_empty(self) -> None:
        """_safe_url_count_query() swallows per-query failures, so the URL stage never raises."""
        db = self._db_without("documents")

        report = check_rag_consistency(db)  # type: ignore[arg-type]

        prefixes = {error.split(":")[0] for error in report.diagnostic_errors}
        assert prefixes == {
            "Document checks collection failed",
            "Affected identifiers collection failed",
            "FK consistency probe failed",
        }
        assert report.url_level_mismatches is None
        assert report.read_smoke_test_ok is False
        assert is_consistent(report) is False

    def test_missing_vec_table_raises_fingerprint_refusal(self) -> None:
        """REQ-003: dropping the (name-only) vec table is a fingerprint finding."""
        db = self._db_without("chunks_vec")

        with pytest.raises(RuntimeError, match="missing table 'chunks_vec'"):
            check_rag_consistency(db)  # type: ignore[arg-type]

    def test_a_consistent_database_records_no_diagnostics(self) -> None:
        report = check_rag_consistency(_make_rag_db())  # type: ignore[arg-type]

        assert report.diagnostic_errors is None
        assert report.read_smoke_test_ok is True
        assert is_consistent(report) is True


# ── Fail-closed probe-error tests ─────────────────────────────────────────────


class _RaisingSQLiteHelper(_FakeSQLiteHelper):
    """Fake helper that raises sqlite3.Error for one targeted SQL fragment.

    Lets each fatal-class probe's propagation be exercised in isolation while
    every other query on the same connection stays real.
    """

    def __init__(self, conn: sqlite3.Connection, fragment: str) -> None:
        super().__init__(conn)
        self.fragment = fragment

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        if self.fragment in sql:
            raise sqlite3.OperationalError(f"injected probe failure: {self.fragment}")
        return self.conn.execute(sql, params)


class TestFailClosedProbeErrors:
    """Each probe error surfaces as a diagnostic + unverified flag, never a silent zero."""

    def test_fk_probe_error_marks_fk_unverified(self) -> None:
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "fk probe error")
        _insert_vec(db, chunk_id)
        db.commit()
        helper = _RaisingSQLiteHelper(
            db.conn, "FROM chunks WHERE doc_id NOT IN (SELECT doc_id FROM documents)"
        )

        report = check_rag_consistency(helper)  # type: ignore[arg-type]

        assert report.fk_unverified is True
        assert report.fk_inconsistency_count == 0  # unverified, not a healthy verdict
        assert report.embedding_unverified is False
        assert report.schema_unverified is False
        assert any(
            error.startswith("FK consistency probe failed")
            for error in report.diagnostic_errors
        )
        assert is_consistent(report) is False

    def test_embedding_probe_error_marks_embedding_unverified(self) -> None:
        db = _make_rag_db()
        helper = _RaisingSQLiteHelper(db.conn, "length(embedding) FROM chunks_vec")

        report = check_rag_consistency(helper)  # type: ignore[arg-type]

        assert report.embedding_unverified is True
        assert report.dimension_mismatch == 0  # unverified, not a healthy verdict
        assert report.fk_unverified is False
        assert report.schema_unverified is False
        assert any(
            error.startswith("Embedding dimension probe failed")
            for error in report.diagnostic_errors
        )
        assert is_consistent(report) is False

    def test_schema_probe_error_marks_schema_unverified(self) -> None:
        db = _make_rag_db()
        helper = _RaisingSQLiteHelper(db.conn, "FROM sqlite_master")

        report = check_rag_consistency(helper)  # type: ignore[arg-type]

        assert report.schema_unverified is True
        assert report.unknown_schema == 0  # unverified, not a healthy verdict
        assert report.fk_unverified is False
        assert report.embedding_unverified is False
        assert any(
            error.startswith("Schema recognition probe failed")
            for error in report.diagnostic_errors
        )
        assert is_consistent(report) is False

    def test_one_probe_failure_does_not_cancel_the_others(self) -> None:
        """AC-003: with the embedding probe raising, FK and schema still report real values."""
        db = _make_rag_db()
        # A chunk referencing a missing document: the FK probe must still count it.
        db.execute(
            "INSERT INTO chunks (doc_id, content, chunk_index) VALUES (9999, 'orphan fk', 0)"
        )
        db.commit()
        helper = _RaisingSQLiteHelper(db.conn, "length(embedding) FROM chunks_vec")

        report = check_rag_consistency(helper)  # type: ignore[arg-type]

        assert report.embedding_unverified is True
        assert report.fk_unverified is False
        assert report.fk_inconsistency_count == 1  # real FK result despite the raise
        assert report.schema_unverified is False
        assert report.unknown_schema == 0  # real schema result despite the raise
        assert report.fatal_count >= 1  # the FK violation is still classified FATAL


class TestVerificationStatusContract:
    """The unverified flags are explicit report-contract fields, orthogonal to severity."""

    @staticmethod
    def _clean_report(**flags: bool) -> RagConsistencyReport:
        return RagConsistencyReport(
            chunks=1,
            fts=1,
            vec=1,
            orphan_vec_count=0,
            fts_gap=0,
            fts_orphan_count=0,
            read_smoke_test_ok=True,
            **flags,
        )

    def test_flags_exist_and_default_false(self) -> None:
        report = self._clean_report()
        assert report.fk_unverified is False
        assert report.embedding_unverified is False
        assert report.schema_unverified is False
        assert is_consistent(report) is True

    def test_zero_counts_never_aggregate_an_unverified_dimension_as_healthy(
        self,
    ) -> None:
        """AC-002: an unverified dimension makes the report inconsistent at all-zero counts."""
        for flag in ("fk_unverified", "embedding_unverified", "schema_unverified"):
            assert is_consistent(self._clean_report(**{flag: True})) is False
