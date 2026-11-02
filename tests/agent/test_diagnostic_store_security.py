from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from agent.diagnostic_store import DiagnosticStore
from cryptography.fernet import Fernet


class MockConnection:
    def __init__(self):
        self.executed_calls = []

    def execute(self, sql: str, params: tuple[Any, ...] | Any) -> MockConnection:
        self.executed_calls.append((sql, params))
        return self

    def commit(self) -> None:
        pass


class MockContext:
    def __enter__(self) -> MockConnection:
        return self._conn

    def __exit__(self, *args: Any) -> None:
        pass

    def __init__(self, conn: MockConnection):
        self._conn = conn


class TestArtifactURISanitization:
    """Test artifact URI sanitization — verify filtered before persistence."""

    def test_artifact_uris_are_redacted_in_json(self, tmp_path: Any) -> None:
        """Artifacts field should be redacted when saved via save()."""
        store = DiagnosticStore()
        store.session_id = 1

        with patch.object(DiagnosticStore, "_purge_old_diagnostics"):
            with patch("agent.diagnostic_store.SQLiteHelper") as mock_helper:
                mock_conn = MockConnection()
                mock_ctx = MockContext(mock_conn)
                mock_helper.return_value.open.return_value = mock_ctx
                store.save(
                    session_id=1,
                    kind="test",
                    content='{"artifacts": ["http://sensitive.example.com/path"], "rag_stage_outcomes": []}',
                )

    def test_non_artifact_content_preserved(self, tmp_path: Any) -> None:
        """Non-sensitive fields should be preserved."""
        store = DiagnosticStore()
        store.session_id = 1

        with patch.object(DiagnosticStore, "_purge_old_diagnostics"):
            with patch("agent.diagnostic_store.SQLiteHelper") as mock_helper:
                mock_conn = MockConnection()
                mock_ctx = MockContext(mock_conn)
                mock_helper.return_value.open.return_value = mock_ctx
                store.save(
                    session_id=1,
                    kind="test",
                    content='{"name": "John Doe", "email": "john@example.com"}',
                )


class TestRAGOutcomeMasking:
    """Test RAG outcome masking — verify masked before persistence."""

    def test_rag_stages_are_redacted(self, tmp_path: Any) -> None:
        """rag_stage_outcomes should be redacted when saved via save()."""
        store = DiagnosticStore()
        store.session_id = 1

        with patch.object(DiagnosticStore, "_purge_old_diagnostics"):
            with patch("agent.diagnostic_store.SQLiteHelper") as mock_helper:
                mock_conn = MockConnection()
                mock_ctx = MockContext(mock_conn)
                mock_helper.return_value.open.return_value = mock_ctx
                store.save(
                    session_id=1,
                    kind="test",
                    content='{"rag_stage_outcomes": [{"result": "secret_data"}, {"result": "another_secret"}]}',
                )

    def test_non_list_rag_stages_preserved(self, tmp_path: Any) -> None:
        """Non-list rag_stage_outcomes should not be redacted."""
        store = DiagnosticStore()
        store.session_id = 1

        with patch.object(DiagnosticStore, "_purge_old_diagnostics"):
            with patch("agent.diagnostic_store.SQLiteHelper") as mock_helper:
                mock_conn = MockConnection()
                mock_ctx = MockContext(mock_conn)
                mock_helper.return_value.open.return_value = mock_ctx
                store.save(
                    session_id=1,
                    kind="test",
                    content='{"rag_stage_outcomes": {"status": "ok"}}',
                )

    def test_invalid_json_not_modified(self, tmp_path: Any) -> None:
        """Invalid JSON should pass through unchanged."""
        store = DiagnosticStore()
        store.session_id = 1

        with patch.object(DiagnosticStore, "_purge_old_diagnostics"):
            with patch("agent.diagnostic_store.SQLiteHelper") as mock_helper:
                mock_conn = MockConnection()
                mock_ctx = MockContext(mock_conn)
                mock_helper.return_value.open.return_value = mock_ctx
                store.save(
                    session_id=1,
                    kind="test",
                    content="not valid json at all",
                )


