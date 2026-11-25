"""
tests/test_tool_approval_paths.py
Unit tests for the allowed_root pre-flight check in check_approval().

Covers path-based root jail detection before risk classification.
"""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.config_builders import build_agent_config
from agent.config_dataclasses import AgentConfig
from agent.tool_approval import (
    _GRANT_TTL_SECONDS,
    check_approval,
    run_approval_checks,
)
from agent.tool_enums import ApprovalDecisionType
from agent.tool_preparation import PreparedToolCall, _canonical_args_hash
from shared.runtime_tool import AgentSafetyTier
from shared.runtime_tool_registry import RuntimeTool, RuntimeToolRegistry
from shared.tool_metadata import (
    TOOL_FIELD_SET_VERSION,
    PreviewCapability,
    ResourceKeyKind,
    SideEffectClass,
)
from shared.tool_spec import ToolSpec
from shared.transport_dto import ToolCallResult, ToolExecutionContext

from tests.agent._config_test_defaults import (
    ALL_TOOL_NAMES,
    PERMISSIVE_ALLOWED_ROOT,
    PERMISSIVE_SQLITE_VEC_SO,
    SHIPPED_APPROVAL_PROTECTED_PATHS,
    SHIPPED_DB_PATH_KEYS,
)
from tests.agent._producer_registry import PRODUCER_TIERS

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_cfg(**overrides: Any) -> AgentConfig:
    """Build a minimal AgentConfig with test-safe defaults."""
    base = build_agent_config(
        {
            "allowed_tools": ALL_TOOL_NAMES,
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
            # memory_embed_enabled now defaults to True; memory_embed_url must be non-empty
            # to satisfy MemoryConfig.__post_init__'s cross-field validation.
            "memory_embed_url": "http://127.0.0.1:9999",
            # build_agent_config() resolves the typed DB configuration from the mapping, so the fixture supplies the mirrored path keys.
            **SHIPPED_DB_PATH_KEYS,
            "mcp_servers": {
                "dummy": {
                    "transport": "http",
                    "url": "http://127.0.0.1:9999",
                    "auth_token": "test-token",
                }
            },
            # Standard tier classification; mirrors config/agent.toml defaults
            "allowed_root": PERMISSIVE_ALLOWED_ROOT,
            "sqlite_vec_so": PERMISSIVE_SQLITE_VEC_SO,
            **overrides,
        }
    )
    return base


# Declared metadata mirroring the producers' registration (agentcfg003 REQ-008):
# name -> (resource_scope_keys, preview_capability). Tiers come from the
# producer-declared tier map (PRODUCER_TIERS).
_DECLARED: dict[str, tuple[dict[str, ResourceKeyKind], str]] = {
    "write_file": ({"path": "path"}, "dry_run"),
    "edit_file": ({"path": "path"}, "dry_run"),
    "move_file": ({"source": "path", "destination": "path"}, "dry_run"),
    "delete_file": ({"path": "path"}, "dry_run"),
}


def _make_reg() -> RuntimeToolRegistry:
    """RuntimeToolRegistry seeded with the tools used in this file."""
    return RuntimeToolRegistry(
        tools={
            name: RuntimeTool(
                name=name,
                server_key="file_server",
                server_url="",
                description="",
                input_schema={},
                raw_definition={},
                status="active",
                is_write=True,
                requires_serial=False,
                resource_scope_kind="filesystem",
                resource_scope_keys=keys,
                agent_safety_tier=cast(AgentSafetyTier, PRODUCER_TIERS[name]),
                side_effect_class=cast(SideEffectClass, "local_write"),
                retry_policy="same_logical_call_only",
                reconciliation_policy="local_state",
                idempotency_required=True,
                preview_capability=cast(PreviewCapability, preview),
                policy_version=TOOL_FIELD_SET_VERSION,
                enabled_for_llm=True,
                capabilities=(),
            )
            for name, (keys, preview) in _DECLARED.items()
        },
        allowed_servers=frozenset({"file_server"}),
    )


