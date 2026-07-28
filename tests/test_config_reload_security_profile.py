"""
tests/test_config_reload_security_profile.py

Characterization test for security_profile fallback in config_reload.
"""

from __future__ import annotations

from typing import Any

import pytest
from agent.config_dataclasses import AgentConfig
from agent.services.config_reload import apply_config_changes


def _make_ctx(**overrides: Any) -> Any:
    """Create a minimal context object with required attributes."""
    defaults: dict[str, Any] = {
        "context_char_limit": 8000,
        "context_compress_turns": 4,
        "tool_cache_ttl": 300,
        "top_k_search": 20,
        "top_k_rerank": 15,
        "rag_top_k": 5,
        "use_mqe": True,
        "use_search": True,
        "use_rrf": True,
        "use_rerank": True,
        "llm_max_retries": 3,
        "llm_retry_base_delay": 1.0,
        "rag_min_score": 0.0,
        "max_chunks_per_doc": 2,
        "use_two_stage_fetch": False,
        "two_stage_max_docs": 2,
        "serial_tool_calls": False,
        "use_semantic_cache": False,
        "semantic_cache_threshold": 0.92,
        "tool_result_max_llm_chars": 4000,
        "masked_fields": [],
        "allowed_tools": [],
        "tool_definitions": [],
        "tool_safety_tiers": {},
        "approval_risk_rules": {},
        "approval_shell_safe_prefixes": ["/bin/", "/usr/bin/"],
        "approval_github_allowed_repos": [],
        "allowed_root": "",
        "security_profile": "development",
        "security_lockdown_enabled": False,
        "memory_local_only": False,
    }
    merged = {**defaults, **overrides}
    cfg = AgentConfig(**merged)
    ctx = type("MockContext", (), {"cfg": cfg})()
    return ctx


class TestInvalidSecurityProfileIgnored:
    """Test invalid security_profile value is silently ignored during config reload."""

    @pytest.mark.asyncio
    async def test_invalid_security_profile_preserves_current_value(self) -> None:
        """Invalid security_profile value should preserve the current value."""
        ctx = _make_ctx(security_profile="production")
        original_value = ctx.cfg.mcp.security_profile
        assert original_value == "production"

        new_cfg = {"security_profile": "INVALID_VALUE"}
        await apply_config_changes(ctx, new_cfg)

        assert ctx.cfg.mcp.security_profile == original_value

    @pytest.mark.asyncio
    async def test_empty_string_security_profile_preserves_current_value(self) -> None:
        """Empty string security_profile should preserve the current value."""
        ctx = _make_ctx(security_profile="development")
        original_value = ctx.cfg.mcp.security_profile
        assert original_value == "development"

        new_cfg = {"security_profile": ""}
        await apply_config_changes(ctx, new_cfg)

        assert ctx.cfg.mcp.security_profile == original_value

    @pytest.mark.asyncio
    async def test_numeric_security_profile_preserves_current_value(self) -> None:
        """Numeric string security_profile should preserve the current value."""
        ctx = _make_ctx(security_profile="staging")
        original_value = ctx.cfg.mcp.security_profile
        assert original_value == "staging"

        new_cfg = {"security_profile": "123"}
        await apply_config_changes(ctx, new_cfg)

        assert ctx.cfg.mcp.security_profile == original_value

    @pytest.mark.asyncio
    async def test_valid_security_profile_applied(self) -> None:
        """Valid security_profile should be applied successfully."""
        ctx = _make_ctx(security_profile="development")
        original_value = ctx.cfg.mcp.security_profile
        assert original_value == "development"

        new_cfg = {"security_profile": "production"}
        await apply_config_changes(ctx, new_cfg)

        assert ctx.cfg.mcp.security_profile == "production"
