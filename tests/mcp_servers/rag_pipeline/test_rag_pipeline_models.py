"""tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py

Characterization tests for RagPipelineConfig.from_dict / .load(), the two
code paths in rag_pipeline_models.py not exercised by
test_rag_pipeline_mcp_service.py (which only constructs RagPipelineConfig
directly via its dataclass __init__, never through from_dict/load).
"""

from __future__ import annotations

from typing import Any

import pytest
from mcp_servers.rag_pipeline.rag_pipeline_models import RagPipelineConfig
from shared.config_loader import ConfigLoader


class TestRagPipelineConfigFromDict:
    def test_defaults_when_dict_empty(self) -> None:
        cfg = RagPipelineConfig.from_dict({})
        assert cfg == RagPipelineConfig()

    def test_defaults_match_operational_toml(self) -> None:
        # Source of truth: config/rag_pipeline_mcp_server.toml's operational values.
        # A future edit to either side without the other must fail this test.
        cfg = RagPipelineConfig()
        assert cfg.top_k_search == 20
        assert cfg.top_k_rerank == 15
        assert cfg.rag_min_score == 2.0
        assert cfg.semantic_cache_max_size == 100
        assert cfg.refiner_max_chars_per_chunk == 300

    def test_custom_values_are_mapped(self) -> None:
        raw: dict[str, Any] = {
            "llm_url": "http://llm.example",
            "embed_url": "http://embed.example",
            "rag_db_path": "/tmp/rag.sqlite",
            "sqlite_vec_so": "/tmp/vec0.so",
            "sqlite_timeout": 15,
            "sqlite_busy_timeout_ms": 5000,
            "mqe_n_queries": 7,
            "mqe_prompt_template": "mqe {query}",
            "rerank_prompt_template": "rerank {query}",
            "use_mqe": False,
            "use_rrf": False,
            "rrf_k": 30,
            "use_rerank": False,
            "use_refiner": True,
            "top_k_search": 8,
            "top_k_rerank": 16,
            "rag_top_k": 4,
            "rag_min_score": 0.5,
            "max_chunks_per_doc": 2,
            "semantic_cache_max_size": 64,
            "semantic_cache_threshold": 0.8,
            "use_semantic_cache": True,
            "refiner_max_tokens": 128,
            "refiner_max_chars_per_chunk": 400,
            "refiner_timeout": 12.5,
            "rag_auth_token": "secret-token",
        }
        cfg = RagPipelineConfig.from_dict(raw)
        assert cfg.llm_url == "http://llm.example"
        assert cfg.embed_url == "http://embed.example"
        assert cfg.rag_db_path == "/tmp/rag.sqlite"
        assert cfg.sqlite_vec_so == "/tmp/vec0.so"
        assert cfg.sqlite_timeout == 15
        assert cfg.sqlite_busy_timeout_ms == 5000
        assert cfg.mqe_n_queries == 7
        assert cfg.mqe_prompt_template == "mqe {query}"
        assert cfg.rerank_prompt_template == "rerank {query}"
        assert cfg.use_mqe is False
        assert cfg.use_rrf is False
        assert cfg.rrf_k == 30
        assert cfg.use_rerank is False
        assert cfg.use_refiner is True
        assert cfg.top_k_search == 8
        assert cfg.top_k_rerank == 16
        assert cfg.rag_top_k == 4
        assert cfg.rag_min_score == 0.5
        assert cfg.max_chunks_per_doc == 2
        assert cfg.semantic_cache_max_size == 64
        assert cfg.semantic_cache_threshold == 0.8
        assert cfg.use_semantic_cache is True
        assert cfg.refiner_max_tokens == 128
        assert cfg.refiner_max_chars_per_chunk == 400
        assert cfg.refiner_timeout == 12.5
        assert cfg.rag_auth_token == "secret-token"

    def test_numeric_string_values_are_coerced(self) -> None:
        """from_dict wraps numeric fields in int()/float(); TOML round-trips
        or manually-built dicts may hand it stringly-typed numbers."""
        cfg = RagPipelineConfig.from_dict(
            {
                "sqlite_timeout": "45",
                "rrf_k": "90",
                "rag_min_score": "1.5",
                "refiner_timeout": "20.0",
            }
        )
        assert cfg.sqlite_timeout == 45
        assert cfg.rrf_k == 90
        assert cfg.rag_min_score == 1.5
        assert cfg.refiner_timeout == 20.0

    def test_falsy_present_values_are_not_treated_as_missing(self) -> None:
        """d.get(key, default) only falls back on a missing key, not a falsy
        one -- explicit 0/""/False values must survive, not silently revert
        to the dataclass default."""
        cfg = RagPipelineConfig.from_dict(
            {
                "sqlite_timeout": 0,
                "use_mqe": False,
                "rag_auth_token": "",
                "rag_min_score": 0,
            }
        )
        assert cfg.sqlite_timeout == 0
        assert cfg.use_mqe is False
        assert cfg.rag_auth_token == ""
        assert cfg.rag_min_score == 0.0

    def test_unknown_keys_are_ignored(self) -> None:
        cfg = RagPipelineConfig.from_dict({"not_a_real_field": "x", "llm_url": "u"})
        assert cfg.llm_url == "u"
        assert not hasattr(cfg, "not_a_real_field")


class TestRagPipelineConfigLoad:
    def test_load_delegates_to_config_loader_with_expected_filename(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured: dict[str, Any] = {}

        def fake_load(self: ConfigLoader, *names: str) -> dict[str, Any]:
            captured["names"] = names
            return {"llm_url": "http://from-toml", "top_k_search": 9}

        monkeypatch.setattr(ConfigLoader, "load", fake_load)

        cfg = RagPipelineConfig.load()

        assert captured["names"] == ("rag_pipeline_mcp_server.toml",)
        assert cfg.llm_url == "http://from-toml"
        assert cfg.top_k_search == 9
        # Fields absent from the fake TOML payload fall back to dataclass defaults.
        assert cfg.use_mqe is True

    def test_load_propagates_config_loader_errors(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """load() is documented as fail-fast: it must not swallow errors
        raised by ConfigLoader (e.g. missing/malformed TOML file)."""

        def raising_load(self: ConfigLoader, *names: str) -> dict[str, Any]:
            raise ValueError("boom")

        monkeypatch.setattr(ConfigLoader, "load", raising_load)

        with pytest.raises(ValueError, match="boom"):
            RagPipelineConfig.load()
