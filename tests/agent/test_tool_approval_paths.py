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
    STRICT_PRODUCTION_OVERRIDES,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_cfg(**overrides: Any) -> AgentConfig:
    """Build a minimal AgentConfig with test-safe defaults."""
    base = build_agent_config(
        {
            **STRICT_PRODUCTION_OVERRIDES,
            "allowed_tools": ALL_TOOL_NAMES,
            "context_char_limit": 8000,
            "context_compress_turns": 4,
            "llm_max_retries": 3,
            "llm_retry_base_delay": 1.0,
            "masked_fields": [],
            "plan_blocked_tools": [],
            "llm_temperature": 0.2,
            "llm_max_tokens": 1024,
            "use_refiner": False,
            "refiner_max_tokens": 512,
            "refiner_timeout": 30.0,
            "refiner_max_chars_per_chunk": 300,
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

        with patch("asyncio.to_thread", new=AsyncMock(return_value="y")):
            result = await check_approval(
                ctx, "write_file", {"path": f"{root}/file.txt"}
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_disabled_root_does_not_block(self, tmp_path: Any) -> None:
        # Use tmp_path (not /etc) to avoid triggering approval_protected_paths escalation
        outside = str(tmp_path / "outside.txt")
        cfg = _make_cfg(allowed_root="", approval_protected_paths=[])
        ctx = _make_ctx(cfg=cfg)
        ctx.services_required.tools = MagicMock()
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output=f"Dry-run: {outside} [would write]",
                is_error=False,
                request_id="",
                server_key="",
            )
        )

        with patch("asyncio.to_thread", new=AsyncMock(return_value="y")):
            result = await check_approval(ctx, "write_file", {"path": outside})

        assert result is True