def _make_ctx(cfg: AgentConfig | None = None) -> MagicMock:
    """Build a minimal AgentContext mock."""
    ctx = MagicMock()
    ctx.cfg = cfg or _make_cfg()
    ctx.turn.current_turn_id = "test-turn-id"
    ctx.workflow.workflow_id = "wf-test-id"
    ctx.workflow.current_task_id = "test-task-id"
    ctx.session.session_id = None
    ctx.services_required.audit_logger = None
    ctx.services_required.tools = AsyncMock()
    ctx.services_required.runtime_tools = _make_reg()
    return ctx


# ── check_approval(): ALLOWED_ROOT pre-flight ─────────────────────────────────


class TestCheckApprovalAllowedRoot:
    @pytest.mark.asyncio
    async def test_path_outside_root_immediately_denied(self, tmp_path: Any) -> None:
        import tempfile

        root = tempfile.mkdtemp()
        cfg = _make_cfg(allowed_root=root)
        ctx = _make_ctx(cfg=cfg)
        audit = MagicMock()
        ctx.services_required.audit_logger = audit
        ctx.services_required.tools = MagicMock()
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="Dry-run: /etc/passwd [would write]",
                is_error=False,
                request_id="",
                server_key="",
            )
        )

        result = await check_approval(ctx, "write_file", {"path": "/etc/passwd"})

        assert result is False
        logged = audit.info.call_args[0][0]
        assert "denied_root_jail" in logged

    @pytest.mark.asyncio
    async def test_path_inside_root_proceeds_to_risk_check(self, tmp_path: Any) -> None:
        import tempfile

        root = tempfile.mkdtemp()
        cfg = _make_cfg(allowed_root=root)
        ctx = _make_ctx(cfg=cfg)
        ctx.services_required.tools = MagicMock()
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output=f"Dry-run: {root}/file.txt [would write]",
                is_error=False,
                request_id="",
                server_key="",
            )
        )

        with patch(
            "agent.tool_approval._approval_read", new=AsyncMock(return_value="y")
        ):
            result = await check_approval(
                ctx, "write_file", {"path": f"{root}/file.txt"}
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_empty_allowed_root_denies_path_arguments(
        self, tmp_path: Any
    ) -> None:
        # REQ-003: an empty allowed_root (e.g. produced by a /reload) denies
        # path-bearing calls instead of disabling the jail.
        # Use tmp_path (not /etc) to avoid triggering approval_protected_paths escalation
        outside = str(tmp_path / "outside.txt")
        cfg = _make_cfg(approval_protected_paths=[])
        cfg.approval.allowed_root = ""
        ctx = _make_ctx(cfg=cfg)
        audit = MagicMock()
        ctx.services_required.audit_logger = audit

        result = await check_approval(ctx, "write_file", {"path": outside})

        assert result is False
        logged = audit.info.call_args[0][0]
        assert "denied_root_jail" in logged


# ── Protected-path escalation (DT-06 Option A pin, Plan row 14) ──────────────


class TestProtectedPathEscalation:
    """Pin that a declared path-bearing WRITE_DANGEROUS tool on a shipped
    protected path inside allowed_root resolves to HIGH via the escalation
    branch, while a protected path outside the jail is denied by the jail check
    first (agentcfg003 REQ-004: the declared tier is the risk source; a
    tier-NONE tool short-circuits before escalation)."""

    IN_JAIL_PROTECTED_PATH = "/opt/llm/config/app.toml"

    def _escalation_cfg(self) -> AgentConfig:
        return _make_cfg(
            allowed_root="/opt/llm",
            approval_protected_paths=SHIPPED_APPROVAL_PROTECTED_PATHS,
        )

    @staticmethod
    def _ctx_with_audit(ctx: MagicMock) -> MagicMock:
        ctx.services_required.audit_logger = MagicMock()
        ctx.services_required.tools = MagicMock()
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="Dry-run: would write",
                is_error=False,
                request_id="",
                server_key="",
            )
        )
        return ctx

    @pytest.mark.asyncio
    @pytest.mark.parametrize("tool", ["delete_file"])
    async def test_in_jail_protected_path_resolves_high(self, tool: str) -> None:
        ctx = self._ctx_with_audit(_make_ctx(cfg=self._escalation_cfg()))
        # HIGH risk requires the full word "yes" (_prompt_user_approval).
        with patch(
            "agent.tool_approval._approval_read", new=AsyncMock(return_value="yes")
        ):
            result = await check_approval(
                ctx, tool, {"path": self.IN_JAIL_PROTECTED_PATH}
            )
        assert result is True
        logged = ctx.services_required.audit_logger.info.call_args[0][0]
        assert '"risk":"high"' in logged

    @pytest.mark.asyncio
    @pytest.mark.parametrize("tool", ["write_file", "edit_file", "move_file"])
    async def test_tier_none_tool_is_not_escalated(self, tool: str) -> None:
        """agentcfg003 risk delta: the shipped WRITE_SAFE tools map to tier NONE
        and auto-approve on the same protected path — the removed per-tool risk
        rules no longer escalate them."""
        args: dict[str, Any] = (
            {"source": self.IN_JAIL_PROTECTED_PATH, "destination": "/opt/llm/other"}
            if tool == "move_file"
            else {"path": self.IN_JAIL_PROTECTED_PATH}
        )
        ctx = self._ctx_with_audit(_make_ctx(cfg=self._escalation_cfg()))
        read = AsyncMock(return_value="yes")
        with patch("agent.tool_approval._approval_read", new=read):
            result = await check_approval(ctx, tool, args)
        assert result is True
        read.assert_not_awaited()
        logged = ctx.services_required.audit_logger.info.call_args[0][0]
        assert '"risk":"none"' in logged

    @pytest.mark.asyncio
    @pytest.mark.parametrize("tool", ["delete_file"])
    async def test_same_path_without_protected_paths_stays_medium(
        self, tool: str
    ) -> None:
        """Branch provenance: removing the protected paths from the same config
        keeps the same call at the declared medium level, proving the HIGH above
        came from the escalation branch."""
        cfg = _make_cfg(allowed_root="/opt/llm", approval_protected_paths=[])
        ctx = self._ctx_with_audit(_make_ctx(cfg=cfg))
        with patch(
            "agent.tool_approval._approval_read", new=AsyncMock(return_value="y")
        ):
            result = await check_approval(
                ctx, tool, {"path": self.IN_JAIL_PROTECTED_PATH}
            )
        assert result is True
        logged = ctx.services_required.audit_logger.info.call_args[0][0]
        assert '"risk":"high"' not in logged
        assert '"risk":"medium"' in logged

    @pytest.mark.asyncio
    async def test_protected_path_outside_jail_denied_by_jail(self) -> None:
        """/etc/ is a shipped protected path but outside allowed_root: the jail
        denies it before the escalation branch runs — the two mechanisms stay
        distinguishable."""
        ctx = self._ctx_with_audit(_make_ctx(cfg=self._escalation_cfg()))
        read = AsyncMock(return_value="y")
        with patch("agent.tool_approval._approval_read", new=read):
            result = await check_approval(ctx, "delete_file", {"path": "/etc/cron.d/x"})
        assert result is False
        read.assert_not_awaited()
        logged = ctx.services_required.audit_logger.info.call_args[0][0]
        assert "denied_root_jail" in logged


