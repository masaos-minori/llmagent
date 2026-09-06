#!/usr/bin/env python3
"""scripts/db/session_consistency.py — Session domain logical consistency verification.

Mirrors rag_consistency.py's three-part shape:
  - frozen report dataclass (counts + affected-identifier tuples, None when not applicable)
  - check_session_consistency(db) collector with per-group try/except isolation
  - is_consistent(report) predicate
"""

import sqlite3

from db.helper import SQLiteHelper
from db.models import SessionConsistencyReport


def _collect_basic_counts(db: SQLiteHelper) -> tuple[int, int, int]:
    """Return (sessions_count, messages_count, memories_count)."""
    sessions = db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    messages = db.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    memories = db.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    return sessions, messages, memories


def _collect_referential_validity(
    db: SQLiteHelper,
) -> tuple[int, int, tuple[int, ...] | None, tuple[tuple[str, str], ...] | None]:
    """Return (orphaned_message_count, orphaned_memory_link_count, affected_msg_ids, affected_mem_links)."""
    orphaned_message_count = db.execute(
        "SELECT COUNT(*) FROM messages WHERE session_id NOT IN (SELECT session_id FROM sessions)"
    ).fetchone()[0]
    affected_msg_ids: tuple[int, ...] | None = None
    if orphaned_message_count > 0:
        rows = db.execute(
            "SELECT message_id FROM messages WHERE session_id NOT IN (SELECT session_id FROM sessions) LIMIT 10"
        ).fetchall()
        affected_msg_ids = tuple(r[0] for r in rows)

    orphaned_memory_link_count = db.execute(
        "SELECT COUNT(*) FROM memory_links WHERE src_id NOT IN (SELECT memory_id FROM memories) OR dst_id NOT IN (SELECT memory_id FROM memories)"
    ).fetchone()[0]
    affected_mem_links: tuple[tuple[str, str], ...] | None = None
    if orphaned_memory_link_count > 0:
        rows = db.execute(
            "SELECT src_id, dst_id FROM memory_links WHERE src_id NOT IN (SELECT memory_id FROM memories) OR dst_id NOT IN (SELECT memory_id FROM memories) LIMIT 10"
        ).fetchall()
        affected_mem_links = tuple((r[0], r[1]) for r in rows)

    return (
        orphaned_message_count,
        orphaned_memory_link_count,
        affected_msg_ids,
        affected_mem_links,
    )


def _check_read_smoke_test(db: SQLiteHelper) -> bool:
    """Verify each required table can be read without raising."""
    required_tables = [
        "sessions",
        "messages",
        "memories",
        "memories_fts",
        "memory_links",
        "session_diagnostics",
        "memories_vec",
    ]
    for table in required_tables:
        try:
            db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        except sqlite3.Error:
            return False
    return True


def _check_write_smoke_test(db: SQLiteHelper) -> bool | None:
    """Insert a throwaway row into session_diagnostics and verify row count unchanged.

    Returns None when the table does not exist or cannot be written to.
    Uses NULL for session_id to avoid FK constraint violations (no real session exists during smoke test).
    Omits id column to let SQLite auto-generate it (INTEGER PRIMARY KEY AUTOINCREMENT).
    """
    try:
        before = int(
            db.execute("SELECT COUNT(*) FROM session_diagnostics").fetchone()[0]
        )
        db.execute(
            "INSERT INTO session_diagnostics(session_id, kind, content, created_at) VALUES (NULL, 'smoke', 'smoke', strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))"
        )
        db.commit()
        after = int(
            db.execute("SELECT COUNT(*) FROM session_diagnostics").fetchone()[0]
        )
        # Clean up the throwaway row (delete the last inserted row)
        rows = db.execute(
            "SELECT id FROM session_diagnostics WHERE kind='smoke' ORDER BY id DESC LIMIT 1"
        ).fetchall()
        if rows:
            db.execute("DELETE FROM session_diagnostics WHERE id=?", (rows[0][0],))
        db.commit()
        final = int(
            db.execute("SELECT COUNT(*) FROM session_diagnostics").fetchone()[0]
        )
        return after == before + 1 and final == before
    except sqlite3.Error:
        return None


