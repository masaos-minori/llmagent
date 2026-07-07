"""tests/test_tool_audit.py
Unit tests for agent/tool_audit.py: audit logging functions.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

from agent.config_builders import build_agent_config
from agent.config_dataclasses import AgentConfig
from agent.tool_audit import audit_tool_exec, log_approval_decision, write_round_exec
from agent.tool_enums import ApprovalDecisionType, RiskLevel
from agent.tool_models import ApprovalOutcome


def _make_cfg(**overrides: Any) -> AgentConfig:
    """Build a minimal AgentConfig with test-safe defaults."""
    base = build_agent_config(
        {
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
            "use_tool_summarize": False,
            "tool_summarize_threshold": 3000,
            "use_semantic_cache": False,
            "semantic_cache_threshold": 0.92,
            "semantic_cache_max_size": 100,
            "tool_definitions_strict": False,
            "mcp_watchdog_interval": 0.0,
            "mcp_watchdog_max_restarts": 3,
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
            "web_search_url": "http://127.0.0.1:8004",
            "github_server_url": "http://127.0.0.1:8006",
            "mcp_servers": {
                "_dummy": {"transport": "http", "url": "http://127.0.0.1:9999"}
            },
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
    return ctx


class TestLogApprovalDecision:
    def test_logs_structured_event(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        ctx.turn.current_turn_id = "turn-xyz"
        outcome = ApprovalOutcome(
            tool_name="write_file",
            risk_level=RiskLevel.MEDIUM,
            decision=ApprovalDecisionType.APPROVED,
            escalation_reason="",
        )
        log_approval_decision(ctx, outcome)
        ctx.services_required.audit_logger.info.assert_called_once()
        logged = ctx.services_required.audit_logger.info.call_args[0][0]
        assert "approval_decision" in logged
        assert "write_file" in logged
        assert "task_id" in logged
        assert "turn-xyz" in logged
        assert "ts" in logged

    def test_no_op_when_audit_logger_none(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = None
        outcome = ApprovalOutcome(
            tool_name="write_file",
            risk_level=RiskLevel.NONE,
            decision=ApprovalDecisionType.APPROVED,
        )
        log_approval_decision(ctx, outcome)  # must not raise


class TestAuditToolExec:
    def test_writes_to_audit_logger_when_conditions_met(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        ctx.cfg.tool.masked_fields = []
        ctx.cfg.approval.approval_resource_keys = {}
        ctx.turn.current_turn_id = "turn-abc"

        audit_tool_exec(ctx, "read_text_file", {"path": "/tmp/f"}, False, "req-123")

        ctx.services_required.audit_logger.info.assert_called_once()
        logged = ctx.services_required.audit_logger.info.call_args[0][0]
        assert "tool_exec" in logged
        assert "req-123" in logged
        assert "operation_type" in logged
        assert "resource_scope" in logged

    def test_skips_when_audit_logger_is_none(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = None
        # No error raised even though logger is None
        audit_tool_exec(ctx, "read_text_file", {}, False, "req-123")

    def test_skips_event_when_mcp_request_id_is_empty(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        ctx.cfg.tool.masked_fields = []
        ctx.cfg.approval.approval_resource_keys = {}
        audit_tool_exec(ctx, "read_text_file", {}, False, "")
        ctx.services_required.audit_logger.info.assert_not_called()


class TestWriteRoundExec:
    def test_logs_new_fields_when_provided(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        write_round_exec(
            ctx,
            round_id="r-1",
            tool_count=2,
            mode="serial",
            has_side_effect=True,
            trigger_tool="write_file",
            elapsed_ms=50.0,
            affected_tools=["write_file", "read_text_file"],
            serial_reason="side_effect",
            estimated_parallel_ms=20.0,
        )
        ctx.services_required.audit_logger.info.assert_called_once()
        logged = ctx.services_required.audit_logger.info.call_args[0][0]
        extra = json.loads(logged)
        assert extra["affected_tools"] == ["write_file", "read_text_file"]
        assert extra["serial_reason"] == "side_effect"
        assert extra["estimated_parallel_ms"] == 20.0

    def test_defaults_to_empty_when_omitted(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        write_round_exec(
            ctx,
            round_id="r-2",
            tool_count=1,
            mode="parallel",
            has_side_effect=False,
            trigger_tool=None,
            elapsed_ms=10.0,
        )
        logged = ctx.services_required.audit_logger.info.call_args[0][0]
        extra = json.loads(logged)
        assert extra["affected_tools"] == []
        assert extra["serial_reason"] is None
        assert extra["estimated_parallel_ms"] is None

    def test_no_op_when_audit_logger_none(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = None
        write_round_exec(
            ctx,
            round_id="r-3",
            tool_count=1,
            mode="parallel",
            has_side_effect=False,
            trigger_tool=None,
            elapsed_ms=5.0,
        )  # must not raise