class TestLatencySummarySensitivity:
    """Test latency summary sensitivity — verify no internal details exposed."""

    def test_partial_completion_content_structure(self, tmp_path: Any) -> None:
        """Partial completion should contain expected fields without secrets."""
        store = DiagnosticStore()
        store.session_id = 1

        with patch.object(DiagnosticStore, "_purge_old_diagnostics"):
            with patch("agent.diagnostic_store.SQLiteHelper") as mock_helper:
                mock_conn = MockConnection()
                mock_ctx = MockContext(mock_conn)
                mock_helper.return_value.open.return_value = mock_ctx
                store.save_partial_completion(
                    session_id=1,
                    turn=5,
                    reason="max_tokens_exceeded",
                    content_length=10000,
                )

    def test_serialization_event_content_structure(self, tmp_path: Any) -> None:
        """Serialization event should contain expected fields."""
        store = DiagnosticStore()
        store.session_id = 1

        with patch.object(DiagnosticStore, "_purge_old_diagnostics"):
            with patch("agent.diagnostic_store.SQLiteHelper") as mock_helper:
                mock_conn = MockConnection()
                mock_ctx = MockContext(mock_conn)
                mock_helper.return_value.open.return_value = mock_ctx
                store.save_serialization_event(
                    session_id=1,
                    round_id="abc123",
                    trigger_tool="rag_run_pipeline",
                    affected_count=5,
                    mode="RAG",
                    elapsed_ms=100.0,
                    reason="artifact_uri=/etc/shadow;user=admin",
                )


class TestEncryptionStatus:
    """Test encryption status — verify encrypted vs plaintext storage."""

    def test_save_without_encrypt_is_plaintext(self, tmp_path: Any) -> None:
        """save() without encrypt=True should store plaintext."""
        store = DiagnosticStore()
        store.session_id = 1

        with patch.object(DiagnosticStore, "_purge_old_diagnostics"):
            with patch("agent.diagnostic_store.SQLiteHelper") as mock_helper:
                mock_conn = MockConnection()
                mock_ctx = MockContext(mock_conn)
                mock_helper.return_value.open.return_value = mock_ctx
                store.save(
                    session_id=1,
                    kind="test",
                    content="sensitive_content=secret_value",
                    encrypt=False,
                )

        assert len(mock_conn.executed_calls) == 1
        assert "sensitive_content=secret_value" in mock_conn.executed_calls[0][1][2]

    def test_save_with_encrypt_and_key_is_encrypted(self, tmp_path: Any) -> None:
        """save() with encrypt=True and key configured should store encrypted data."""
        store = DiagnosticStore()
        store.session_id = 1
        fernet_key = Fernet.generate_key().decode("utf-8")

        with patch.object(DiagnosticStore, "_purge_old_diagnostics"):
            with patch.object(
                DiagnosticStore, "_load_diagnostics_config"
            ) as mock_load_cfg:
                mock_cfg = type(
                    "MockConfig",
                    (),
                    {"encryption_key": fernet_key, "sensitive_fields": frozenset()},
                )()
                mock_load_cfg.return_value = mock_cfg
                with patch("agent.diagnostic_store.SQLiteHelper") as mock_helper:
                    mock_conn = MockConnection()
                    mock_ctx = MockContext(mock_conn)
                    mock_helper.return_value.open.return_value = mock_ctx
                    store.save(
                        session_id=1,
                        kind="test",
                        content='{"api_key": "abcdefghijklmnop"}',
                        encrypt=True,
                    )

        assert len(mock_conn.executed_calls) == 1
        # Encrypted content should NOT contain the original text
        assert (
            '{"api_key": "abcdefghijklmnop"}' not in mock_conn.executed_calls[0][1][2]
        )

    def test_save_with_encrypt_but_no_key_raises_on_sensitive_data(
        self, tmp_path: Any
    ) -> None:
        """save() with encrypt=True but no key should raise on sensitive data."""
        store = DiagnosticStore()
        store.session_id = 1

        from unittest.mock import patch

        with patch.object(DiagnosticStore, "_purge_old_diagnostics"):
            with patch.object(
                DiagnosticStore, "_load_diagnostics_config"
            ) as mock_load_cfg:
                mock_cfg = type(
                    "MockConfig",
                    (),
                    {"encryption_key": "", "sensitive_fields": frozenset()},
                )()
                mock_load_cfg.return_value = mock_cfg
                with patch("agent.diagnostic_store.SQLiteHelper") as mock_helper:
                    mock_conn = MockConnection()
                    mock_ctx = MockContext(mock_conn)
                    mock_helper.return_value.open.return_value = mock_ctx
                    with pytest.raises(
                        RuntimeError, match="Sensitive information detected"
                    ):
                        store.save(
                            session_id=1,
                            kind="test",
                            content='{"api_key": "abcdefghijklmnop"}',
                            encrypt=True,
                        )

        assert len(mock_conn.executed_calls) == 0


