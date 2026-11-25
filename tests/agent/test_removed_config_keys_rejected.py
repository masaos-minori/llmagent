"""tests/agent/test_removed_config_keys_rejected.py

Regression coverage for REQ-009/AC-7: the Agent config-loading path rejects
removed SemanticCache-related keys (use_semantic_cache, semantic_cache_threshold,
semantic_cache_max_size) with the REQ-003 migration error, individually and in
combination.

AC-6 extends the same rejection to the reload path: the reload candidate is built
through `build_agent_config`, so a removed or moved key is rejected by both paths
before anything live is mutated.
"""

from __future__ import annotations

from typing import Any

import pytest
from agent.config_builders import build_agent_config
from agent.services.exceptions import ConfigReloadValidationError

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

REMOVED_KEYS = frozenset(
    ("use_semantic_cache", "semantic_cache_threshold", "semantic_cache_max_size")
)

# Keys the per-tool maps were replaced by the declared tool metadata (agentcfg003
# REQ-005); they are no longer read by any section builder, so they are unknown
# production keys rather than fields.
MOVED_MAP_KEYS = frozenset(("tool_safety_tiers", "approval_risk_rules"))

_REJECTED_VALUES: dict[str, Any] = {
    "use_semantic_cache": True,
    "semantic_cache_threshold": 0.5,
    "semantic_cache_max_size": 50,
    "tool_safety_tiers": {"read_text_file": "SUPERUSER"},
    "approval_risk_rules": {"write_file": "extreme"},
}

for _k in REMOVED_KEYS | MOVED_MAP_KEYS:
    _MIN_CFG_EQUIVALENT[_k] = _REJECTED_VALUES[_k]


@pytest.mark.parametrize(
    "key,value",
    [
        ("use_semantic_cache", True),
        ("semantic_cache_threshold", 0.5),
        ("semantic_cache_max_size", 50),
        ("tool_safety_tiers", {"read_text_file": "SUPERUSER"}),
        ("approval_risk_rules", {"write_file": "extreme"}),
    ],
)
def test_individual_removed_key_rejected(key: str, value: object) -> None:
    """Each individually-present removed key raises ValueError."""
    merged = {**_MIN_CFG_EQUIVALENT, key: value}
    with pytest.raises(ValueError, match=key):
        build_agent_config(merged)


def test_all_three_removed_keys_rejected() -> None:
    """All three removed keys together also raise ValueError."""
    merged = {**_MIN_CFG_EQUIVALENT}
    for k in REMOVED_KEYS:
        merged[k] = True  # type: ignore[literal-required] — literal-required false positive on dynamic dict assignment in loop
    with pytest.raises(ValueError):
        build_agent_config(merged)


@pytest.mark.parametrize(
    "key,value",
    [
        ("use_semantic_cache", True),
        ("semantic_cache_threshold", 0.5),
        ("semantic_cache_max_size", 50),
        ("tool_safety_tiers", {"read_text_file": "SUPERUSER"}),
        ("approval_risk_rules", {"write_file": "extreme"}),
    ],
)
def test_removed_key_rejected_by_reload_path(key: str, value: object) -> None:
    """AC-6: the reload candidate runs the same key check, so the reload path rejects
    the key the startup path rejects, and nothing live is mutated."""
    from agent.services.config_reload import ConfigReloadService

    from tests.agent._config_test_defaults import reload_fixture_ctx

    ctx = reload_fixture_ctx()
    live_cfg = ctx.cfg
    live_prompt = ctx.conv.system_prompt_content

    with pytest.raises(ConfigReloadValidationError, match=key):
        ConfigReloadService(ctx).apply_config_dict({key: value})

    assert ctx.cfg is live_cfg  # the candidate is a separate object, never installed
    assert ctx.conv.system_prompt_content == live_prompt
    assert not hasattr(ctx.cfg.approval, key)
    assert not hasattr(ctx.cfg.tool, key)
