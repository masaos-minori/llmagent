"""tests/test_memory_local_only.py
Unit tests for memory_local_only configuration passthrough:
- MemoryConfig has memory_local_only field (default False)
- _build_memory_config reads memory_local_only from config
- factory.py passes local_only to EmbeddingClientConfig
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestMemoryLocalOnlyConfig:
    def test_default_false(self) -> None:
        """memory_local_only defaults to False."""
        from agent.config_dataclasses import MemoryConfig

        cfg = MemoryConfig()
        assert cfg.memory_local_only is False

    def test_config_builder_reads_memory_local_only_true(self) -> None:
        """_build_memory_config reads memory_local_only=true from config."""
        from agent.config_builders import _build_memory_config

        cfg = _build_memory_config({"memory_local_only": True})
        assert cfg.memory_local_only is True

    def test_config_builder_reads_memory_local_only_false(self) -> None:
        """_build_memory_config reads memory_local_only=false from config."""
        from agent.config_builders import _build_memory_config

        cfg = _build_memory_config({"memory_local_only": False})
        assert cfg.memory_local_only is False

    def test_config_builder_default_false_when_missing(self) -> None:
        """_build_memory_config defaults to False when memory_local_only not in config."""
        from agent.config_builders import _build_memory_config

        cfg = _build_memory_config({})
        assert cfg.memory_local_only is False


class TestFactoryLocalOnlyPassthrough:
    def test_factory_passes_local_only_to_embedding_client(self) -> None:
        """factory.py passes memory_local_only to EmbeddingClientConfig."""
        from agent.factory import _build_embedding_client

        ctx = MagicMock()
        ctx.cfg.rag.embed_url = "http://localhost:8001/embed"
        ctx.cfg.memory.memory_embed_timeout_sec = 5.0
        ctx.cfg.memory.memory_embed_dim = 384
        ctx.cfg.memory.memory_local_only = True

        captured: list[object] = []

        class FakeConfig:
            def __init__(self, **kwargs: object) -> None:
                captured.append(kwargs)

        class FakeClient:
            def __init__(self, cfg: object, http: object, *, enabled: bool) -> None:
                pass

        _build_embedding_client(ctx, MagicMock(), FakeClient, FakeConfig)
        assert len(captured) == 1
        assert captured[0].get("local_only") is True  # type: ignore[attr-defined]

    def test_factory_passes_local_only_false(self) -> None:
        """factory.py passes memory_local_only=False when disabled."""
        from agent.factory import _build_embedding_client

        ctx = MagicMock()
        ctx.cfg.rag.embed_url = "http://localhost:8001/embed"
        ctx.cfg.memory.memory_embed_timeout_sec = 5.0
        ctx.cfg.memory.memory_embed_dim = 384
        ctx.cfg.memory.memory_local_only = False

        captured: list[object] = []

        class FakeConfig:
            def __init__(self, **kwargs: object) -> None:
                captured.append(kwargs)

        class FakeClient:
            def __init__(self, cfg: object, http: object, *, enabled: bool) -> None:
                pass

        _build_embedding_client(ctx, MagicMock(), FakeClient, FakeConfig)
        assert len(captured) == 1
        assert captured[0].get("local_only") is False  # type: ignore[attr-defined]

    def test_factory_default_false_when_not_set(self) -> None:
        """factory.py uses local_only=False when memory_local_only not set (explicit config)."""
        from agent.factory import _build_embedding_client

        ctx = MagicMock()
        ctx.cfg.rag.embed_url = "http://localhost:8001/embed"
        ctx.cfg.memory.memory_embed_timeout_sec = 5.0
        ctx.cfg.memory.memory_embed_dim = 384
        ctx.cfg.memory.memory_local_only = False  # explicitly set to False

        captured: list[object] = []

        class FakeConfig:
            def __init__(self, **kwargs: object) -> None:
                captured.append(kwargs)

        class FakeClient:
            def __init__(self, cfg: object, http: object, *, enabled: bool) -> None:
                pass

        _build_embedding_client(ctx, MagicMock(), FakeClient, FakeConfig)
        assert len(captured) == 1
        assert captured[0].get("local_only") is False  # type: ignore[attr-defined]


class TestLocalOnlyRejectsNonLocalUrl:
    def test_non_local_url_rejected_when_local_only_true(self) -> None:
        """EmbeddingClient rejects non-local URL when local_only=True."""
        from agent.memory.embedding_client import EmbeddingClient, EmbeddingClientConfig

        cfg = EmbeddingClientConfig(
            embed_url="http://external-api.com:8080/embed",
            local_only=True,
        )
        with pytest.raises(ValueError, match="memory_local_only=True"):
            EmbeddingClient(cfg, enabled=True)

    def test_localhost_url_allowed_when_local_only_true(self) -> None:
        """EmbeddingClient allows localhost URL when local_only=True."""
        from agent.memory.embedding_client import EmbeddingClient, EmbeddingClientConfig

        cfg = EmbeddingClientConfig(
            embed_url="http://localhost:8080/embed",
            local_only=True,
        )
        client = EmbeddingClient(cfg, enabled=True)
        assert client.get_status().local_only is True

    def test_127_url_allowed_when_local_only_true(self) -> None:
        """EmbeddingClient allows 127.0.0.1 URL when local_only=True."""
        from agent.memory.embedding_client import EmbeddingClient, EmbeddingClientConfig

        cfg = EmbeddingClientConfig(
            embed_url="http://127.0.0.1:8080/embed",
            local_only=True,
        )
        client = EmbeddingClient(cfg, enabled=True)
        assert client.get_status().local_only is True
