"""tests/test_diagnostic_store.py
Unit tests for agent/diagnostic_store.py:
DiagnosticStore.save(), fetch(), fetch_all(), save_serialization_event(),
and convenience methods (save_partial_completion, save_transport_failure,
save_loop_guard_hint, fetch_by_kind).
"""

from __future__ import annotations

import json
import sqlite3
from unittest.mock import patch

import pytest
from agent.diagnostic_store import DiagnosticStore

# ── In-memory schema (session_diagnostics only; no FK to sessions needed) ─────

_SCHEMA = """
CREATE TABLE IF NOT EXISTS session_diagnostics (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER,
    kind        TEXT NOT NULL,
    content     TEXT NOT NULL,
    workflow_id TEXT,
    task_id     TEXT,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_diag_session ON session_diagnostics(session_id);
"""


class _FakeSQLiteHelper:
    """SQLiteHelper drop-in backed by in-memory SQLite.
    Supports open(write_mode, row_factory) and context-manager protocol.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def open(
        self,
        *,
        write_mode: bool = False,
        row_factory: bool = False,
        **_: object,
    ) -> _FakeSQLiteHelper:
        if row_factory:
            self._conn.row_factory = sqlite3.Row
        else:
            self._conn.row_factory = None  # type: ignore[assignment]
        return self

    def __enter__(self) -> _FakeSQLiteHelper:
        return self

    def __exit__(self, *_: object) -> None:
        pass

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def fetchall(self, sql: str, params: tuple = ()) -> list:
        return self._conn.execute(sql, params).fetchall()

    def commit(self) -> None:
        self._conn.commit()


@pytest.fixture
def fake_db() -> _FakeSQLiteHelper:
    conn = sqlite3.connect(":memory:")
    conn.executescript(_SCHEMA)
    return _FakeSQLiteHelper(conn)


# ── save + fetch ──────────────────────────────────────────────────────────────


class TestDiagnosticStoreSave:
    def test_save_inserts_one_row(self, fake_db: _FakeSQLiteHelper) -> None:
        store = DiagnosticStore()
        with patch(
            "agent.diagnostic_store.SQLiteHelper", side_effect=lambda _: fake_db
        ):
            store.save(1, kind="rag_query", content='{"q": "hello"}')
        rows = fake_db.fetchall(
            "SELECT session_id, kind, content FROM session_diagnostics"
        )
        assert len(rows) == 1
        assert rows[0][1] == "rag_query"
        assert rows[0][2] == '{"q": "hello"}'

    def test_save_with_none_session_id(self, fake_db: _FakeSQLiteHelper) -> None:
        store = DiagnosticStore()
        with patch(
            "agent.diagnostic_store.SQLiteHelper", side_effect=lambda _: fake_db
        ):
            store.save(None, kind="event", content="data")
        rows = fake_db.fetchall("SELECT session_id FROM session_diagnostics")
        assert len(rows) == 1
        assert rows[0][0] is None

    def test_multiple_saves_accumulate(self, fake_db: _FakeSQLiteHelper) -> None:
        store = DiagnosticStore()
        with patch(
            "agent.diagnostic_store.SQLiteHelper", side_effect=lambda _: fake_db
        ):
            store.save(1, kind="k1", content="c1")
            store.save(1, kind="k2", content="c2")
        rows = fake_db.fetchall("SELECT kind FROM session_diagnostics")
        assert len(rows) == 2


class TestDiagnosticStoreFetch:
    def test_fetch_returns_rows_for_session(self, fake_db: _FakeSQLiteHelper) -> None:
        store = DiagnosticStore()
        with patch(
            "agent.diagnostic_store.SQLiteHelper", side_effect=lambda _: fake_db
        ):
            store.save(42, kind="rag_query", content='{"q": "test"}')
            store.save(42, kind="session_summary", content='{"turns": 3}')
            entries = store.fetch(42)
        assert len(entries) == 2
        kinds = {e["kind"] for e in entries}
        assert kinds == {"rag_query", "session_summary"}

    def test_fetch_returns_empty_for_unknown_session(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        store = DiagnosticStore()
        with patch(
            "agent.diagnostic_store.SQLiteHelper", side_effect=lambda _: fake_db
        ):
            entries = store.fetch(9999)
        assert entries == []

    def test_fetch_does_not_return_other_sessions(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        store = DiagnosticStore()
        with patch(
            "agent.diagnostic_store.SQLiteHelper", side_effect=lambda _: fake_db
        ):
            store.save(1, kind="k1", content="for session 1")
            store.save(2, kind="k2", content="for session 2")
            entries = store.fetch(1)
        assert len(entries) == 1
        assert entries[0]["kind"] == "k1"

    def test_fetch_entries_are_dicts_with_expected_keys(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        store = DiagnosticStore()
        with patch(
            "agent.diagnostic_store.SQLiteHelper", side_effect=lambda _: fake_db
        ):
            store.save(1, kind="rag_query", content="{}")
            entries = store.fetch(1)
        entry = entries[0]
        assert "kind" in entry
        assert "content" in entry
        assert "session_id" in entry


# ── fetch_all ─────────────────────────────────────────────────────────────────


class TestDiagnosticStoreFetchAll:
    def test_fetch_all_returns_rows_across_sessions(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        store = DiagnosticStore()
        with patch(
            "agent.diagnostic_store.SQLiteHelper", side_effect=lambda _: fake_db
        ):
            store.save(1, kind="k1", content="c1")
            store.save(2, kind="k2", content="c2")
            entries = store.fetch_all(limit=10)
        assert len(entries) == 2
        kinds = {e["kind"] for e in entries}
        assert "k1" in kinds and "k2" in kinds

    def test_fetch_all_respects_limit(self, fake_db: _FakeSQLiteHelper) -> None:
        store = DiagnosticStore()
        with patch(
            "agent.diagnostic_store.SQLiteHelper", side_effect=lambda _: fake_db
        ):
            for i in range(5):
                store.save(i, kind="k", content=f"c{i}")
            entries = store.fetch_all(limit=3)
        assert len(entries) == 3


# ── save_serialization_event ──────────────────────────────────────────────────


class TestSaveSerializationEvent:
    def test_stores_json_with_expected_fields(self, fake_db: _FakeSQLiteHelper) -> None:
        store = DiagnosticStore()
        with patch(
            "agent.diagnostic_store.SQLiteHelper", side_effect=lambda _: fake_db
        ):
            store.save_serialization_event(
                session_id=1,
                round_id="r1",
                trigger_tool="write_file",
                affected_count=3,
                mode="serial",
                elapsed_ms=12.5,
                reason="cycle detected",
            )
            entries = store.fetch(1)
        assert len(entries) == 1
        assert entries[0]["kind"] == "serialization_event"
        data = json.loads(entries[0]["content"])
        assert data["trigger_tool"] == "write_file"
        assert data["affected_count"] == 3
        assert data["mode"] == "serial"
        assert data["elapsed_ms"] == 12.5
        assert data["reason"] == "cycle detected"

    def test_elapsed_ms_is_rounded(self, fake_db: _FakeSQLiteHelper) -> None:
        store = DiagnosticStore()
        with patch(
            "agent.diagnostic_store.SQLiteHelper", side_effect=lambda _: fake_db
        ):
            store.save_serialization_event(
                session_id=1,
                round_id="r2",
                trigger_tool="edit_file",
                affected_count=1,
                mode="async",
                elapsed_ms=12.567,
                reason="none",
            )
            entries = store.fetch(1)
        data = json.loads(entries[0]["content"])
        assert data["elapsed_ms"] == 12.6


class TestConvenienceMethods:
    def test_save_partial_completion(self, fake_db: _FakeSQLiteHelper) -> None:
        store = DiagnosticStore()
        with patch(
            "agent.diagnostic_store.SQLiteHelper", side_effect=lambda _: fake_db
        ):
            store.save_partial_completion(
                session_id=1,
                turn=3,
                reason="timeout",
                content_length=1024,
            )
            rows = store.fetch_by_kind(1, "partial_completion")
        assert len(rows) == 1
        payload = json.loads(rows[0]["content"])
        assert payload["turn"] == 3
        assert payload["reason"] == "timeout"
        assert payload["content_length"] == 1024

    def test_save_transport_failure(self, fake_db: _FakeSQLiteHelper) -> None:
        store = DiagnosticStore()
        with patch(
            "agent.diagnostic_store.SQLiteHelper", side_effect=lambda _: fake_db
        ):
            store.save_transport_failure(
                session_id=1,
                tool_name="read_text_file",
                server_key="file_read",
                error_msg="Connection refused",
            )
            rows = store.fetch_by_kind(1, "transport_failure")
        assert len(rows) == 1
        payload = json.loads(rows[0]["content"])
        assert payload["tool_name"] == "read_text_file"
        assert payload["server_key"] == "file_read"

    def test_save_loop_guard_hint(self, fake_db: _FakeSQLiteHelper) -> None:
        store = DiagnosticStore()
        with patch(
            "agent.diagnostic_store.SQLiteHelper", side_effect=lambda _: fake_db
        ):
            store.save_loop_guard_hint(
                session_id=1,
                reason="cycle_detected",
                turn_count=7,
            )
            rows = store.fetch_by_kind(1, "loop_guard_hint")
        assert len(rows) == 1
        payload = json.loads(rows[0]["content"])
        assert payload["reason"] == "cycle_detected"
        assert payload["turn_count"] == 7

    def test_fetch_by_kind_returns_empty_for_unknown_kind(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        store = DiagnosticStore()
        with patch(
            "agent.diagnostic_store.SQLiteHelper", side_effect=lambda _: fake_db
        ):
            rows = store.fetch_by_kind(1, "nonexistent_kind")
        assert rows == []

    def test_fetch_by_kind_filters_by_kind(self, fake_db: _FakeSQLiteHelper) -> None:
        store = DiagnosticStore()
        with patch(
            "agent.diagnostic_store.SQLiteHelper", side_effect=lambda _: fake_db
        ):
            store.save_partial_completion(
                session_id=1, turn=1, reason="t", content_length=10
            )
            store.save_transport_failure(
                session_id=1, tool_name="t", server_key="s", error_msg="e"
            )
            partial_rows = store.fetch_by_kind(1, "partial_completion")
            transport_rows = store.fetch_by_kind(1, "transport_failure")
        assert len(partial_rows) == 1
        assert len(transport_rows) == 1
