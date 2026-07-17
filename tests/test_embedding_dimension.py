"""tests/test_embedding_dimension.py
Unit tests for embedding dimension consistency checks:
- factory.py passes memory_embed_dim to MemoryStore and EmbeddingClientConfig
- startup.py detects config mismatch between memory and db embedding_dims
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

# ── factory: embed_dim passthrough ───────────────────────────────────────────


class TestFactoryEmbedDimPassthrough:
    def test_memorystore_receives_embed_dim_from_config(self) -> None:
        """factory.py passes memory_embed_dim to MemoryStore()."""
        from agent.factory import _build_embedding_client

        ctx = MagicMock()
        ctx.cfg.rag.embed_url = "http://localhost:8080/embed"
        ctx.cfg.memory.memory_embed_timeout_sec = 5.0
        ctx.cfg.memory.memory_embed_dim = 512

        captured: list[object] = []

        class FakeConfig:
            def __init__(self, **kwargs: object) -> None:
                captured.append(kwargs)

        class FakeClient:
            def __init__(self, cfg: object, http: object, *, enabled: bool) -> None:
                pass

        _build_embedding_client(ctx, MagicMock(), FakeClient, FakeConfig)
        assert len(captured) == 1
        assert captured[0].get("embed_dim") == 512  # type: ignore[attr-defined]


# ── startup: dimension consistency check ─────────────────────────────────────


def _make_startup(memory_dim: int, db_dim: int) -> object:
    """Build an StartupOrchestrator-like object with _check_embedding_dimensions method."""
    from agent.startup import StartupOrchestrator

    ctx = MagicMock()
    ctx.cfg.memory.memory_embed_dim = memory_dim

    startup = object.__new__(StartupOrchestrator)
    startup._ctx = ctx

    with patch("db.config.build_db_config") as mock_build:
        mock_cfg = MagicMock()
        mock_cfg.embedding_dims = db_dim
        mock_build.return_value = mock_cfg
        startup._check_embedding_dimensions = lambda: (
            StartupOrchestrator._check_embedding_dimensions(startup)
        )

    return startup, mock_build


class TestStartupDimensionCheck:
    def test_matching_dims_logs_and_passes(self) -> None:
        """_check_embedding_dimensions does not raise when dims match."""
        from agent.startup import StartupOrchestrator

        ctx = MagicMock()
        ctx.cfg.memory.memory_embed_dim = 384

        startup = object.__new__(StartupOrchestrator)
        startup._ctx = ctx

        with patch("db.config.build_db_config") as mock_build:
            mock_cfg = MagicMock()
            mock_cfg.embedding_dims = 384
            mock_build.return_value = mock_cfg
            startup._check_embedding_dimensions()  # should not raise

    def test_mismatched_dims_raises_runtime_error(self) -> None:
        """_check_embedding_dimensions raises RuntimeError on dim mismatch."""
        from agent.startup import StartupOrchestrator

        ctx = MagicMock()
        ctx.cfg.memory.memory_embed_dim = 512

        startup = object.__new__(StartupOrchestrator)
        startup._ctx = ctx

        with patch("db.config.build_db_config") as mock_build:
            mock_cfg = MagicMock()
            mock_cfg.embedding_dims = 384
            mock_build.return_value = mock_cfg
            with pytest.raises(RuntimeError, match="Embedding dimension mismatch"):
                startup._check_embedding_dimensions()
