"""tests/test_diagnostic_store.py
Unit tests for agent/diagnostic_store.py:
DiagnosticStore.save(), fetch(), save_serialization_event(),
and convenience methods (save_partial_completion, save_transport_failure).

The store consumes an injected DiagnosticsConfig snapshot (constructed
positionally/keyword), so every test builds a DiagnosticsConfig rather than
mocking ConfigLoader / _load_diagnostics_config.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from agent.config_dataclasses import DiagnosticsConfig
from agent.diagnostic_store import DiagnosticStore
from cryptography.fernet import Fernet, InvalidToken

from tests.agent._config_test_defaults import MIN_DB_CONFIG

# ── In-memory schema (session_diagnostics only; no FK to sessions needed) ─────
_SCHEMA = """
CREATE TABLE IF NOT EXISTS session_diagnostics (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER,
    kind        TEXT NOT NULL,
    content     TEXT NOT NULL,
    workflow_id TEXT,
    task_id     TEXT,
    storage_format TEXT NOT NULL DEFAULT 'plaintext',
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


def _cfg(**overrides: object) -> DiagnosticsConfig:
    """Build a DiagnosticsConfig with sensible defaults overridable per test."""
    return DiagnosticsConfig(**overrides)  # type: ignore[arg-type]


def _store(**cfg_overrides: object) -> DiagnosticStore:
    """Construct a store wired to an injected DiagnosticsConfig."""
    return DiagnosticStore(
        diagnostics_cfg=_cfg(**cfg_overrides), db_config=MIN_DB_CONFIG
    )


# ── save + fetch ──────────────────────────────────────────────────────────────


class TestDiagnosticStoreSave:
    def test_save_inserts_one_row(self, fake_db: _FakeSQLiteHelper) -> None:
        store = _store()
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
        ):
            store.save(1, kind="k", content="v")
        rows = fake_db.fetchall("SELECT * FROM session_diagnostics")
        assert len(rows) == 1

    def test_save_with_none_session_id(self, fake_db: _FakeSQLiteHelper) -> None:
        store = _store()
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
        ):
            store.save(None, kind="k", content="v")
        rows = fake_db.fetchall("SELECT session_id FROM session_diagnostics")
        assert rows[0][0] is None

    def test_multiple_saves_accumulate(self, fake_db: _FakeSQLiteHelper) -> None:
        store = _store()
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
        ):
            store.save(1, kind="k", content="v")
            store.save(1, kind="k", content="w")
        rows = fake_db.fetchall("SELECT * FROM session_diagnostics")
        assert len(rows) == 2

    def test_fetch_returns_rows_for_session(self, fake_db: _FakeSQLiteHelper) -> None:
        store = _store()
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
        ):
            store.save(1, kind="k", content="v")
            store.save(2, kind="k", content="w")
            entries = store.fetch(1)
        assert len(entries) == 1

    def test_fetch_ignores_other_sessions(self, fake_db: _FakeSQLiteHelper) -> None:
        store = _store()
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
        ):
            store.save(1, kind="k", content="v")
            store.save(2, kind="k", content="w")
            entries = store.fetch(2)
        assert entries[0]["content"] == "w"

    def test_convenience_methods_persist(self, fake_db: _FakeSQLiteHelper) -> None:
        store = _store()
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
        ):
            store.save_serialization_event(1, "r1", "t1", 3, "mode", 12.0, "reason")
        rows = fake_db.fetchall("SELECT kind FROM session_diagnostics")
        assert {r[0] for r in rows} == {"serialization_event"}


class TestDiagnosticStoreSaveFields:
    def test_stores_json_with_expected_fields(self, fake_db: _FakeSQLiteHelper) -> None:
        store = _store()
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
        ):
            store.save(1, kind="k", content='{"turn": 1}')
        (row,) = fake_db.fetchall("SELECT content FROM session_diagnostics")
        assert json.loads(row[0]) == {"turn": 1}

    def test_elapsed_ms_is_rounded(self, fake_db: _FakeSQLiteHelper) -> None:
        store = _store()
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
        ):
            store.save_serialization_event(1, "r1", "t1", 3, "mode", 12.345, "reason")
        (row,) = fake_db.fetchall("SELECT content FROM session_diagnostics")
        assert json.loads(row[0])["elapsed_ms"] == 12.3

    def test_save_partial_completion(self, fake_db: _FakeSQLiteHelper) -> None:
        store = _store()
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
        ):
            store.save_partial_completion(1, turn=2, reason="stop", content_length=10)
        (row,) = fake_db.fetchall("SELECT kind, content FROM session_diagnostics")
        assert row[0] == "partial_completion"
        assert json.loads(row[1])["turn"] == 2

    def test_save_transport_failure(self, fake_db: _FakeSQLiteHelper) -> None:
        store = _store()
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
        ):
            store.save_transport_failure(1, "tool", "key", "boom")
        (row,) = fake_db.fetchall("SELECT kind FROM session_diagnostics")
        assert row[0] == "transport_failure"