# ── run_approval_checks(): grant horizon from config (mcpdl003 REQ-002) ──────


def _grant_pc(name: str, args: dict[str, Any]) -> PreparedToolCall:
    """PreparedToolCall carrying the preparation-phase execution context."""
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


class TestGrantTtlFromConfig:
    @pytest.mark.asyncio
    async def test_configured_ttl_sets_grant_horizon(self) -> None:
        ctx = _make_ctx(cfg=_make_cfg(approval_grant_ttl_seconds=120.0))
        ctx.conv.plan_mode = False
        ctx.services_required.audit_logger = MagicMock()
        approved, denied = await run_approval_checks(
            ctx, [_grant_pc("write_file", {"path": "/tmp/f"})]
        )
        assert denied == []
        grant = approved[0].grant
        assert grant is not None
        assert grant.expires_at - grant.issued_at == 120.0

    @pytest.mark.asyncio
    async def test_default_ttl_matches_retired_constant(self) -> None:
        ctx = _make_ctx()
        ctx.conv.plan_mode = False
        ctx.services_required.audit_logger = MagicMock()
        approved, denied = await run_approval_checks(
            ctx, [_grant_pc("write_file", {"path": "/tmp/f"})]
        )
        assert denied == []
        grant = approved[0].grant
        assert grant is not None
        assert grant.expires_at - grant.issued_at == _GRANT_TTL_SECONDS
        assert grant.mode == ApprovalDecisionType.AUTO.value