def _check_required_tables_exist(db: SQLiteHelper) -> list[str]:
    """Check that all required tables exist; return list of missing table names."""
    required_tables = [
        "sessions",
        "messages",
        "memories",
        "memories_fts",
        "memory_links",
        "session_diagnostics",
        "memories_vec",
    ]
    missing = []
    for table in required_tables:
        cursor = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        )
        if cursor.fetchone() is None:
            missing.append(table)
    return missing


def check_session_consistency(db: SQLiteHelper) -> SessionConsistencyReport:
    """Return a SessionConsistencyReport for the given database connection.

    All queries are read-only except the write smoke test which inserts and deletes
    a throwaway row within the same check group. Orphan detection uses the same
    pattern as check_rag_consistency(): per-group try/except isolation so one
    failing check group does not abort the others.
    """
    diagnostic_errors: list[str] = []

    # Initialize default values
    sessions = messages = memories = 0
    orphaned_message_count = orphaned_memory_link_count = 0
    session_diagnostics_readable = False
    read_smoke_test_ok = False
    write_smoke_test_ok: bool | None = None
    affected_orphaned_message_ids: tuple[int, ...] | None = None
    affected_orphaned_memory_link_pairs: tuple[tuple[str, str], ...] | None = None

    # Check required tables exist
    try:
        missing_tables = _check_required_tables_exist(db)
        if missing_tables:
            diagnostic_errors.extend([f"Missing table: {t}" for t in missing_tables])
    except sqlite3.Error as e:
        diagnostic_errors.append(f"Table existence check failed: {e}")

    # Collect basic counts
    try:
        sessions, messages, memories = _collect_basic_counts(db)
    except sqlite3.Error as e:
        diagnostic_errors.append(f"Basic counts collection failed: {e}")

    # Check referential validity
    try:
        (
            orphaned_message_count,
            orphaned_memory_link_count,
            affected_orphaned_message_ids,
            affected_orphaned_memory_link_pairs,
        ) = _collect_referential_validity(db)
    except sqlite3.Error as e:
        diagnostic_errors.append(f"Referential validity check failed: {e}")

    # Check session diagnostics readable
    try:
        db.execute("SELECT COUNT(*) FROM session_diagnostics").fetchone()
        session_diagnostics_readable = True
    except sqlite3.Error:
        pass

    # Read smoke test
    try:
        read_smoke_test_ok = _check_read_smoke_test(db)
    except sqlite3.Error as e:
        diagnostic_errors.append(f"Read smoke test failed: {e}")

    # Write smoke test
    try:
        write_smoke_test_ok = _check_write_smoke_test(db)
    except sqlite3.Error as e:
        diagnostic_errors.append(f"Write smoke test failed: {e}")

    report = SessionConsistencyReport(
        sessions=sessions,
        messages=messages,
        memories=memories,
        orphaned_message_count=orphaned_message_count,
        orphaned_memory_link_count=orphaned_memory_link_count,
        session_diagnostics_readable=session_diagnostics_readable,
        read_smoke_test_ok=read_smoke_test_ok,
        write_smoke_test_ok=write_smoke_test_ok,
        affected_orphaned_message_ids=affected_orphaned_message_ids,
        affected_orphaned_memory_link_pairs=affected_orphaned_memory_link_pairs,
        diagnostic_errors=tuple(diagnostic_errors) if diagnostic_errors else None,
    )
    return report


def is_consistent(report: SessionConsistencyReport) -> bool:
    """Return True only when all consistency checks pass.

    Consistent requires: no orphaned messages, no orphaned memory links,
    session diagnostics readable, read smoke test passes, write smoke test
    is not False (None means not run/applicable), and no diagnostic errors.
    """
    consistent: bool = (
        report.orphaned_message_count == 0
        and report.orphaned_memory_link_count == 0
        and report.session_diagnostics_readable
        and report.read_smoke_test_ok
        and report.write_smoke_test_ok is not False
        and not report.diagnostic_errors
    )
    return consistent
