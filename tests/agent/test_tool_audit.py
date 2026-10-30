"""tests/test_tool_audit.py
Unit tests for agent/tool_audit.py: audit logging functions.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pytest
from agent.config_builders import build_agent_config
from agent.config_dataclasses import AgentConfig
from agent.tool_audit import (
    AUDIT_ARGS_PREVIEW_MAX_CHARS,
    audit_approval,
    audit_stage_completed,
    audit_tool_exec,
    log_approval_decision,
    write_round_exec,
)
from agent.tool_enums import ApprovalDecisionType, RiskLevel
from agent.tool_models import ApprovalOutcome
from shared.json_utils import dumps as _json_dumps

from tests.agent._config_test_defaults import (
    ALL_TOOL_NAMES,
    STRICT_PRODUCTION_OVERRIDES,
)


def _make_cfg(**overrides: Any) -> AgentConfig:
    """Build a minimal AgentConfig with test-safe defaults."""
    base = build_agent_config(
        {
            **STRICT_PRODUCTION_OVERRIDES,
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


class TestAuditApprovalInv11:
    """INV-11: every tool-level approval decision is a tool_approval audit event
    that carries the workflow_id and the task_id field (the turn ID)."""

    @staticmethod
    def _logged_event(decision: ApprovalDecisionType) -> dict[str, Any]:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        ctx.turn.current_turn_id = "turn-xyz"
        audit_approval(
            ctx, "write_file", RiskLevel.MEDIUM, {"path": "/tmp/x.txt"}, decision
        )
        ctx.services_required.audit_logger.info.assert_called_once()
        return json.loads(ctx.services_required.audit_logger.info.call_args[0][0])

    def test_approved_decision_is_recorded_with_workflow_context(self) -> None:
        event = self._logged_event(ApprovalDecisionType.APPROVED)
        assert event["event"] == "tool_approval"
        assert event["decision"] == "approved"
        assert event["workflow_id"] == "wf-test-id"
        assert event["task_id"] == "turn-xyz"

    def test_denied_decision_is_recorded_with_workflow_context(self) -> None:
        event = self._logged_event(ApprovalDecisionType.DENIED)
        assert event["event"] == "tool_approval"
        assert event["decision"] == "denied"
        assert event["workflow_id"] == "wf-test-id"
        assert event["task_id"] == "turn-xyz"


class TestAuditStageCompleted:
    def _logged(self, **kwargs: Any) -> dict[str, Any]:
        ctx = MagicMock()
        ctx.services_required.audit_logger = MagicMock()
        audit_stage_completed(ctx, "t1", "execute", 12.5, **kwargs)
        ctx.services_required.audit_logger.info.assert_called_once()
        return json.loads(ctx.services_required.audit_logger.info.call_args[0][0])

    def test_event_includes_attempt_number(self) -> None:
        assert self._logged(attempt_number=2)["attempt_number"] == 2

    def test_attempt_number_defaults_to_null(self) -> None:
        event = self._logged()
        assert event["event"] == "stage_completed"
        assert event["attempt_number"] is None


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

    def test_skips_event_when_mcp_request_id_is_empty_and_source_is_empty(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        ctx.cfg.tool.masked_fields = []
        ctx.cfg.approval.approval_resource_keys = {}
        audit_tool_exec(ctx, "read_text_file", {}, False, "", source="")
        ctx.services_required.audit_logger.info.assert_not_called()

    def test_emits_event_when_mcp_request_id_empty_but_source_set(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        ctx.cfg.tool.masked_fields = []
        ctx.cfg.approval.approval_resource_keys = {}
        audit_tool_exec(ctx, "read_text_file", {}, False, "", source="cache")
        ctx.services_required.audit_logger.info.assert_called_once()
        logged = ctx.services_required.audit_logger.info.call_args[0][0]
        assert "tool_exec" in logged
        assert '"source":"cache"' in logged or '"source": "cache"' in logged
        assert "read_text_file" in logged

    def test_source_default_agent_in_audit_event(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        ctx.cfg.tool.masked_fields = []
        ctx.cfg.approval.approval_resource_keys = {}
        audit_tool_exec(ctx, "read_text_file", {"path": "/tmp/f"}, False, "req-123")
        ctx.services_required.audit_logger.info.assert_called_once()
        logged = ctx.services_required.audit_logger.info.call_args[0][0]
        assert '"source":"agent"' in logged or '"source": "agent"' in logged


def _args_preview_after_write(writer: str, args: dict[str, Any]) -> dict[str, Any]:
    """Run one audit writer with a mock sink and return the logged args_preview."""
    ctx = _make_ctx()
    ctx.services_required.audit_logger = MagicMock()
    ctx.cfg.tool.masked_fields = ["secret"]
    ctx.cfg.approval.approval_resource_keys = {}
    if writer == "approval":
        audit_approval(ctx, "write_file", RiskLevel.MEDIUM, args, "approved")
    else:
        audit_tool_exec(ctx, "write_file", args, False, "req-1")
    logged = ctx.services_required.audit_logger.info.call_args[0][0]
    preview: dict[str, Any] = json.loads(logged)["args_preview"]
    return preview


def _args_of_serialized_length(length: int) -> dict[str, Any]:
    """Build args whose serialized form is exactly ``length`` characters."""
    base = len(_json_dumps({"k": ""}))
    return {"k": "x" * (length - base)}


@pytest.mark.parametrize("writer", ["approval", "exec"])
class TestArgsPreviewBound:
    def test_oversized_value_becomes_envelope(self, writer: str) -> None:
        preview = _args_preview_after_write(writer, {"k": "x" * 5000})
        assert preview["truncated"] is True
        assert len(preview["preview"]) <= AUDIT_ARGS_PREVIEW_MAX_CHARS
        assert "k" not in preview

    def test_exactly_at_cap_is_unchanged(self, writer: str) -> None:
        args = _args_of_serialized_length(AUDIT_ARGS_PREVIEW_MAX_CHARS)
        assert _args_preview_after_write(writer, args) == args

    def test_one_over_cap_becomes_envelope(self, writer: str) -> None:
        args = _args_of_serialized_length(AUDIT_ARGS_PREVIEW_MAX_CHARS + 1)
        preview = _args_preview_after_write(writer, args)
        assert preview["truncated"] is True
        assert len(preview["preview"]) == AUDIT_ARGS_PREVIEW_MAX_CHARS

    def test_masked_value_survives_prefix_and_marker_is_distinct(
        self, writer: str
    ) -> None:
        args = {"secret": "RAW-SECRET-VALUE", "z": "x" * 5000}
        preview = _args_preview_after_write(writer, args)
        assert preview["truncated"] is True
        assert "***" in preview["preview"]
        assert "RAW-SECRET-VALUE" not in preview["preview"]


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