class TestFilterSensitiveFields:
    def test_redacts_artifacts_and_rag_stage_outcomes(self) -> None:
        store = _store()
        payload = json.dumps(
            {
                "artifacts": ["uri1", "uri2", "uri3"],
                "rag_stage_outcomes": ["stage1"],
                "other": "kept",
            }
        )
        result = json.loads(store._filter_sensitive_fields(payload, _cfg()))
        assert result["artifacts"] == {"_redacted": True, "count": 3}
        assert result["rag_stage_outcomes"] == {"_redacted": True, "count": 1}
        assert result["other"] == "kept"

    def test_preserves_count_for_empty_list(self) -> None:
        store = _store()
        payload = json.dumps({"artifacts": []})
        result = json.loads(store._filter_sensitive_fields(payload, _cfg()))
        assert result["artifacts"] == {"_redacted": True, "count": 0}

    def test_passthrough_when_no_sensitive_fields(self) -> None:
        store = _store()
        payload = '{"turn": 1}'
        assert store._filter_sensitive_fields(payload, _cfg()) == payload

    def test_passthrough_for_non_json_content(self) -> None:
        store = _store()
        assert store._filter_sensitive_fields("not json", _cfg()) == "not json"

    def test_passthrough_for_json_non_dict(self) -> None:
        store = _store()
        assert store._filter_sensitive_fields("[1, 2, 3]", _cfg()) == "[1, 2, 3]"

    def test_save_redacts_sensitive_fields_and_preserves_count(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        store = _store()
        payload = json.dumps({"artifacts": ["a", "b"], "rag_stage_outcomes": []})
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
        ):
            store.save(1, kind="rag_query", content=payload)
            entries = store.fetch(1)
        stored = json.loads(entries[0]["content"])
        assert stored["artifacts"] == {"_redacted": True, "count": 2}
        assert stored["rag_stage_outcomes"] == {"_redacted": True, "count": 0}


# ── encryption by policy ───────────────────────────────────────────────────────


class TestEncryption:
    def test_encrypt_content_is_noop_when_key_empty(self) -> None:
        store = _store()
        assert store._encrypt_content("plaintext", "") == "plaintext"

    def test_encrypt_content_roundtrip(self) -> None:
        key = Fernet.generate_key().decode("utf-8")
        ciphertext = _store()._encrypt_content("plaintext", key)
        assert ciphertext != "plaintext"
        assert (
            Fernet(key.encode("utf-8")).decrypt(ciphertext.encode("utf-8"))
            == b"plaintext"
        )

    def test_wrong_key_fails_to_decrypt(self) -> None:
        key = Fernet.generate_key().decode("utf-8")
        wrong_key = Fernet.generate_key().decode("utf-8")
        ciphertext = _store()._encrypt_content("plaintext", key)
        with pytest.raises(InvalidToken):
            Fernet(wrong_key.encode("utf-8")).decrypt(ciphertext.encode("utf-8"))

    def test_save_encrypts_by_policy_when_key_configured(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        key = Fernet.generate_key().decode("utf-8")
        store = _store(encryption_key=key)
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
        ):
            store.save(1, kind="k", content='{"turn": 1}')
        rows = fake_db.fetchall(
            "SELECT content, storage_format FROM session_diagnostics"
        )
        stored_content = rows[0][0]
        assert stored_content != '{"turn": 1}'
        assert rows[0][1] == "encrypted"
        decrypted = Fernet(key.encode("utf-8")).decrypt(stored_content.encode("utf-8"))
        assert json.loads(decrypted) == {"turn": 1}

    def test_fetch_decrypts_content_saved_by_policy(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        """fetch() should decrypt ciphertext saved with a configured key."""
        key = Fernet.generate_key().decode("utf-8")
        plaintext = '{"turn": 1}'
        store = _store(encryption_key=key)
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
        ):
            store.save(1, kind="k", content=plaintext)
            entries = store.fetch(1)
        assert len(entries) == 1
        assert entries[0]["kind"] == "k"
        # This assertion exercises the decrypt branch inside fetch() itself
        assert entries[0]["content"] == plaintext

    def test_save_without_key_leaves_content_plaintext(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        store = _store()  # no encryption_key configured
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
        ):
            store.save(1, kind="k", content='{"turn": 1}')
        rows = fake_db.fetchall(
            "SELECT content, storage_format FROM session_diagnostics"
        )
        assert rows[0][0] == '{"turn": 1}'
        assert rows[0][1] == "plaintext"


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
        store = _store(retention_days=30)
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
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
        store = _store(retention_days=0)
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
        ):
            store.save(1, kind="new_kind", content="new content")
        rows = fake_db.fetchall("SELECT kind FROM session_diagnostics")
        kinds = {r[0] for r in rows}
        assert "ancient_kind" in kinds

    def test_purge_uses_injected_retention_default(
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
        store = _store()  # default retention_days=30
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
        ):
            store.save(1, kind="new_kind", content="new content")
        rows = fake_db.fetchall("SELECT kind FROM session_diagnostics")
        kinds = {r[0] for r in rows}
        assert "old_kind" not in kinds
        assert "new_kind" in kinds


