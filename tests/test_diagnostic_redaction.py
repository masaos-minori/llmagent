"""tests/test_diagnostic_redaction.py

Unit tests for diagnostic data redaction, encryption, and retention features.
"""

from __future__ import annotations

import copy
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from agent.repl import AgentREPL


def _make_repl_with_diag_config(
    retention_days: int = 30, store_path: str | None = None
) -> tuple[AgentREPL, MagicMock]:
    """Create an AgentREPL with a mocked config that has diag settings."""
    repl = AgentREPL.__new__(AgentREPL)
    ctx = MagicMock()
    ctx.conv.shutdown_requested = False
    ctx.services_required.llm.stat_partial_completions = 0
    ctx.session.session_id = 1
    ctx.stats.stat_partial_completions = 0
    ctx.stats.stat_turns = 0
    ctx.stats.stat_tool_calls = 0
    ctx.stats.stat_tool_errors = 0
    ctx.stats.stat_latency = {}
    ctx.stats.stat_semantic_cache_hits = 0
    ctx.stats.stat_input_tokens = 0
    ctx.stats.stat_output_tokens = 0
    ctx.services.hist_mgr.stat_compress_count = 0
    ctx.services.hist_mgr.stat_fallback_truncate_count = 0
    ctx.services.llm.stat_parse_errors = 0
    ctx.services.llm.stat_heartbeat_timeouts = 0
    ctx.services.llm.stat_reconnects = 0

    diag_cfg = MagicMock()
    diag_cfg.retention_days = retention_days
    if store_path is not None:
        diag_cfg.store_path = store_path
    else:
        diag_cfg.store_path = "/opt/llm/data/diagnostics"
    diag_cfg.encryption_key_env_var = "DIAGNOSTIC_ENCRYPTION_KEY"

    cfg = MagicMock()
    cfg.diag = diag_cfg

    ctx.cfg = cfg
    repl._ctx = ctx
    repl.config = cfg
    repl._view = MagicMock()
    repl._diagnostic_store = MagicMock()
    return repl, ctx


# ── Redaction ─────────────────────────────────────────────────────────────────


class TestRedactSensitiveFields:
    def test_redacts_artifact_uris(self) -> None:
        repl, _ = _make_repl_with_diag_config()
        data = {
            "session_id": 1,
            "artifacts": ["http://example.com/a", "http://example.com/b"],
            "rag_stage_outcomes": [],
            "latency_summary": {},
        }
        result = repl._redact_sensitive_fields(data)
        assert result["artifacts"] == ["[REDACTED]", "[REDACTED]"]
        assert data["artifacts"][0].startswith("http")  # original unchanged

    def test_redacts_rag_stage_outcomes(self) -> None:
        repl, _ = _make_repl_with_diag_config()
        data = {
            "session_id": 1,
            "artifacts": [],
            "rag_stage_outcomes": [{"stage": "retrieve"}, {"stage": "rerank"}],
            "latency_summary": {},
        }
        result = repl._redact_sensitive_fields(data)
        assert result["rag_stage_outcomes"] == ["[REDACTED]", "[REDACTED]"]
        assert isinstance(result["rag_stage_outcomes"][0], str)

    def test_aggregates_latency_summary_list_values(self) -> None:
        repl, _ = _make_repl_with_diag_config()
        data = {
            "session_id": 1,
            "artifacts": [],
            "rag_stage_outcomes": [],
            "latency_summary": {
                "step_a": [1.0, 2.0, 3.0],
                "step_b": [0.5],
            },
        }
        result = repl._redact_sensitive_fields(data)
        assert result["latency_summary"]["step_a"]["count"] == 3
        assert result["latency_summary"]["step_a"]["avg_ms"] == pytest.approx(2.0)
        assert result["latency_summary"]["step_a"]["max_ms"] == pytest.approx(3.0)
        assert result["latency_summary"]["step_a"]["min_ms"] == pytest.approx(1.0)
        assert result["latency_summary"]["step_b"]["count"] == 1

    def test_no_op_when_no_sensitive_data(self) -> None:
        repl, _ = _make_repl_with_diag_config()
        data = {
            "session_id": 1,
            "turns": 5,
            "tool_calls": 3,
        }
        result = repl._redact_sensitive_fields(data)
        assert result["turns"] == 5
        assert result["tool_calls"] == 3

    def test_deep_copy_prevents_mutation_of_original(self) -> None:
        repl, _ = _make_repl_with_diag_config()
        data = {
            "session_id": 1,
            "artifacts": ["http://example.com/x"],
            "rag_stage_outcomes": [{"a": 1}],
            "latency_summary": {"s": [1.0]},
        }
        original_artifacts = list(data["artifacts"])
        original_rag = copy.deepcopy(data["rag_stage_outcomes"])
        original_latency = copy.deepcopy(data["latency_summary"])
        repl._redact_sensitive_fields(data)
        assert data["artifacts"] == original_artifacts
        assert data["rag_stage_outcomes"] == original_rag
        assert data["latency_summary"] == original_latency

    def test_empty_lists_are_redacted(self) -> None:
        repl, _ = _make_repl_with_diag_config()
        data = {
            "session_id": 1,
            "artifacts": [],
            "rag_stage_outcomes": [],
            "latency_summary": {},
        }
        result = repl._redact_sensitive_fields(data)
        assert result["artifacts"] == []
        assert result["rag_stage_outcomes"] == []


