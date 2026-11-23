"""tests/agent/test_safety_tier_single_source.py

ADR-003 INV-03: routing, approval, and auditing read the Safety Tier from the same
RuntimeTool declaration. One tool is registered per declared tier; every consumer must
agree with that declaration, and moving the declaration must move every consumer.
"""

from __future__ import annotations

import json
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.config_builders import build_agent_config
from agent.config_dataclasses import AgentConfig
from agent.tool_approval import run_approval_checks
from agent.tool_enums import RiskLevel
from agent.tool_policy import classify_risk, is_plan_mode_blocked
from agent.tool_preparation import PreparedToolCall, _canonical_args_hash
from shared.route_resolver import ToolRouteResolver
from shared.runtime_tool import AgentSafetyTier, build_runtime_tool
from shared.runtime_tool_registry import RuntimeToolRegistry
from shared.tool_spec import ToolSpec
from shared.transport_dto import ToolExecutionContext

from tests.agent._config_test_defaults import (
    PERMISSIVE_ALLOWED_ROOT,
    PERMISSIVE_SQLITE_VEC_SO,
    SHIPPED_DB_PATH_KEYS,
)

SERVER_KEY = "test_server"

# tier -> tool name. The expectation is written here, not read from tool_policy, so a
# consumer that consults a second source is caught.
_TOOLS: dict[str, str] = {
    "READ_ONLY": "t_read_only",
    "WRITE_SAFE": "t_write_safe",
    "WRITE_DANGEROUS": "t_write_dangerous",
    "ADMIN": "t_admin",
}
_EXPECTED_RISK: dict[str, RiskLevel] = {
    "READ_ONLY": RiskLevel.NONE,
    "WRITE_SAFE": RiskLevel.NONE,
    "WRITE_DANGEROUS": RiskLevel.MEDIUM,
    "ADMIN": RiskLevel.HIGH,
}


def _tool(name: str, tier: str) -> Any:
    """Build one RuntimeTool with the full execution-metadata field set."""
    return build_runtime_tool(
        name=name,
        server_key=SERVER_KEY,
        is_write=tier != "READ_ONLY",
        requires_serial=False,
        resource_scope_kind="",
        resource_scope_keys={},
        agent_safety_tier=cast(AgentSafetyTier, tier),
        side_effect_class="read_only" if tier == "READ_ONLY" else "local_write",
        retry_policy="safe_read_retry",
        reconciliation_policy="not_required",
        idempotency_required=False,
        preview_capability="none",
        policy_version="2.1",
    )


def _registry(tier: str) -> RuntimeToolRegistry:
    name = _TOOLS[tier]
    return RuntimeToolRegistry(
        tools={name: _tool(name, tier)}, allowed_servers=frozenset({SERVER_KEY})
    )


def _make_cfg(tier: str) -> AgentConfig:
    """Build a minimal AgentConfig with test-safe defaults for the registered tool."""
    return build_agent_config(
        {
            "allowed_tools": [_TOOLS[tier]],
            "context_char_limit": 8000,
            "context_compress_turns": 4,
            "llm_retry_base_delay": 1.0,
            "masked_fields": [],
            "plan_blocked_tools": [],
            "llm_temperature": 0.2,
            "llm_max_tokens": 1024,
            "tool_dedup_max_repeats": 3,
            "tool_cycle_detect_window": 2,
            "tool_error_max_consecutive": 3,
            "memory_embed_url": "http://127.0.0.1:9999",
            **SHIPPED_DB_PATH_KEYS,
            "mcp_servers": {
                SERVER_KEY: {
                    "transport": "http",
                    "url": "http://127.0.0.1:9999",
                    "auth_token": "test-token",
                }
            },
            "allowed_root": PERMISSIVE_ALLOWED_ROOT,
            "sqlite_vec_so": PERMISSIVE_SQLITE_VEC_SO,
        }
    )


def _make_ctx(tier: str) -> MagicMock:
    """Build a minimal AgentContext mock wired to the tier's registry."""
    ctx = MagicMock()
    ctx.cfg = _make_cfg(tier)
    ctx.turn.current_turn_id = "test-turn-id"
    ctx.workflow.workflow_id = "wf-test-id"
    ctx.session.session_id = None
    ctx.conv.plan_mode = False
    ctx.services_required.audit_logger = MagicMock()
    ctx.services_required.tools = MagicMock()
    ctx.services_required.runtime_tools = _registry(tier)
    return ctx


def _prepared_call(tier: str) -> PreparedToolCall:
    name = _TOOLS[tier]
    args: dict[str, Any] = {}
    return PreparedToolCall(
        call_id="call_1",
        name=name,
        args=args,
        spec=ToolSpec(call_id="call_1", name=name, args=args),
        original_call={"id": "call_1", "function": {"name": name, "arguments": "{}"}},
        context=ToolExecutionContext(
            call_id="call_1",
            tool=name,
            args_hash=_canonical_args_hash(args),
            operation="call_tool",
        ),
    )


class TestSafetyTierSingleSource:
    """Each consumer reports the tier as declared, with no second source."""

    @pytest.mark.parametrize("tier", sorted(_EXPECTED_RISK))
    def test_consumers_agree_with_the_declaration(self, tier: str) -> None:
        registry = _registry(tier)
        name = _TOOLS[tier]
        declared = registry.get(name)

        # Routing: the resolver answers from the same RuntimeTool instance.
        resolver = ToolRouteResolver(runtime_registry=registry)
        assert resolver.resolve(name) == SERVER_KEY
        assert registry.get(name) is declared
        assert declared.agent_safety_tier == tier

        # Approval and plan mode read the declared tier.
        cfg = _make_cfg(tier)
        assert classify_risk(cfg, name, {}, registry) == _EXPECTED_RISK[tier]
        assert is_plan_mode_blocked(cfg, name, registry) == (tier != "READ_ONLY")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("tier", sorted(_EXPECTED_RISK))
    async def test_audit_event_carries_the_declared_tier(self, tier: str) -> None:
        ctx = _make_ctx(tier)
        # HIGH requires the full word "yes"; a lower risk accepts "y".
        answer = "yes" if _EXPECTED_RISK[tier] == RiskLevel.HIGH else "y"
        with patch(
            "agent.tool_approval._approval_read", new=AsyncMock(return_value=answer)
        ):
            approved, denied = await run_approval_checks(ctx, [_prepared_call(tier)])
        assert denied == []
        assert len(approved) == 1
        event: dict[str, Any] = json.loads(
            ctx.services_required.audit_logger.info.call_args[0][0]
        )
        assert event["event"] == "tool_approval"
        assert event["risk"] == _EXPECTED_RISK[tier].value

    def test_flipping_the_declaration_moves_every_consumer(self) -> None:
        """The same tool name under a different declared tier moves every consumer, so
        no consumer holds its own copy of the tier."""
        name = _TOOLS["WRITE_DANGEROUS"]
        before = _registry("WRITE_DANGEROUS")
        after = RuntimeToolRegistry(
            tools={name: _tool(name, "READ_ONLY")},
            allowed_servers=frozenset({SERVER_KEY}),
        )

        cfg = _make_cfg("WRITE_DANGEROUS")
        assert classify_risk(cfg, name, {}, before) == RiskLevel.MEDIUM
        assert is_plan_mode_blocked(cfg, name, before) is True

        assert classify_risk(cfg, name, {}, after) == RiskLevel.NONE
        assert is_plan_mode_blocked(cfg, name, after) is False
        resolver = ToolRouteResolver(runtime_registry=after)
        assert resolver.resolve(name) == SERVER_KEY
        assert after.get(name).agent_safety_tier == "READ_ONLY"