def test_save_rejects_sensitive_data_without_encryption(
    fake_db: _FakeSQLiteHelper,
) -> None:
    """Verify refusal when sensitive data is present without a key."""
    store = _store()
    sensitive_content = '{"api_key": "sk-abcdefghijklmnop12345"}'
    with patch(
        "agent.diagnostic_store.SQLiteHelper",
        side_effect=lambda _, db_config=None: fake_db,
    ):
        with pytest.raises(RuntimeError, match="Sensitive information detected"):
            store.save(1, kind="test", content=sensitive_content)


def test_save_successfully_encrypts_when_key_provided(
    fake_db: _FakeSQLiteHelper,
) -> None:
    """Verify successful encryption when a key is provided."""
    key = Fernet.generate_key().decode("utf-8")
    store = _store(encryption_key=key)
    sensitive_content = '{"api_key": "sk-abcdefghijklmnop12345"}'
    with patch(
        "agent.diagnostic_store.SQLiteHelper",
        side_effect=lambda _, db_config=None: fake_db,
    ):
        store.save(1, kind="test", content=sensitive_content)

    rows = fake_db.fetchall("SELECT content FROM session_diagnostics")
    assert len(rows) == 1
    decrypted = Fernet(key.encode("utf-8")).decrypt(rows[0][0].encode("utf-8"))
    assert json.loads(decrypted) == {"api_key": "sk-abcdefghijklmnop12345"}


def test_save_saves_non_sensitive_data_normally(fake_db: _FakeSQLiteHelper) -> None:
    """Verify non-sensitive data is saved normally without encryption."""
    store = _store()
    safe_content = '{"message": "hello world"}'
    with patch(
        "agent.diagnostic_store.SQLiteHelper",
        side_effect=lambda _, db_config=None: fake_db,
    ):
        store.save(1, kind="test", content=safe_content)

    rows = fake_db.fetchall("SELECT content FROM session_diagnostics")
    assert len(rows) == 1
    assert rows[0][0] == safe_content


# ── sensitive_fields from config ────────────────────────────────────────────────


class TestSensitiveFieldsFromConfig:
    def test_custom_sensitive_fields_applied_from_config(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        """Custom sensitive_fields from config should be merged with defaults."""
        store = _store(sensitive_fields=frozenset({"custom_field"}))
        payload = json.dumps(
            {
                "artifacts": ["uri1"],  # default sensitive field — redacted
                "custom_field": ["data1"],  # custom sensitive field — redacted
                "other": "kept",  # non-sensitive — preserved
            }
        )
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
        ):
            store.save(1, kind="k", content=payload)
            entries = store.fetch(1)
        stored = json.loads(entries[0]["content"])
        assert stored["artifacts"] == {"_redacted": True, "count": 1}
        assert stored["custom_field"] == {"_redacted": True, "count": 1}
        assert stored["other"] == "kept"

    def test_empty_sensitive_fields_in_config_means_no_extra_redaction(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        """Empty sensitive_fields in config should still apply defaults."""
        store = _store()
        payload = json.dumps(
            {
                "artifacts": ["uri1"],
                "rag_stage_outcomes": [],
                "other": "kept",
            }
        )
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
        ):
            store.save(1, kind="k", content=payload)
            entries = store.fetch(1)
        stored = json.loads(entries[0]["content"])
        assert stored["artifacts"] == {"_redacted": True, "count": 1}
        assert stored["rag_stage_outcomes"] == {"_redacted": True, "count": 0}
        assert stored["other"] == "kept"

    def test_missing_sensitive_fields_in_config_uses_default(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        """Missing sensitive_fields in config should use dataclass default."""
        store = _store()
        payload = json.dumps(
            {
                "artifacts": ["uri1"],
                "rag_stage_outcomes": [],
                "other": "kept",
            }
        )
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
        ):
            store.save(1, kind="k", content=payload)
            entries = store.fetch(1)
        stored = json.loads(entries[0]["content"])
        assert stored["artifacts"] == {"_redacted": True, "count": 1}
        assert stored["rag_stage_outcomes"] == {"_redacted": True, "count": 0}
        assert stored["other"] == "kept"