class TestSensitiveDataRefusal:
    """Test refusal when sensitive data is present without a key."""

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
        self, tmp_path: Any, sensitive_content: str
    ) -> None:
        """Should raise RuntimeError when sensitive data is detected and no key is configured."""
        from unittest.mock import patch

        store = DiagnosticStore()
        store.session_id = 1

        with patch.object(DiagnosticStore, "_purge_old_diagnostics"):
            with patch("agent.diagnostic_store.SQLiteHelper") as mock_helper:
                mock_conn = MockConnection()
                mock_ctx = MockContext(mock_conn)
                mock_helper.return_value.open.return_value = mock_ctx

                with pytest.raises(
                    RuntimeError, match="Sensitive information detected"
                ):
                    store.save(
                        session_id=1,
                        kind="test",
                        content=sensitive_content,
                        encrypt=False,
                    )

    def test_allow_when_sensitive_data_present_with_key(self, tmp_path: Any) -> None:
        """Should allow saving when an encryption key is provided."""
        from unittest.mock import patch

        from cryptography.fernet import Fernet

        store = DiagnosticStore()
        store.session_id = 1
        fernet_key = Fernet.generate_key().decode("utf-8")

        with patch.object(DiagnosticStore, "_purge_old_diagnostics"):
            with patch.object(
                DiagnosticStore, "_load_diagnostics_config"
            ) as mock_load_cfg:
                mock_cfg = type(
                    "MockConfig",
                    (),
                    {"encryption_key": fernet_key, "sensitive_fields": frozenset()},
                )()
                mock_load_cfg.return_value = mock_cfg
                with patch("agent.diagnostic_store.SQLiteHelper") as mock_helper:
                    mock_conn = MockConnection()
                    mock_ctx = MockContext(mock_conn)
                    mock_helper.return_value.open.return_value = mock_ctx
                    store.save(
                        session_id=1,
                        kind="test",
                        content='{"api_key": "abcdefghijklmnop"}',
                        encrypt=True,
                    )

        assert len(mock_conn.executed_calls) == 1
        # Encrypted content should NOT contain the original text
        assert (
            '{"api_key": "abcdefghijklmnop"}' not in mock_conn.executed_calls[0][1][2]
        )


