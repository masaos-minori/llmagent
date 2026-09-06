"""tests/agent/test_removed_config_keys_rejected.py

Regression coverage for REQ-009/AC-7: the Agent config-loading path rejects
removed SemanticCache-related keys (use_semantic_cache, semantic_cache_threshold,
semantic_cache_max_size) with the REQ-003 migration error, individually and in
combination.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from agent.config_builders import build_agent_config

# Minimal config satisfying _build_mcp_servers (needs at least one HTTP server
# with url) and AgentConfig.__post_init__'s memory_embed_enabled cross-field
# check (now defaults to True, so embed_url must be non-empty).
_MIN_CFG_EQUIVALENT: dict = {
    "mcp_servers": {
        "test-server": {
            "transport": "http",
            "url": "http://127.0.0.1:9999",
            "auth_token": "test-token",
        }
    },
    "embed_url": "http://127.0.0.1:9999",
}

REMOVED_KEYS = frozenset(("use_semantic_cache", "semantic_cache_threshold", "semantic_cache_max_size"))

for _k in REMOVED_KEYS:
    _MIN_CFG_EQUIVALENT[_k] = True  # type: ignore[literal-required]

@pytest.mark.parametrize(
    "key,value",
    [
        ("use_semantic_cache", True),
        ("semantic_cache_threshold", 0.5),
        ("semantic_cache_max_size", 50),
    ],
)
def test_individual_removed_key_rejected(key: str, value: object) -> None:
    """Each individually-present removed key raises ValueError."""
    merged = {**_MIN_CFG_EQUIVALENT, key: value}
    with patch("agent.config_builders.sys.exit"):
        with pytest.raises(ValueError, match=key):
            build_agent_config(merged)

def test_all_three_removed_keys_rejected() -> None:
    """All three removed keys together also raise ValueError."""
    merged = {**_MIN_CFG_EQUIVALENT}
    for k in REMOVED_KEYS:
        merged[k] = True  # type: ignore[literal-required]
    with patch("agent.config_builders.sys.exit"):
        with pytest.raises(ValueError):
            build_agent_config(merged)
