"""tests/test_memory_status.py
Tests for /memory status command and supporting infrastructure:
  - EmbeddingClient.get_status()
  - HybridRetriever.last_retrieval_mode and embed_client
  - _MemoryMixin._memory_status()
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest
from agent.memory.embedding_client import (
    EmbeddingClient,
    EmbeddingClientConfig,
    EmbeddingClientStatus,
)
from agent.memory.retriever import HybridRetriever

# ── EmbeddingClient.get_status() ─────────────────────────────────────────────


@pytest.fixture()
def config() -> EmbeddingClientConfig:
    return EmbeddingClientConfig(
        embed_url="http://localhost:8080/embed",
        circuit_open_after=3,
        circuit_reset_sec=60.0,
        embed_dim=0,
    )


class TestGetStatus:
    def test_disabled_client(self, config: EmbeddingClientConfig) -> None:
        client = EmbeddingClient(config, enabled=False)
        status = client.get_status()
        assert isinstance(status, EmbeddingClientStatus)
        assert status.enabled is False
        assert status.circuit_open is False
        assert status.fail_count == 0
        assert status.resets_in_sec is None

    def test_enabled_closed_circuit(self, config: EmbeddingClientConfig) -> None:
        client = EmbeddingClient(config, enabled=True)
        status = client.get_status()
        assert status.enabled is True
        assert status.circuit_open is False
        assert status.resets_in_sec is None

    def test_circuit_open_shows_resets_in_sec(
        self, config: EmbeddingClientConfig
    ) -> None:
        client = EmbeddingClient(config, enabled=True)
        # Force circuit open
        client._fail_count = config.circuit_open_after
        client._circuit_opened_at = time.monotonic()
        status = client.get_status()
        assert status.circuit_open is True
        assert status.resets_in_sec is not None
        assert 0.0 < status.resets_in_sec <= config.circuit_reset_sec

    def test_circuit_open_fail_count_preserved(
        self, config: EmbeddingClientConfig
    ) -> None:
        client = EmbeddingClient(config, enabled=True)
        client._fail_count = 5
        client._circuit_opened_at = time.monotonic()
        status = client.get_status()
        assert status.fail_count == 5

    def test_auto_reset_when_elapsed(self) -> None:
        cfg = EmbeddingClientConfig(
            embed_url="http://localhost:8080/embed",
            circuit_open_after=3,
            circuit_reset_sec=0.001,
            embed_dim=0,
        )
        client = EmbeddingClient(cfg, enabled=True)
        client._fail_count = cfg.circuit_open_after
        client._circuit_opened_at = time.monotonic() - 1.0  # way past reset
        status = client.get_status()
        # Circuit auto-reset
        assert status.circuit_open is False
        assert status.resets_in_sec is None


# ── HybridRetriever attributes ────────────────────────────────────────────────


class TestHybridRetrieverAttributes:
    def test_embed_client_stored(self, config: EmbeddingClientConfig) -> None:
        ec = EmbeddingClient(config, enabled=False)
        ret = HybridRetriever(embed_client=ec)
        assert ret.embed_client is ec

    def test_embed_client_defaults_to_none(self) -> None:
        ret = HybridRetriever()
        assert ret.embed_client is None

    def test_last_retrieval_mode_defaults_to_unknown(self) -> None:
        ret = HybridRetriever()
        assert ret.last_retrieval_mode == "unknown"


# ── /memory status command ────────────────────────────────────────────────────


def _make_mixin() -> object:
    from agent.commands.cmd_memory import _MemoryMixin
    from agent.commands.output_port import CliOutputPort

    mixin = _MemoryMixin.__new__(_MemoryMixin)
    mixin._out = MagicMock(spec=CliOutputPort)
    mixin._ctx = MagicMock()
    mixin._ctx.services_required.audit_logger = None
    return mixin


class TestCmdMemoryStatus:
    def test_memory_disabled_writes_disabled_message(self) -> None:
        mixin = _make_mixin()
        mixin._memory_status(None)
        mixin._out.write.assert_called_once()
        msg = mixin._out.write.call_args[0][0]
        assert "disabled" in msg

    def test_memory_enabled_writes_table(self, config: EmbeddingClientConfig) -> None:
        ec = EmbeddingClient(config, enabled=True)
        mem = MagicMock()
        mem.retriever.embed_client = ec
        mem.retriever.last_retrieval_mode = "fts_only"
        mixin = _make_mixin()
        mixin._memory_status(mem)
        mixin._out.write_table.assert_called_once()
        args = mixin._out.write_table.call_args[0]
        rows = args[1]
        enabled_row = next(r for r in rows if r[0] == "Embedding enabled")
        assert enabled_row[1] == "Yes"

    def test_circuit_open_shown_in_status(self, config: EmbeddingClientConfig) -> None:
        ec = EmbeddingClient(config, enabled=True)
        ec._fail_count = config.circuit_open_after
        ec._circuit_opened_at = time.monotonic()
        mem = MagicMock()
        mem.retriever.embed_client = ec
        mem.retriever.last_retrieval_mode = "fts_only"
        mixin = _make_mixin()
        mixin._memory_status(mem)
        args = mixin._out.write_table.call_args[0]
        rows = args[1]
        circuit_row = next(r for r in rows if r[0] == "Circuit")
        assert "OPEN" in circuit_row[1]

    def test_no_embed_client_writes_message(self) -> None:
        mem = MagicMock()
        mem.retriever.embed_client = None
        mixin = _make_mixin()
        mixin._memory_status(mem)
        mixin._out.write.assert_called_once()
        msg = mixin._out.write.call_args[0][0]
        assert "embed_client" in msg

    def test_last_retrieval_mode_shown(self, config: EmbeddingClientConfig) -> None:
        ec = EmbeddingClient(config, enabled=True)
        mem = MagicMock()
        mem.retriever.embed_client = ec
        mem.retriever.last_retrieval_mode = "hybrid"
        mixin = _make_mixin()
        mixin._memory_status(mem)
        args = mixin._out.write_table.call_args[0]
        rows = args[1]
        mode_row = next(r for r in rows if r[0] == "Last retrieval mode")
        assert mode_row[1] == "hybrid"


# ── build_status_table mode labels ─────────────────────────────────────────────


class TestBuildStatusTableModeLabels:
    def test_memory_layer_disabled_label(self) -> None:
        from agent.commands.memory_status import MemoryStatus, build_status_table

        status = MemoryStatus(memory_layer_enabled=False)
        rows = build_status_table(status)
        mode_row = next(r for r in rows if r[0] == "Mode")
        assert mode_row[1] == "Memory layer disabled"

    def test_hybrid_mode_label(self, config: EmbeddingClientConfig) -> None:
        from agent.commands.memory_status import MemoryStatus, build_status_table

        status = MemoryStatus(
            memory_layer_enabled=True,
            embedding_enabled=True,
            circuit_open=False,
        )
        rows = build_status_table(status)
        mode_row = next(r for r in rows if r[0] == "Mode")
        assert mode_row[1] == "Hybrid mode (semantic + FTS)"

    def test_degraded_mode_label(self, config: EmbeddingClientConfig) -> None:
        from agent.commands.memory_status import MemoryStatus, build_status_table

        ec = EmbeddingClient(config, enabled=True)
        ec._fail_count = config.circuit_open_after
        ec._circuit_opened_at = time.monotonic()
        status = MemoryStatus(
            memory_layer_enabled=True,
            embedding_enabled=True,
            circuit_open=True,
        )
        rows = build_status_table(status)
        mode_row = next(r for r in rows if r[0] == "Mode")
        assert mode_row[1] == "Degraded mode (circuit open, FTS fallback)"

    def test_fts_only_label(self, config: EmbeddingClientConfig) -> None:
        from agent.commands.memory_status import MemoryStatus, build_status_table

        status = MemoryStatus(
            memory_layer_enabled=True,
            embedding_enabled=False,
            circuit_open=False,
        )
        rows = build_status_table(status)
        mode_row = next(r for r in rows if r[0] == "Mode")
        assert mode_row[1] == "Memory enabled, embedding disabled (FTS-only)"
