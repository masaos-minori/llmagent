"""tests/mcp_servers/rag_pipeline/test_rag_pipeline_removed_config_keys_rejected.py

Regression coverage for REQ-009/AC-7: the RAG MCP config-loading path rejects
removed SemanticCache-related keys (use_semantic_cache, semantic_cache_threshold,
semantic_cache_max_size) with the REQ-003 migration error, individually and in
combination.
"""

from __future__ import annotations

from typing import Any

import pytest
from mcp_servers.rag_pipeline.rag_pipeline_models import RagPipelineConfig
from shared.config_loader import ConfigLoader

REMOVED_KEYS = frozenset(("use_semantic_cache", "semantic_cache_threshold", "semantic_cache_max_size"))

@pytest.mark.parametrize(
    "key,value",
    [
        ("use_semantic_cache", True),
        ("semantic_cache_threshold", 0.5),
        ("semantic_cache_max_size", 50),
    ],
)
def test_individual_removed_key_rejected(key: str, value: object, monkeypatch: pytest.MonkeyPatch) -> None:
    """Each individually-present removed key raises ValueError."""
    def fake_load(self: ConfigLoader, *names: str) -> dict[str, Any]:
        return {"llm_url": "http://x", key: value}

    monkeypatch.setattr(ConfigLoader, "load", fake_load)
    with pytest.raises(ValueError, match=key):
        RagPipelineConfig.load()

def test_all_three_removed_keys_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """All three removed keys together also raise ValueError."""
    payload: dict[str, Any] = {"llm_url": "http://x"}
    for k in REMOVED_KEYS:
        payload[k] = True  # type: ignore[literal-required]

    def fake_load(self: ConfigLoader, *names: str) -> dict[str, Any]:
        return payload

    monkeypatch.setattr(ConfigLoader, "load", fake_load)
    with pytest.raises(ValueError):
        RagPipelineConfig.load()
