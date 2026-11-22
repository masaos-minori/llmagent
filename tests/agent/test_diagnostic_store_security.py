"""tests/test_diagnostic_store_security.py

Security properties of agent/diagnostic_store.py DiagnosticStore.save():
  - artifacts / rag_stage_outcomes are redacted before persistence
  - sensitive data is refused (fail-closed) without an encryption key
  - sensitive data is Fernet-encrypted by policy when a key is configured
  - the refusal guard tracks agent.secrets_masker.detects_secrets exactly
  - a _filter_sensitive_fields failure fails closed (raises, persists nothing)

The store consumes an injected DiagnosticsConfig snapshot, so every test builds
a DiagnosticsConfig rather than mocking ConfigLoader / _load_diagnostics_config,
and save() takes no encrypt= flag (encryption is purely policy-driven by the
configured key). Regression against procedure 01 (fail-closed store).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any
from unittest.mock import patch

import pytest
from agent.config_dataclasses import DiagnosticsConfig
from agent.diagnostic_store import DiagnosticStore
from agent.secrets_masker import detects_secrets
from cryptography.fernet import Fernet

from tests.agent._config_test_defaults import MIN_DB_CONFIG


class MockConnection:
    """Records executed SQL so tests can inspect what would be persisted."""

    def __init__(self) -> None:
        self.executed_calls: list[tuple[str, tuple[Any, ...]]] = []

    def execute(self, sql: str, params: tuple[Any, ...] | Any = ()) -> MockConnection:
        self.executed_calls.append((sql, params))
        return self

    def commit(self) -> None:
        pass


class MockContext:
    def __init__(self, conn: MockConnection) -> None:
        self._conn = conn

    def __enter__(self) -> MockConnection:
        return self._conn

    def __exit__(self, *args: Any) -> None:
        pass


def _make_store(**overrides: Any) -> DiagnosticStore:
    """Construct a store wired to an injected DiagnosticsConfig."""
    return DiagnosticStore(
        diagnostics_cfg=DiagnosticsConfig(**overrides), db_config=MIN_DB_CONFIG
    )


def _run_save(
    store: DiagnosticStore,
    conn: MockConnection,
    save_fn: Callable[[], None],
) -> None:
    """Run a save operation against a recording MockConnection.

    _purge_old_diagnostics is stubbed because it opens its own SQLiteHelper and
    reads cursor.rowcount, which MockConnection does not provide.
    """
    with patch.object(DiagnosticStore, "_purge_old_diagnostics"):
        with patch("agent.diagnostic_store.SQLiteHelper") as mock_helper:
            mock_ctx = MockContext(conn)
            mock_helper.return_value.open.return_value = mock_ctx
            save_fn()


def _save(
    store: DiagnosticStore,
    conn: MockConnection,
    content: str,
    *,
    kind: str = "test",
) -> None:
    _run_save(store, conn, lambda: store.save(session_id=1, kind=kind, content=content))


def _stored_content(conn: MockConnection) -> str:
    """Return the content argument of the single recorded INSERT."""
    assert len(conn.executed_calls) == 1
    return conn.executed_calls[0][1][2]


class TestArtifactURISanitization:
    """Artifacts / RAG outcomes are redacted before persistence."""

    def test_artifacts_and_rag_outcomes_redacted_before_persist(self) -> None:
        store = _make_store()
        conn = MockConnection()
        payload = (
            '{"artifacts": ["http://sensitive.example.com/path"], '
            '"rag_stage_outcomes": []}'
        )
        _save(store, conn, payload)
        stored = json.loads(_stored_content(conn))
        assert stored["artifacts"] == {"_redacted": True, "count": 1}
        assert stored["rag_stage_outcomes"] == {"_redacted": True, "count": 0}

    def test_non_sensitive_fields_preserved(self) -> None:
        store = _make_store()
        conn = MockConnection()
        _save(store, conn, '{"name": "John Doe", "email": "john@example.com"}')
        stored = json.loads(_stored_content(conn))
        assert stored == {"name": "John Doe", "email": "john@example.com"}


class TestRAGOutcomeMasking:
    """RAG stage outcome masking."""

    def test_rag_stages_are_redacted(self) -> None:
        store = _make_store()
        conn = MockConnection()
        payload = (
            '{"rag_stage_outcomes": [{"result": "secret_data"}, '
            '{"result": "another_secret"}]}'
        )
        _save(store, conn, payload)
        stored = json.loads(_stored_content(conn))
        assert stored["rag_stage_outcomes"] == {"_redacted": True, "count": 2}

    def test_non_list_rag_stages_preserved(self) -> None:
        store = _make_store()
        conn = MockConnection()
        _save(store, conn, '{"rag_stage_outcomes": {"status": "ok"}}')
        stored = json.loads(_stored_content(conn))
        assert stored["rag_stage_outcomes"] == {"status": "ok"}

    def test_invalid_json_not_modified(self) -> None:
        store = _make_store()
        conn = MockConnection()
        _save(store, conn, "not valid json at all")
        assert _stored_content(conn) == "not valid json at all"


class TestLatencySummarySensitivity:
    """Convenience event methods persist without leaking secrets."""

    def test_partial_completion_content_structure(self) -> None:
        store = _make_store()
        conn = MockConnection()
        _run_save(
            store,
            conn,
            lambda: store.save_partial_completion(
                session_id=1,
                turn=5,
                reason="max_tokens_exceeded",
                content_length=10000,
            ),
        )
        stored = json.loads(_stored_content(conn))
        assert stored == {
            "turn": 5,
            "reason": "max_tokens_exceeded",
            "content_length": 10000,
        }

    def test_serialization_event_content_structure(self) -> None:
        store = _make_store()
        conn = MockConnection()
        _run_save(
            store,
            conn,
            lambda: store.save_serialization_event(
                session_id=1,
                round_id="abc123",
                trigger_tool="rag_run_pipeline",
                affected_count=5,
                mode="RAG",
                elapsed_ms=100.0,
                reason="artifact_uri=/etc/shadow;user=admin",
            ),
        )
        stored = json.loads(_stored_content(conn))
        assert stored["round_id"] == "abc123"
        assert stored["trigger_tool"] == "rag_run_pipeline"
        assert stored["affected_count"] == 5
        assert stored["mode"] == "RAG"
        assert stored["elapsed_ms"] == 100.0


class TestEncryptionStatus:
    """Encryption is driven by the configured key, not a caller flag."""

    def test_save_without_key_is_plaintext(self) -> None:
        store = _make_store()
        conn = MockConnection()
        _save(store, conn, "sensitive_content=secret_value")
        assert _stored_content(conn) == "sensitive_content=secret_value"

    def test_save_with_key_is_encrypted(self) -> None:
        key = Fernet.generate_key().decode("utf-8")
        store = _make_store(encryption_key=key)
        conn = MockConnection()
        _save(store, conn, '{"api_key": "abcdefghijklmnop"}')
        stored = _stored_content(conn)
        assert stored != '{"api_key": "abcdefghijklmnop"}'
        decrypted = Fernet(key.encode("utf-8")).decrypt(stored.encode("utf-8"))
        assert json.loads(decrypted) == {"api_key": "abcdefghijklmnop"}


class TestSensitiveDataRefusal:
    """Refuse sensitive data without a key; allow it with one."""

    @pytest.mark.parametrize(
        "sensitive_content",
        [
            '{"api_key": "abcdefghijklmnop"}',
            '{"secret": "1234567890abcdefgh"}',
            '{"token": "abcde12345fghij67890"}',
            '{"password": "supersecretpassword123"}',
            '{"bearer": "bearer_token_extremely_long_string"}',
            '{"client_secret": "client_secret_very_long_string_123"}',
        ],
    )
    def test_refuse_when_sensitive_data_present_without_key(
        self, sensitive_content: str
    ) -> None:
        store = _make_store()
        conn = MockConnection()
        with pytest.raises(RuntimeError, match="Sensitive information detected"):
            _save(store, conn, sensitive_content)
        assert conn.executed_calls == []

    def test_allow_when_sensitive_data_present_with_key(self) -> None:
        key = Fernet.generate_key().decode("utf-8")
        store = _make_store(encryption_key=key)
        conn = MockConnection()
        _save(store, conn, '{"api_key": "abcdefghijklmnop"}')
        stored = _stored_content(conn)
        assert stored != '{"api_key": "abcdefghijklmnop"}'


class TestSharedDetectorGuard:
    """diagmask001 REQ-002/REQ-003/REQ-004: the save() guard must refuse exactly
    what agent.secrets_masker.detects_secrets flags, keep the carve-outs and not
    refuse exemptions. Against the fail-closed store (procedure 01)."""

    REFUSAL_SHAPES = [
        '{"authorization": "Bearer eyJhbGciOiJIUzI1Ni01234567890abcdef.abcdefghijklmnopqrstuv"}',
        '{"credential": "hunter2"}',
        '{"private_key": "abc"}',
        '{"passwd": "topsecret99"}',
        "plain text api_key => sec35",
        '{"note": "see postgres://admin:s3cr3tpw@db:5432/x"}',
        "eyJhbGciOiJIUzI1NiJ9.c2VjcmV0cGF5bG9hZA.qS3pR8xYvZ0aB1cD2eF3gH4i",
    ]
    EXEMPTION_SHAPES = [
        '{"message": "hello world"}',
        "[INCOMPLETE: timeout]",
        "token=***MASKED***",
        '{"token": ""}',
        "https://example.com/api/items",
    ]

    @pytest.mark.parametrize("sensitive_content", REFUSAL_SHAPES)
    def test_refuses_new_shapes_without_key(self, sensitive_content: str) -> None:
        """New shapes must raise with zero INSERTs."""
        store = _make_store()
        conn = MockConnection()
        with pytest.raises(RuntimeError, match="Sensitive information detected"):
            _save(store, conn, sensitive_content)
        assert conn.executed_calls == []

    @pytest.mark.parametrize("content", REFUSAL_SHAPES + EXEMPTION_SHAPES)
    def test_guard_matches_shared_detector(self, content: str) -> None:
        """AC-1: save() raises exactly when detects_secrets(content) is True."""
        store = _make_store()
        conn = MockConnection()
        expected_refusal = detects_secrets(content)
        if expected_refusal:
            with pytest.raises(RuntimeError, match="Sensitive information detected"):
                _save(store, conn, content)
        else:
            _save(store, conn, content)
        assert len(conn.executed_calls) == (0 if expected_refusal else 1)

    @pytest.mark.parametrize("content", EXEMPTION_SHAPES)
    def test_saves_exemptions_without_raise(self, content: str) -> None:
        """AC-4 exemptions save unchanged with the INSERT executed."""
        store = _make_store()
        conn = MockConnection()
        _save(store, conn, content)
        assert len(conn.executed_calls) == 1
        assert _stored_content(conn) == content

    @pytest.mark.parametrize(
        "content", ['{"credential": "hunter2"}', "api_key => topsecretxyz"]
    )
    def test_encrypted_path_still_saves_new_shapes(self, content: str) -> None:
        """AC-4: with a key configured, AC-3 shapes store as ciphertext without raising."""
        key = Fernet.generate_key().decode("utf-8")
        store = _make_store(encryption_key=key)
        conn = MockConnection()
        _save(store, conn, content)
        assert len(conn.executed_calls) == 1
        assert content not in _stored_content(conn)

    def test_filter_failure_raises_and_persists_nothing(self) -> None:
        """Fail-closed (procedure 01): a _filter_sensitive_fields failure raises
        RuntimeError and no INSERT is executed — the old fail-open carve-out is
        gone."""
        store = _make_store()
        conn = MockConnection()
        with pytest.raises(RuntimeError, match="Redaction failed"):
            with patch.object(
                DiagnosticStore,
                "_filter_sensitive_fields",
                side_effect=Exception("filter boom"),
            ):
                _save(store, conn, '{"api_key": "abcdefghijklmnop"}')
        assert conn.executed_calls == []
