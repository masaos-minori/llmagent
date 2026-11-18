"""
tests/test_tool_approval_paths.py
Unit tests for the allowed_root pre-flight check in check_approval().

Covers path-based root jail detection before risk classification.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.config_builders import build_agent_config
from agent.config_dataclasses import AgentConfig
from agent.tool_approval import check_approval
from shared.transport_dto import ToolCallResult

from tests.agent._config_test_defaults import (
    ALL_APPROVAL_RISK_RULES,
    ALL_TOOL_NAMES,
    ALL_TOOL_SAFETY_TIERS,
    PERMISSIVE_ALLOWED_ROOT,
    PERMISSIVE_SQLITE_VEC_SO,
    SHIPPED_APPROVAL_PROTECTED_PATHS,
)

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
            # memory_embed_enabled now defaults to True; embed_url must be non-empty
            # to satisfy AgentConfig.__post_init__'s cross-field validation.
            "embed_url": "http://127.0.0.1:9999",
            "mcp_servers": {
                "_dummy": {
                    "transport": "http",
                    "url": "http://127.0.0.1:9999",
                    "auth_token": "test-token",
                }
            },
            # Standard tier classification; mirrors config/agent.toml defaults
            "tool_safety_tiers": ALL_TOOL_SAFETY_TIERS,
            "approval_risk_rules": ALL_APPROVAL_RISK_RULES,
            "allowed_root": PERMISSIVE_ALLOWED_ROOT,
            "sqlite_vec_so": PERMISSIVE_SQLITE_VEC_SO,
            **overrides,
        }
    )
    return base


def _make_ctx(cfg: AgentConfig | None = None) -> MagicMock:
    """Build a minimal AgentContext mock."""
    ctx = MagicMock()
    ctx.cfg = cfg or _make_cfg()
    ctx.turn.current_turn_id = "test-turn-id"
    ctx.workflow.workflow_id = "wf-test-id"
    ctx.session.session_id = None
    ctx.services_required.audit_logger = None
    ctx.services_required.tools = AsyncMock()
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
    """Pin that a ruled path-bearing tool on a shipped protected path inside
    allowed_root resolves to HIGH via the escalation branch, while a
    protected path outside the jail is denied by the jail check first."""

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
    @pytest.mark.parametrize("tool", ["write_file", "edit_file", "move_file"])
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
    async def test_same_path_without_protected_paths_stays_medium(
        self, tool: str
    ) -> None:
        """Branch provenance: removing the protected paths from the same config
        keeps the same call at the ruled medium level, proving the HIGH above
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
            result = await check_approval(ctx, "write_file", {"path": "/etc/cron.d/x"})
        assert result is False
        read.assert_not_awaited()
        logged = ctx.services_required.audit_logger.info.call_args[0][0]
        assert "denied_root_jail" in logged