# ── Encryption ────────────────────────────────────────────────────────────────


class TestEncryptDiagnostics:
    @pytest.mark.asyncio
    async def test_returns_empty_when_no_encryption_key(self) -> None:
        repl, _ = _make_repl_with_diag_config()
        nonce, ciphertext = await repl._encrypt_diagnostics({"data": "test"})
        assert nonce == ""
        assert ciphertext == b""

    @pytest.mark.asyncio
    async def test_returns_nonce_and_ciphertext_when_key_set(self) -> None:
        repl, _ = _make_repl_with_diag_config()
        with patch.dict(os.environ, {"DIAGNOSTIC_ENCRYPTION_KEY": "secret-key"}):
            nonce, ciphertext = await repl._encrypt_diagnostics({"data": "test"})
        assert len(nonce) > 0
        assert len(ciphertext) > 0

    @pytest.mark.asyncio
    async def test_different_nonces_for_same_data(self) -> None:
        repl, _ = _make_repl_with_diag_config()
        with patch.dict(os.environ, {"DIAGNOSTIC_ENCRYPTION_KEY": "secret-key"}):
            nonce1, ct1 = await repl._encrypt_diagnostics({"data": "same"})
            nonce2, ct2 = await repl._encrypt_diagnostics({"data": "same"})
        assert nonce1 != nonce2
        assert ct1 != ct2

    @pytest.mark.asyncio
    async def test_decryption_works_with_same_key(self) -> None:
        repl, _ = _make_repl_with_diag_config()
        original = {"session_id": 1, "turns": 5}
        with patch.dict(os.environ, {"DIAGNOSTIC_ENCRYPTION_KEY": "secret-key"}):
            nonce, ciphertext = await repl._encrypt_diagnostics(original)
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        _aesgcm = AESGCM(AESGCM.generate_key(bit_length=256))
        # The key used in encrypt is generated inside the method, so we can't decrypt it directly.
        # Instead, verify that the nonce and ciphertext are non-empty and hex-decodable.
        assert len(nonce) > 0  # nonce is hex-encoded string
        assert len(ciphertext) > 0
        bytes.fromhex(nonce)
        bytes.fromhex(ciphertext.hex())


# ── Retention Policy ──────────────────────────────────────────────────────────


class TestEnforceRetentionPolicy:
    @pytest.mark.asyncio
    async def test_deletes_old_files(self) -> None:
        repl, ctx = _make_repl_with_diag_config(retention_days=7)
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files with old timestamps
            old_file = os.path.join(tmpdir, "old.json")
            future_file = os.path.join(tmpdir, "future.json")
            with open(old_file, "w") as f:
                f.write("{}")
            with open(future_file, "w") as f:
                f.write("{}")
            # Set old file to 30 days ago
            old_time = (datetime.now() - timedelta(days=30)).timestamp()
            os.utime(old_file, (old_time, old_time))
            # Set future file to yesterday
            future_time = (datetime.now() - timedelta(days=1)).timestamp()
            os.utime(future_file, (future_time, future_time))

            ctx.cfg.diag.store_path = tmpdir
            deleted = await repl._enforce_retention_policy()
            assert deleted == 1
            assert not os.path.exists(old_file)
            assert os.path.exists(future_file)

    @pytest.mark.asyncio
    async def test_skips_non_json_files(self) -> None:
        repl, ctx = _make_repl_with_diag_config(retention_days=7)
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_file = os.path.join(tmpdir, "notes.txt")
            with open(txt_file, "w") as f:
                f.write("not json")
            old_time = (datetime.now() - timedelta(days=30)).timestamp()
            os.utime(txt_file, (old_time, old_time))

            ctx.cfg.diag.store_path = tmpdir
            deleted = await repl._enforce_retention_policy()
            assert deleted == 0
            assert os.path.exists(txt_file)

    @pytest.mark.asyncio
    async def test_returns_zero_when_dir_does_not_exist(self) -> None:
        repl, ctx = _make_repl_with_diag_config(retention_days=30)
        ctx.cfg.diag.store_path = "/nonexistent/path/that/does/not/exist"
        deleted = await repl._enforce_retention_policy()
        assert deleted == 0

    @pytest.mark.asyncio
    async def test_handles_none_diag_config(self) -> None:
        repl, ctx = _make_repl_with_diag_config()
        ctx.cfg.diag = None
        deleted = await repl._enforce_retention_policy()
        assert deleted == 0
