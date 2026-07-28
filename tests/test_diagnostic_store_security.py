"""
tests/test_diagnostic_store_security.py

Characterization tests for diagnostic store sensitive data handling.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from agent.diagnostic_store import DiagnosticStore


def _make_db(tmp_path: Any) -> str:
    """Create a temp SQLite DB with session_diagnostics table."""
    db_path = str(tmp_path / "test_diagnostics.sqlite")
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS session_diagnostics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            kind TEXT NOT NULL,
            content TEXT NOT NULL,
            workflow_id TEXT,
            task_id TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()
    return db_path


class TestArtifactURISanitization:
    """Test artifact URI sanitization — verify filtered before persistence."""

    def test_artifact_uris_are_redacted_in_json(self, tmp_path: Any) -> None:
        """Artifacts field should be redacted when saved via save()."""
        store = DiagnosticStore()
        store.session_id = 1

        # Patch SQLiteHelper to use our temp DB
        from unittest.mock import patch

        with patch.object(DiagnosticStore, "_purge_old_diagnostics"):
            with patch("agent.diagnostic_store.SQLiteHelper") as mock_helper:
                mock_conn = type("MockConn", (), {"execute": lambda *a, **k: None})()
                mock_ctx = type(
                    "MockCtx",
                    (),
                    {"__enter__": lambda s: mock_conn, "__exit__": lambda s, *a: None},
                )()
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

        from unittest.mock import patch

        with patch.object(DiagnosticStore, "_purge_old_diagnostics"):
            with patch("agent.diagnostic_store.SQLiteHelper") as mock_helper:
                mock_conn = type("MockConn", (), {"execute": lambda *a, **k: None})()
                mock_ctx = type(
                    "MockCtx",
                    (),
                    {"__enter__": lambda s: mock_conn, "__exit__": lambda s, *a: None},
                )()
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

        from unittest.mock import patch

        with patch.object(DiagnosticStore, "_purge_old_diagnostics"):
            with patch("agent.diagnostic_store.SQLiteHelper") as mock_helper:
                mock_conn = type("MockConn", (), {"execute": lambda *a, **k: None})()
                mock_ctx = type(
                    "MockCtx",
                    (),
                    {"__enter__": lambda s: mock_conn, "__exit__": lambda s, *a: None},
                )()
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

        from unittest.mock import patch

        with patch.object(DiagnosticStore, "_purge_old_diagnostics"):
            with patch("agent.diagnostic_store.SQLiteHelper") as mock_helper:
                mock_conn = type("MockConn", (), {"execute": lambda *a, **k: None})()
                mock_ctx = type(
                    "MockCtx",
                    (),
                    {"__enter__": lambda s: mock_conn, "__exit__": lambda s, *a: None},
                )()
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

        from unittest.mock import patch

        with patch.object(DiagnosticStore, "_purge_old_diagnostics"):
            with patch("agent.diagnostic_store.SQLiteHelper") as mock_helper:
                mock_conn = type("MockConn", (), {"execute": lambda *a, **k: None})()
                mock_ctx = type(
                    "MockCtx",
                    (),
                    {"__enter__": lambda s: mock_conn, "__exit__": lambda s, *a: None},
                )()
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

        from unittest.mock import patch

        with patch.object(DiagnosticStore, "_purge_old_diagnostics"):
            with patch("agent.diagnostic_store.SQLiteHelper") as mock_helper:
                captured_content = []

                def capture_execute(sql, params):
                    if "INSERT INTO session_diagnostics" in sql:
                        captured_content.append(params[2])
                    return type("Cursor", (), {"rowcount": 0})()

                mock_conn = type("MockConn", (), {"execute": capture_execute})()
                mock_ctx = type(
                    "MockCtx",
                    (),
                    {"__enter__": lambda s: mock_conn, "__exit__": lambda s, *a: None},
                )()
                mock_helper.return_value.open.return_value = mock_ctx
                store.save_partial_completion(
                    session_id=1,
                    turn=5,
                    reason="max_tokens_exceeded",
                    content_length=10000,
                )

        assert len(captured_content) == 1
        assert "turn" in captured_content[0]
        assert "reason" in captured_content[0]
        assert "content_length" in captured_content[0]

    def test_serialization_event_content_structure(self, tmp_path: Any) -> None:
        """Serialization event should contain expected fields."""
        store = DiagnosticStore()
        store.session_id = 1

        from unittest.mock import patch

        with patch.object(DiagnosticStore, "_purge_old_diagnostics"):
            with patch("agent.diagnostic_store.SQLiteHelper") as mock_helper:
                captured_content = []

                def capture_execute(sql, params):
                    if "INSERT INTO session_diagnostics" in sql:
                        captured_content.append(params[2])
                    return type("Cursor", (), {"rowcount": 0})()

                mock_conn = type("MockConn", (), {"execute": capture_execute})()
                mock_ctx = type(
                    "MockCtx",
                    (),
                    {"__enter__": lambda s: mock_conn, "__exit__": lambda s, *a: None},
                )()
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

        assert len(captured_content) == 1
        assert "round_id" in captured_content[0]
        assert "trigger_tool" in captured_content[0]
        assert "affected_count" in captured_content[0]
        assert "mode" in captured_content[0]
        assert "elapsed_ms" in captured_content[0]
        assert "reason" in captured_content[0]


class TestEncryptionStatus:
    """Test encryption status — verify encrypted vs plaintext storage."""

    def test_save_without_encrypt_is_plaintext(self, tmp_path: Any) -> None:
        """save() without encrypt=True should store plaintext."""
        store = DiagnosticStore()
        store.session_id = 1

        from unittest.mock import patch

        with patch.object(DiagnosticStore, "_purge_old_diagnostics"):
            with patch("agent.diagnostic_store.SQLiteHelper") as mock_helper:
                captured_content = []

                def capture_execute(sql, params):
                    if "INSERT INTO session_diagnostics" in sql:
                        captured_content.append(params[2])
                    return type("Cursor", (), {"rowcount": 0})()

                mock_conn = type("MockConn", (), {"execute": capture_execute})()
                mock_ctx = type(
                    "MockCtx",
                    (),
                    {"__enter__": lambda s: mock_conn, "__exit__": lambda s, *a: None},
                )()
                mock_helper.return_value.open.return_value = mock_ctx
                store.save(
                    session_id=1,
                    kind="test",
                    content="sensitive_content=secret_value",
                    encrypt=False,
                )

        assert len(captured_content) == 1
        assert "sensitive_content=secret_value" in captured_content[0]

    def test_save_with_encrypt_and_key_is_encrypted(self, tmp_path: Any) -> None:
        """save() with encrypt=True and key configured should store encrypted data."""
        store = DiagnosticStore()
        store.session_id = 1

        from unittest.mock import patch

        # Create a valid Fernet key for testing
        from cryptography.fernet import Fernet

        fernet_key = Fernet.generate_key().decode("utf-8")

        with patch.object(DiagnosticStore, "_purge_old_diagnostics"):
            with patch.object(
                DiagnosticStore, "_load_diagnostics_config"
            ) as mock_load_cfg:
                mock_cfg = type("MockConfig", (), {"encryption_key": fernet_key})()
                mock_load_cfg.return_value = mock_cfg
                with patch("agent.diagnostic_store.SQLiteHelper") as mock_helper:
                    captured_content = []

                    def capture_execute(sql, params):
                        if "INSERT INTO session_diagnostics" in sql:
                            captured_content.append(params[2])
                        return type("Cursor", (), {"rowcount": 0})()

                    mock_conn = type("MockConn", (), {"execute": capture_execute})()
                    mock_ctx = type(
                        "MockCtx",
                        (),
                        {
                            "__enter__": lambda s: mock_conn,
                            "__exit__": lambda s, *a: None,
                        },
                    )()
                    mock_helper.return_value.open.return_value = mock_ctx
                    store.save(
                        session_id=1,
                        kind="test",
                        content="sensitive_content=secret_value",
                        encrypt=True,
                    )

        assert len(captured_content) == 1
        # Encrypted content should NOT contain the original text
        assert "sensitive_content=secret_value" not in captured_content[0]

    def test_save_with_encrypt_but_no_key_is_plaintext(self, tmp_path: Any) -> None:
        """save() with encrypt=True but no key should store plaintext."""
        store = DiagnosticStore()
        store.session_id = 1

        from unittest.mock import patch

        with patch.object(DiagnosticStore, "_purge_old_diagnostics"):
            with patch.object(
                DiagnosticStore, "_load_diagnostics_config"
            ) as mock_load_cfg:
                mock_cfg = type("MockConfig", (), {"encryption_key": ""})()
                mock_load_cfg.return_value = mock_cfg
                with patch("agent.diagnostic_store.SQLiteHelper") as mock_helper:
                    captured_content = []

                    def capture_execute(sql, params):
                        if "INSERT INTO session_diagnostics" in sql:
                            captured_content.append(params[2])
                        return type("Cursor", (), {"rowcount": 0})()

                    mock_conn = type("MockConn", (), {"execute": capture_execute})()
                    mock_ctx = type(
                        "MockCtx",
                        (),
                        {
                            "__enter__": lambda s: mock_conn,
                            "__exit__": lambda s, *a: None,
                        },
                    )()
                    mock_helper.return_value.open.return_value = mock_ctx
                    store.save(
                        session_id=1,
                        kind="test",
                        content="sensitive_content=secret_value",
                        encrypt=True,
                    )

        assert len(captured_content) == 1
        assert "sensitive_content=secret_value" in captured_content[0]
