"""tests/test_diagnostic_store.py
Unit tests for agent/diagnostic_store.py:
DiagnosticStore.save(), fetch(), save_serialization_event(),
and convenience methods (save_partial_completion, save_transport_failure).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from agent.diagnostic_store import DiagnosticStore
from cryptography.fernet import Fernet, InvalidToken

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


class _FakeConfigLoader:
    """ConfigLoader drop-in returning a fixed, pre-built config dict."""

    def __init__(self, cfg: dict) -> None:
        self._cfg = cfg

    def load(self, *names: str) -> dict:
        return self._cfg


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
            rows = store.fetch(1)
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
            rows = store.fetch(1)
        assert len(rows) == 1
        payload = json.loads(rows[0]["content"])
        assert payload["tool_name"] == "read_text_file"
        assert payload["server_key"] == "file_read"


# ── _filter_sensitive_fields ────────────────────────────────────────────────


class TestFilterSensitiveFields:
    def test_redacts_artifacts_and_rag_stage_outcomes(self) -> None:
        store = DiagnosticStore()
        payload = json.dumps(
            {
                "artifacts": ["uri1", "uri2", "uri3"],
                "rag_stage_outcomes": ["stage1"],
                "other": "kept",
            }
        )
        result = json.loads(store._filter_sensitive_fields(payload))
        assert result["artifacts"] == {"_redacted": True, "count": 3}
        assert result["rag_stage_outcomes"] == {"_redacted": True, "count": 1}
        assert result["other"] == "kept"

    def test_preserves_count_for_empty_list(self) -> None:
        store = DiagnosticStore()
        payload = json.dumps({"artifacts": []})
        result = json.loads(store._filter_sensitive_fields(payload))
        assert result["artifacts"] == {"_redacted": True, "count": 0}

    def test_passthrough_when_no_sensitive_fields(self) -> None:
        store = DiagnosticStore()
        payload = '{"turn": 1}'
        assert store._filter_sensitive_fields(payload) == payload

    def test_passthrough_for_non_json_content(self) -> None:
        store = DiagnosticStore()
        assert store._filter_sensitive_fields("not json") == "not json"

    def test_passthrough_for_json_non_dict(self) -> None:
        store = DiagnosticStore()
        assert store._filter_sensitive_fields("[1, 2, 3]") == "[1, 2, 3]"

    def test_save_redacts_sensitive_fields_and_preserves_count(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        store = DiagnosticStore()
        payload = json.dumps({"artifacts": ["a", "b"], "rag_stage_outcomes": []})
        with patch(
            "agent.diagnostic_store.SQLiteHelper", side_effect=lambda _: fake_db
        ):
            store.save(1, kind="rag_query", content=payload)
            entries = store.fetch(1)
        stored = json.loads(entries[0]["content"])
        assert stored["artifacts"] == {"_redacted": True, "count": 2}
        assert stored["rag_stage_outcomes"] == {"_redacted": True, "count": 0}


# ── _encrypt_content / save(encrypt=True) ───────────────────────────────────


class TestEncryption:
    def test_encrypt_content_is_noop_when_key_empty(self) -> None:
        store = DiagnosticStore()
        assert store._encrypt_content("plaintext", "") == "plaintext"

    def test_encrypt_content_roundtrip(self) -> None:
        store = DiagnosticStore()
        key = Fernet.generate_key().decode("utf-8")
        ciphertext = store._encrypt_content("plaintext", key)
        assert ciphertext != "plaintext"
        assert (
            Fernet(key.encode("utf-8")).decrypt(ciphertext.encode("utf-8"))
            == b"plaintext"
        )

    def test_wrong_key_fails_to_decrypt(self) -> None:
        store = DiagnosticStore()
        key = Fernet.generate_key().decode("utf-8")
        wrong_key = Fernet.generate_key().decode("utf-8")
        ciphertext = store._encrypt_content("plaintext", key)
        with pytest.raises(InvalidToken):
            Fernet(wrong_key.encode("utf-8")).decrypt(ciphertext.encode("utf-8"))

    def test_save_encrypt_true_with_configured_key(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        key = Fernet.generate_key().decode("utf-8")
        fake_cfg_loader = _FakeConfigLoader(
            {"diagnostics": {"encryption_key": key, "retention_days": 30}}
        )
        store = DiagnosticStore()
        with (
            patch("agent.diagnostic_store.SQLiteHelper", side_effect=lambda _: fake_db),
            patch("agent.diagnostic_store.ConfigLoader", return_value=fake_cfg_loader),
        ):
            store.save(1, kind="k", content='{"turn": 1}', encrypt=True)
        rows = fake_db.fetchall("SELECT content FROM session_diagnostics")
        stored_content = rows[0][0]
        assert stored_content != '{"turn": 1}'
        decrypted = Fernet(key.encode("utf-8")).decrypt(stored_content.encode("utf-8"))
        assert json.loads(decrypted) == {"turn": 1}

    def test_save_encrypt_true_without_configured_key_is_noop(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        fake_cfg_loader = _FakeConfigLoader({"diagnostics": {"retention_days": 30}})
        store = DiagnosticStore()
        with (
            patch("agent.diagnostic_store.SQLiteHelper", side_effect=lambda _: fake_db),
            patch("agent.diagnostic_store.ConfigLoader", return_value=fake_cfg_loader),
        ):
            store.save(1, kind="k", content='{"turn": 1}', encrypt=True)
        rows = fake_db.fetchall("SELECT content FROM session_diagnostics")
        assert rows[0][0] == '{"turn": 1}'

    def test_save_encrypt_false_leaves_content_plaintext(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        key = Fernet.generate_key().decode("utf-8")
        fake_cfg_loader = _FakeConfigLoader(
            {"diagnostics": {"encryption_key": key, "retention_days": 30}}
        )
        store = DiagnosticStore()
        with (
            patch("agent.diagnostic_store.SQLiteHelper", side_effect=lambda _: fake_db),
            patch("agent.diagnostic_store.ConfigLoader", return_value=fake_cfg_loader),
        ):
            store.save(1, kind="k", content='{"turn": 1}')
        rows = fake_db.fetchall("SELECT content FROM session_diagnostics")
        assert rows[0][0] == '{"turn": 1}'


# ── _purge_old_diagnostics ────────────────────────────────────────────────────


class TestPurgeOldDiagnostics:
    def test_purge_deletes_old_rows_and_keeps_recent(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        old_created_at = (datetime.now(UTC) - timedelta(days=40)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        fake_db.execute(
            "INSERT INTO session_diagnostics (session_id, kind, content, created_at)"
            " VALUES (?, ?, ?, ?)",
            (1, "old_kind", "old content", old_created_at),
        )
        fake_db.commit()
        fake_cfg_loader = _FakeConfigLoader({"diagnostics": {"retention_days": 30}})
        store = DiagnosticStore()
        with (
            patch("agent.diagnostic_store.SQLiteHelper", side_effect=lambda _: fake_db),
            patch("agent.diagnostic_store.ConfigLoader", return_value=fake_cfg_loader),
        ):
            store.save(1, kind="new_kind", content="new content")
        rows = fake_db.fetchall("SELECT kind FROM session_diagnostics")
        kinds = {r[0] for r in rows}
        assert "old_kind" not in kinds
        assert "new_kind" in kinds

    def test_purge_disabled_when_retention_days_non_positive(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        ancient_created_at = (datetime.now(UTC) - timedelta(days=400)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        fake_db.execute(
            "INSERT INTO session_diagnostics (session_id, kind, content, created_at)"
            " VALUES (?, ?, ?, ?)",
            (1, "ancient_kind", "ancient content", ancient_created_at),
        )
        fake_db.commit()
        fake_cfg_loader = _FakeConfigLoader({"diagnostics": {"retention_days": 0}})
        store = DiagnosticStore()
        with (
            patch("agent.diagnostic_store.SQLiteHelper", side_effect=lambda _: fake_db),
            patch("agent.diagnostic_store.ConfigLoader", return_value=fake_cfg_loader),
        ):
            store.save(1, kind="new_kind", content="new content")
        rows = fake_db.fetchall("SELECT kind FROM session_diagnostics")
        kinds = {r[0] for r in rows}
        assert "ancient_kind" in kinds

    def test_purge_non_dict_diagnostics_value_uses_default_retention(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        # Guards against a malformed config where "diagnostics" isn't a table
        # (e.g. `diagnostics = "oops"` instead of `[diagnostics]`).
        old_created_at = (datetime.now(UTC) - timedelta(days=31)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        fake_db.execute(
            "INSERT INTO session_diagnostics (session_id, kind, content, created_at)"
            " VALUES (?, ?, ?, ?)",
            (1, "old_kind", "old content", old_created_at),
        )
        fake_db.commit()
        fake_cfg_loader = _FakeConfigLoader({"diagnostics": "not-a-table"})
        store = DiagnosticStore()
        with (
            patch("agent.diagnostic_store.SQLiteHelper", side_effect=lambda _: fake_db),
            patch("agent.diagnostic_store.ConfigLoader", return_value=fake_cfg_loader),
        ):
            store.save(1, kind="new_kind", content="new content")
        rows = fake_db.fetchall("SELECT kind FROM session_diagnostics")
        kinds = {r[0] for r in rows}
        assert "old_kind" not in kinds
        assert "new_kind" in kinds

    def test_purge_missing_diagnostics_config_uses_default_retention(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        old_created_at = (datetime.now(UTC) - timedelta(days=31)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        fake_db.execute(
            "INSERT INTO session_diagnostics (session_id, kind, content, created_at)"
            " VALUES (?, ?, ?, ?)",
            (1, "old_kind", "old content", old_created_at),
        )
        fake_db.commit()
        fake_cfg_loader = _FakeConfigLoader({})
        store = DiagnosticStore()
        with (
            patch("agent.diagnostic_store.SQLiteHelper", side_effect=lambda _: fake_db),
            patch("agent.diagnostic_store.ConfigLoader", return_value=fake_cfg_loader),
        ):
            store.save(1, kind="new_kind", content="new content")
        rows = fake_db.fetchall("SELECT kind FROM session_diagnostics")
        kinds = {r[0] for r in rows}
        assert "old_kind" not in kinds
        assert "new_kind" in kinds