class TestSharedDetectorGuard:
    """diagmask001 REQ-002/REQ-003/REQ-004: the save() guard must refuse exactly
    what agent.secrets_masker.detects_secrets flags, keep the carve-outs and not
    refuse exemptions. Red against the pre-consolidation guard (Plan Phase 1)."""

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

    @staticmethod
    def _save_with_empty_key(
        store: DiagnosticStore, content: str, mock_conn: MockConnection
    ) -> None:
        mock_cfg = type(
            "MockConfig",
            (),
            {"encryption_key": "", "sensitive_fields": frozenset()},
        )()
        with patch.object(DiagnosticStore, "_purge_old_diagnostics"):
            with patch.object(
                DiagnosticStore, "_load_diagnostics_config"
            ) as mock_load_cfg:
                mock_load_cfg.return_value = mock_cfg
                with patch("agent.diagnostic_store.SQLiteHelper") as mock_helper:
                    mock_ctx = MockContext(mock_conn)
                    mock_helper.return_value.open.return_value = mock_ctx
                    store.save(
                        session_id=1,
                        kind="test",
                        content=content,
                        encrypt=False,
                    )

    @pytest.mark.parametrize("sensitive_content", REFUSAL_SHAPES)
    def test_refuses_new_shapes_without_key(
        self, tmp_path: Any, sensitive_content: str
    ) -> None:
        """New shapes must raise with zero INSERTs; the old guard misses them today."""
        store = DiagnosticStore()
        store.session_id = 1
        mock_conn = MockConnection()
        with pytest.raises(RuntimeError, match="Sensitive information detected"):
            self._save_with_empty_key(store, sensitive_content, mock_conn)
        assert len(mock_conn.executed_calls) == 0

    @pytest.mark.parametrize("content", REFUSAL_SHAPES + EXEMPTION_SHAPES)
    def test_guard_matches_shared_detector(self, tmp_path: Any, content: str) -> None:
        """AC-1: save() raises exactly when detects_secrets(content) is True."""
        from agent.secrets_masker import detects_secrets

        store = DiagnosticStore()
        store.session_id = 1
        expected_refusal = detects_secrets(content)
        mock_conn = MockConnection()
        if expected_refusal:
            with pytest.raises(RuntimeError, match="Sensitive information detected"):
                self._save_with_empty_key(store, content, mock_conn)
        else:
            self._save_with_empty_key(store, content, mock_conn)
        assert len(mock_conn.executed_calls) == (0 if expected_refusal else 1)

    @pytest.mark.parametrize("content", EXEMPTION_SHAPES)
    def test_saves_exemptions_without_raise(self, tmp_path: Any, content: str) -> None:
        """AC-4 exemptions save unchanged with the INSERT executed."""
        store = DiagnosticStore()
        store.session_id = 1
        mock_conn = MockConnection()
        self._save_with_empty_key(store, content, mock_conn)
        assert len(mock_conn.executed_calls) == 1
        assert mock_conn.executed_calls[0][1][2] == content

    @pytest.mark.parametrize(
        "content", ['{"credential": "hunter2"}', "api_key => topsecretxyz"]
    )
    def test_encrypted_path_still_saves_new_shapes(
        self, tmp_path: Any, content: str
    ) -> None:
        """AC-4: with a key configured, AC-3 shapes store as ciphertext without raising."""
        from cryptography.fernet import Fernet

        store = DiagnosticStore()
        store.session_id = 1
        fernet_key = Fernet.generate_key().decode("utf-8")
        mock_cfg = type(
            "MockConfig",
            (),
            {"encryption_key": fernet_key, "sensitive_fields": frozenset()},
        )()
        mock_conn = MockConnection()
        with patch.object(DiagnosticStore, "_purge_old_diagnostics"):
            with patch.object(
                DiagnosticStore, "_load_diagnostics_config"
            ) as mock_load_cfg:
                mock_load_cfg.return_value = mock_cfg
                with patch("agent.diagnostic_store.SQLiteHelper") as mock_helper:
                    mock_ctx = MockContext(mock_conn)
                    mock_helper.return_value.open.return_value = mock_ctx
                    store.save(
                        session_id=1,
                        kind="test",
                        content=content,
                        encrypt=True,
                    )
        assert len(mock_conn.executed_calls) == 1
        assert content not in mock_conn.executed_calls[0][1][2]

    def test_filter_failed_carve_out_preserved(
        self, tmp_path: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """AC-4 carve-out: a failing _filter_sensitive_fields persists the
        secret-bearing content unencrypted with a logged warning and no raise."""
        import logging

        store = DiagnosticStore()
        store.session_id = 1
        mock_cfg = type(
            "MockConfig",
            (),
            {"encryption_key": "", "sensitive_fields": frozenset()},
        )()
        mock_conn = MockConnection()
        with caplog.at_level(logging.WARNING, logger="agent.diagnostic_store"):
            with patch.object(DiagnosticStore, "_purge_old_diagnostics"):
                with patch.object(
                    DiagnosticStore, "_load_diagnostics_config"
                ) as mock_load_cfg:
                    mock_load_cfg.return_value = mock_cfg
                    with patch.object(
                        DiagnosticStore,
                        "_filter_sensitive_fields",
                        side_effect=Exception("filter boom"),
                    ):
                        with patch(
                            "agent.diagnostic_store.SQLiteHelper"
                        ) as mock_helper:
                            mock_ctx = MockContext(mock_conn)
                            mock_helper.return_value.open.return_value = mock_ctx
                            store.save(
                                session_id=1,
                                kind="test",
                                content='{"api_key": "abcdefghijklmnop"}',
                                encrypt=False,
                            )
        assert len(mock_conn.executed_calls) == 1
        assert mock_conn.executed_calls[0][1][2] == '{"api_key": "abcdefghijklmnop"}'
        assert any(
            "_filter_sensitive_fields failed" in record.getMessage()
            for record in caplog.records
        )