# ── fetch() encrypted round-trip ────────────────────────────────────────────────


class TestFetchEncryptedRoundTrip:
    def test_fetch_decrypts_encrypted_content(self, fake_db: _FakeSQLiteHelper) -> None:
        """fetch() should decrypt ciphertext when encryption_key is configured."""
        key = Fernet.generate_key().decode("utf-8")
        plaintext = '{"turn": 1}'
        store = _store(encryption_key=key)
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
        ):
            store.save(1, kind="encrypted_entry", content=plaintext)
            entries = store.fetch(1)
        assert len(entries) == 1
        assert entries[0]["kind"] == "encrypted_entry"
        assert json.loads(entries[0]["content"]) == {"turn": 1}

    def test_fetch_leaves_plaintext_when_no_encryption_key(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        """fetch() should leave plaintext unchanged when no encryption_key is configured."""
        plaintext = '{"turn": 1}'
        store = _store()
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
        ):
            store.save(1, kind="plain_entry", content=plaintext)
            entries = store.fetch(1)
        assert len(entries) == 1
        assert entries[0]["content"] == plaintext

    def test_fetch_decrypt_failure_logs_warning_and_marks_format(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        """fetch() marks decrypt_failed + content=None when the stored key no
        longer validates the ciphertext."""
        wrong_key = Fernet.generate_key().decode("utf-8")
        correct_key = Fernet.generate_key().decode("utf-8")
        plaintext = '{"turn": 1}'
        # Encrypt with the correct key (as production would when the key was set).
        correct_store = _store(encryption_key=correct_key)
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
        ):
            correct_store.save(1, kind="bad_decrypt_entry", content=plaintext)
        # Fetch with a store holding a different (rotated/incorrect) key.
        wrong_store = _store(encryption_key=wrong_key)
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
        ):
            entries = wrong_store.fetch(1)
        assert len(entries) == 1
        # The wrong key cannot decrypt the row produced by the correct key.
        assert entries[0]["content"] is None
        assert entries[0]["storage_format"] == "decrypt_failed"


# ── injected config drives behavior (REQ-001/REQ-004/REQ-006) ────────────────


class TestInjectedConfigDrivesBehavior:
    """The injected DiagnosticsConfig snapshot drives save()/fetch() behavior;
    there is no per-operation config load anymore.
    """

    def test_injected_retention_drives_purge(self, fake_db: _FakeSQLiteHelper) -> None:
        old_created_at = (datetime.now(UTC) - timedelta(days=40)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        fake_db.execute(
            "INSERT INTO session_diagnostics (session_id, kind, content, created_at)"
            " VALUES (?, ?, ?, ?)",
            (1, "old_kind", "old content", old_created_at),
        )
        fake_db.commit()
        store = _store(retention_days=5)
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
        ):
            store.save(1, kind="new_kind", content="new content")
        rows = fake_db.fetchall("SELECT kind FROM session_diagnostics")
        kinds = {r[0] for r in rows}
        assert "old_kind" not in kinds  # retention_days=5 purged the 40-day-old row

    def test_injected_key_enables_encryption(self, fake_db: _FakeSQLiteHelper) -> None:
        key = Fernet.generate_key().decode("utf-8")
        store = _store(encryption_key=key)
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
        ):
            store.save(1, kind="k", content='{"q": "x"}')
        (content, fmt) = fake_db.fetchall(
            "SELECT content, storage_format FROM session_diagnostics"
        )[0]
        assert fmt == "encrypted"
        assert content != '{"q": "x"}'

    def test_storage_format_recorded_on_insert(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        store = _store()
        with patch(
            "agent.diagnostic_store.SQLiteHelper",
            side_effect=lambda _, db_config=None: fake_db,
        ):
            store.save(1, kind="k", content="plain")
        (fmt,) = fake_db.fetchall("SELECT storage_format FROM session_diagnostics")
        assert fmt[0] == "plaintext"
