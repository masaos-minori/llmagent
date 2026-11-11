#!/usr/bin/env python3
"""tests/db/test_session_consistency.py — Unit tests for check_session_consistency()/is_consistent().

Mirrors test_rag_consistency.py's structure: a _FakeSQLiteHelper wrapper around a real
in-memory sqlite3.Connection, a fixture schema derived from the canonical DDL SSOT
(vec0 replaced by plain stand-ins, UNK-01 name-only), and one test class per concern
group. The schema-shape gate is the shared fingerprint: drift raises RuntimeError.
"""

from __future__ import annotations

import re
import sqlite3

import pytest
from db.schema_sql import build_session_schema_sql
from db.session_consistency import check_session_consistency, is_consistent

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


# ── Schema (derived from the canonical DDL SSOT; vec0 replaced by a plain
# stand-in so the fixture builds without the sqlite-vec extension) ─────────────

#: Concrete embedding dimension for fixtures. Must match get_embedding_dims()
#: (Qwen3, 1024); the fingerprint compares virtual tables by name only (UNK-01),
#: so the dimension never reaches the compared shapes.
EMBED_DIMS = 1024

_VEC0_PLAIN_SUBSTITUTES: dict[str, str] = {
    "memories_vec": (
        "CREATE TABLE memories_vec (memory_id TEXT PRIMARY KEY, embedding BLOB)"
    ),
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


_SESSION_SCHEMA = _fallback_from_canonical(build_session_schema_sql(EMBED_DIMS))


def _make_session_db() -> _FakeSQLiteHelper:
    """Create an in-memory SQLite database with the session schema."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(_SESSION_SCHEMA)
    conn.commit()
    return _FakeSQLiteHelper(conn)


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestSessionConsistencyHealthy:
    """Tests for healthy (consistent) session database state."""

    def test_is_consistent_returns_true_on_healthy_db(self):
        db = _make_session_db()
        report = check_session_consistency(db)
        assert is_consistent(report) is True

    def test_all_checks_pass_on_healthy_db(self):
        db = _make_session_db()
        report = check_session_consistency(db)
        assert report.sessions >= 0
        assert report.messages >= 0
        assert report.memories >= 0
        assert report.orphaned_message_count == 0
        assert report.orphaned_memory_link_count == 0
        assert report.session_diagnostics_readable is True
        assert report.read_smoke_test_ok is True
        assert report.diagnostic_errors is None

    def test_no_content_leaked_in_healthy_report(self):
        """Assert no report field contains messages.content or memories.content strings."""
        db = _make_session_db()
        report = check_session_consistency(db)
        all_text = ""
        if report.diagnostic_errors:
            all_text += " ".join(report.diagnostic_errors)
        if report.affected_orphaned_message_ids:
            all_text += " ".join(str(i) for i in report.affected_orphaned_message_ids)
        if report.affected_orphaned_memory_link_pairs:
            all_text += " ".join(
                f"{a}{b}" for a, b in report.affected_orphaned_memory_link_pairs
            )
        assert "hello" not in all_text.lower()
        assert "world" not in all_text.lower()
        assert "test" not in all_text.lower()
        assert "message" not in all_text.lower()
        assert "memory" not in all_text.lower()

    def test_check_consistency_leaves_database_unchanged(self):
        """check_session_consistency() runs no INSERT/UPDATE/DELETE/COMMIT and leaves no residue."""
        db = _make_session_db()
        before_rows = db.execute(
            "SELECT * FROM session_diagnostics ORDER BY id"
        ).fetchall()
        before_count = db.execute(
            "SELECT COUNT(*) FROM session_diagnostics"
        ).fetchone()[0]

        statements: list[str] = []
        db.conn.set_trace_callback(statements.append)
        try:
            report = check_session_consistency(db)
        finally:
            db.conn.set_trace_callback(None)

        after_rows = db.execute(
            "SELECT * FROM session_diagnostics ORDER BY id"
        ).fetchall()
        after_count = db.execute("SELECT COUNT(*) FROM session_diagnostics").fetchone()[
            0
        ]
        mutating = [
            s
            for s in statements
            if s.split()[0].upper()
            in {"INSERT", "UPDATE", "DELETE", "REPLACE", "BEGIN", "COMMIT"}
        ]

        assert report.sessions >= 0
        assert before_count == after_count
        assert before_rows == after_rows
        assert mutating == []

    def test_missing_table_raises_fingerprint_refusal(self):
        """Dropping a required table raises the fingerprint refusal (REQ-003)."""
        db = _make_session_db()
        db.execute("DROP TABLE IF EXISTS sessions")
        db.commit()
        with pytest.raises(RuntimeError, match="missing table 'sessions'"):
            check_session_consistency(db)

    def test_orphaned_messages_detected(self):
        """Inserting a messages row without a matching session should be detected."""
        db = _make_session_db()
        db.execute(
            "INSERT INTO messages(message_id, session_id, role, content) VALUES (9999, 9999, 'user', 'orphan')"
        )
        db.commit()
        report = check_session_consistency(db)
        assert report.orphaned_message_count == 1
        assert report.affected_orphaned_message_ids is not None
        assert 9999 in report.affected_orphaned_message_ids
        assert is_consistent(report) is False

    def test_orphaned_memory_links_detected(self):
        """Inserting a memory_links row without matching memories should be detected."""
        db = _make_session_db()
        db.execute(
            "INSERT OR IGNORE INTO memories(memory_id, memory_type, content, summary) VALUES ('valid_mem', 'semantic', 'valid_content', 'valid_summary')"
        )
        db.execute(
            "INSERT INTO memory_links(src_id, dst_id) VALUES ('nonexistent_src', 'nonexistent_dst')"
        )
        db.commit()
        report = check_session_consistency(db)
        assert report.orphaned_memory_link_count == 1
        assert report.affected_orphaned_memory_link_pairs is not None
        assert (
            "nonexistent_src",
            "nonexistent_dst",
        ) in report.affected_orphaned_memory_link_pairs
        assert is_consistent(report) is False

    def test_extra_table_raises_fingerprint_refusal(self):
        """A table not defined by the canonical schema is a fingerprint finding."""
        db = _make_session_db()
        db.execute("CREATE TABLE schema_migrations (version INTEGER)")
        db.commit()
        with pytest.raises(RuntimeError, match="unexpected table 'schema_migrations'"):
            check_session_consistency(db)
