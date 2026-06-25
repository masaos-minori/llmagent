"""
tests/test_tool_approval_preflight.py
Unit tests for check_approval() flows, audit logging, tool execution, and approval checks.

Covers check_approval(), _audit_approval(), _audit_tool_exec(),
execute_one_tool_call(), log_approval_decision(), and run_approval_checks().
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.config import AgentConfig, build_agent_config
from agent.tool_approval import check_approval, run_approval_checks
from agent.tool_audit import audit_approval as _audit_approval
from agent.tool_audit import audit_tool_exec as _audit_tool_exec
from agent.tool_audit import log_approval_decision
from agent.tool_enums import ApprovalDecisionType, RiskLevel
from agent.tool_models import ApprovalOutcome
from agent.tool_runner import execute_one_tool_call
from shared.tool_executor import ToolCallResult

# ── Fixtures ──────────────────────────────────────────────────────────────────


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
            "auto_inject_notes": False,
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
            # Standard tier classification; mirrors config/agent.json defaults
            "tool_safety_tiers": {
                "list_directory": "READ_ONLY",
                "read_text_file": "READ_ONLY",
                "directory_tree": "READ_ONLY",
                "search_files": "READ_ONLY",
                "grep_files": "READ_ONLY",
                "search_web": "READ_ONLY",
                "github_search_repositories": "READ_ONLY",
                "github_get_file_contents": "READ_ONLY",
                "write_file": "WRITE_SAFE",
                "edit_file": "WRITE_SAFE",
                "create_directory": "WRITE_SAFE",
                "move_file": "WRITE_SAFE",
                "github_create_branch": "WRITE_SAFE",
                "github_create_issue": "WRITE_SAFE",
                "github_add_issue_comment": "WRITE_SAFE",
                "delete_file": "WRITE_DANGEROUS",
                "delete_directory": "WRITE_DANGEROUS",
                "github_push_files": "WRITE_DANGEROUS",
                "github_create_or_update_file": "WRITE_DANGEROUS",
                "github_delete_file": "WRITE_DANGEROUS",
                "github_merge_pull_request": "WRITE_DANGEROUS",
                "github_create_pull_request": "WRITE_DANGEROUS",
                "github_update_pull_request": "WRITE_DANGEROUS",
                "shell_run": "ADMIN",
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
    ctx.workflow.workflow_id = None
    ctx.session.session_id = None
    ctx.services.audit_logger = None
    ctx.services.tools = AsyncMock()
    return ctx


# ── check_approval() ─────────────────────────────────────────────────────────


class TestCheckApproval:
    @pytest.mark.asyncio
    async def test_none_risk_auto_approved(self) -> None:
        ctx = _make_ctx()
        with patch("builtins.input") as mock_input:
            result = await check_approval(ctx, "list_directory", {"path": "/tmp"})
        assert result is True
        mock_input.assert_not_called()

    @pytest.mark.asyncio
    async def test_medium_risk_y_approved(self) -> None:
        ctx = _make_ctx()
        with patch("asyncio.to_thread", new=AsyncMock(return_value="y")):
            result = await check_approval(ctx, "write_file", {"path": "/tmp/f.txt"})
        assert result is True

    @pytest.mark.asyncio
    async def test_medium_risk_n_denied(self) -> None:
        ctx = _make_ctx()
        with patch("asyncio.to_thread", new=AsyncMock(return_value="n")):
            result = await check_approval(ctx, "write_file", {"path": "/tmp/f.txt"})
        assert result is False

    @pytest.mark.asyncio
    async def test_high_risk_yes_approved(self) -> None:
        ctx = _make_ctx()
        with patch("asyncio.to_thread", new=AsyncMock(return_value="yes")):
            result = await check_approval(ctx, "delete_file", {"path": "/tmp/f.txt"})
        assert result is True

    @pytest.mark.asyncio
    async def test_high_risk_y_is_insufficient(self) -> None:
        # 'y' alone must NOT approve a high-risk operation
        ctx = _make_ctx()
        with patch("asyncio.to_thread", new=AsyncMock(return_value="y")):
            result = await check_approval(ctx, "delete_file", {"path": "/tmp/f.txt"})
        assert result is False

    @pytest.mark.asyncio
    async def test_audit_log_written_on_medium_approval(self) -> None:
        ctx = _make_ctx()
        audit = MagicMock()
        ctx.services.audit_logger = audit
        with patch("asyncio.to_thread", new=AsyncMock(return_value="y")):
            await check_approval(ctx, "write_file", {"path": "/tmp/f.txt"})
        audit.info.assert_called_once()
        logged = audit.info.call_args[0][0]
        assert "tool_approval" in logged
        assert "approved" in logged

    @pytest.mark.asyncio
    async def test_audit_log_written_on_denial(self) -> None:
        ctx = _make_ctx()
        audit = MagicMock()
        ctx.services.audit_logger = audit
        with patch("asyncio.to_thread", new=AsyncMock(return_value="n")):
            await check_approval(ctx, "write_file", {"path": "/tmp/f.txt"})
        logged = audit.info.call_args[0][0]
        assert "denied" in logged

    @pytest.mark.asyncio
    async def test_audit_log_auto_for_none_risk(self) -> None:
        ctx = _make_ctx()
        audit = MagicMock()
        ctx.services.audit_logger = audit
        with patch("builtins.input"):
            await check_approval(ctx, "list_directory", {})
        logged = audit.info.call_args[0][0]
        assert "auto" in logged

    @pytest.mark.asyncio
    async def test_audit_log_skipped_when_no_logger(self) -> None:
        ctx = _make_ctx()
        ctx.services.audit_logger = None
        # Should not raise even with no audit logger
        with patch("asyncio.to_thread", new=AsyncMock(return_value="y")):
            result = await check_approval(ctx, "write_file", {"path": "/tmp/f.txt"})
        assert result is True

    @pytest.mark.asyncio
    async def test_medium_risk_empty_input_denied(self) -> None:
        ctx = _make_ctx()
        with patch("asyncio.to_thread", new=AsyncMock(return_value="")):
            result = await check_approval(ctx, "write_file", {"path": "/tmp/f.txt"})
        assert result is False

    @pytest.mark.asyncio
    async def test_medium_risk_input_with_whitespace_approved(self) -> None:
        ctx = _make_ctx()
        with patch("asyncio.to_thread", new=AsyncMock(return_value=" y ")):
            result = await check_approval(ctx, "write_file", {"path": "/tmp/f.txt"})
        assert result is True

    @pytest.mark.asyncio
    async def test_high_risk_empty_input_denied(self) -> None:
        ctx = _make_ctx()
        with patch("asyncio.to_thread", new=AsyncMock(return_value="")):
            result = await check_approval(ctx, "delete_file", {"path": "/tmp/f.txt"})
        assert result is False

    @pytest.mark.asyncio
    async def test_high_risk_input_with_whitespace_approved(self) -> None:
        ctx = _make_ctx()
        with patch("asyncio.to_thread", new=AsyncMock(return_value=" yes ")):
            result = await check_approval(ctx, "delete_file", {"path": "/tmp/f.txt"})
        assert result is True

    @pytest.mark.asyncio
    async def test_audit_log_skipped_when_no_logger_high_risk(self) -> None:
        ctx = _make_ctx()
        ctx.services.audit_logger = None
        with patch("asyncio.to_thread", new=AsyncMock(return_value="yes")):
            result = await check_approval(ctx, "delete_file", {"path": "/tmp/f.txt"})
        assert result is True

    @pytest.mark.asyncio
    async def test_audit_logger_error_propagates(self) -> None:
        ctx = _make_ctx()
        audit = MagicMock()
        ctx.services.audit_logger = audit
        audit.info.side_effect = RuntimeError("audit error")
        with patch("asyncio.to_thread", new=AsyncMock(return_value="y")):
            with pytest.raises(RuntimeError, match="audit error"):
                await check_approval(ctx, "write_file", {"path": "/tmp/f.txt"})

    @pytest.mark.asyncio
    async def test_medium_risk_uppercase_y_approved(self) -> None:
        ctx = _make_ctx()
        with patch("asyncio.to_thread", new=AsyncMock(return_value="Y")):
            result = await check_approval(ctx, "write_file", {"path": "/tmp/f.txt"})
        assert result is True

    @pytest.mark.asyncio
    async def test_high_risk_uppercase_yes_approved(self) -> None:
        ctx = _make_ctx()
        with patch("asyncio.to_thread", new=AsyncMock(return_value="YES")):
            result = await check_approval(ctx, "delete_file", {"path": "/tmp/f.txt"})
        assert result is True

    @pytest.mark.asyncio
    async def test_medium_risk_full_word_yes_is_insufficient(self) -> None:
        ctx = _make_ctx()
        with patch("asyncio.to_thread", new=AsyncMock(return_value="yes")):
            result = await check_approval(ctx, "write_file", {"path": "/tmp/f.txt"})
        assert result is False


# ── _audit_approval() ─────────────────────────────────────────────────────────


class TestAuditApproval:
    def test_no_op_when_audit_logger_is_none(self) -> None:
        ctx = _make_ctx()
        ctx.services.audit_logger = None
        # Must not raise
        _audit_approval(ctx, "delete_file", "high", {"path": "/tmp/x"}, "approved")

    def test_writes_json_lines_event(self) -> None:
        ctx = _make_ctx()
        audit = MagicMock()
        ctx.services.audit_logger = audit
        _audit_approval(ctx, "shell_run", "high", {"command": "rm /tmp/x"}, "denied")
        audit.info.assert_called_once()
        payload: str = audit.info.call_args[0][0]
        import orjson

        event = orjson.loads(payload)
        assert event["event"] == "tool_approval"
        assert event["tool"] == "shell_run"
        assert event["risk"] == "high"
        assert event["decision"] == "denied"
        assert "ts" in event

    def test_masked_fields_applied_to_args(self) -> None:
        cfg = _make_cfg(masked_fields=["secret"])
        ctx = _make_ctx(cfg=cfg)
        audit = MagicMock()
        ctx.services.audit_logger = audit
        _audit_approval(
            ctx,
            "write_file",
            "medium",
            {"path": "/tmp/f", "secret": "s3cr3t"},
            "approved",
        )
        payload: str = audit.info.call_args[0][0]
        assert "s3cr3t" not in payload

    def test_operation_type_in_audit_event(self) -> None:
        ctx = _make_ctx()
        audit = MagicMock()
        ctx.services.audit_logger = audit
        _audit_approval(ctx, "delete_file", "high", {"path": "/tmp/x"}, "denied")
        import orjson

        event = orjson.loads(audit.info.call_args[0][0])
        assert event["operation_type"] == "delete"

    def test_resource_scope_contains_path_keys(self) -> None:
        ctx = _make_ctx()
        audit = MagicMock()
        ctx.services.audit_logger = audit
        _audit_approval(
            ctx,
            "write_file",
            "medium",
            {"path": "/opt/llm/x.py", "other": "val"},
            "approved",
        )
        import orjson

        event = orjson.loads(audit.info.call_args[0][0])
        assert "path" in event["resource_scope"]
        assert "other" not in event["resource_scope"]

    def test_resource_scope_contains_branch_keys(self) -> None:
        ctx = _make_ctx()
        audit = MagicMock()
        ctx.services.audit_logger = audit
        _audit_approval(
            ctx,
            "github_create_pull_request",
            "medium",
            {"owner": "org", "repo": "r", "base": "main"},
            "approved",
        )
        import orjson

        event = orjson.loads(audit.info.call_args[0][0])
        assert "base" in event["resource_scope"]
        assert "owner" not in event["resource_scope"]


# ── check_approval() dry_run flow ─────────────────────────────────────────────


class TestCheckApprovalDryRun:
    @pytest.mark.asyncio
    async def test_dry_run_result_appended_to_preview(self) -> None:
        """dry_run execution output should be included in preview before prompt."""
        cfg = _make_cfg()
        ctx = _make_ctx(cfg=cfg)
        ctx.services.tools = MagicMock()
        ctx.services.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="Dry-run: /tmp/f (5 bytes) [new file]", is_error=False, request_id="", server_key=""
            )
        )

        printed: list[str] = []
        with (
            patch("builtins.print", side_effect=lambda *a: printed.append(str(a))),
            patch("asyncio.to_thread", new=AsyncMock(return_value="y")),
        ):
            result = await check_approval(
                ctx, "write_file", {"path": "/tmp/f.txt", "content": "hi"}
            )

        assert result is True
        combined = " ".join(printed)
        assert "Dry-run" in combined
        ctx.services.tools.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_dry_run_skipped_for_non_dry_run_tool(self) -> None:
        """shell_run is not in approval_dry_run_tools; dry_run must not be called."""
        cfg = _make_cfg(approval_dry_run_tools=[])
        ctx = _make_ctx(cfg=cfg)
        ctx.services.tools = MagicMock()
        ctx.services.tools.execute = AsyncMock()

        with patch("asyncio.to_thread", new=AsyncMock(return_value="yes")):
            await check_approval(ctx, "shell_run", {"command": "rm /tmp/x"})

        ctx.services.tools.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_dry_run_exception_does_not_abort_approval(self) -> None:
        """If dry_run raises, approval flow must continue normally."""
        cfg = _make_cfg()
        ctx = _make_ctx(cfg=cfg)
        ctx.services.tools = MagicMock()
        ctx.services.tools.execute = AsyncMock(side_effect=RuntimeError("mcp error"))

        with (
            patch("builtins.print"),
            patch("asyncio.to_thread", new=AsyncMock(return_value="y")),
        ):
            result = await check_approval(
                ctx, "write_file", {"path": "/tmp/f.txt", "content": "hi"}
            )

        assert result is True  # approval still proceeds


# ── _audit_tool_exec() ────────────────────────────────────────────────────────


class TestAuditToolExec:
    def test_writes_to_audit_logger_when_conditions_met(self) -> None:
        ctx = _make_ctx()
        ctx.services.audit_logger = MagicMock()
        ctx.cfg.masked_fields = []
        ctx.turn.current_turn_id = "turn-abc"

        _audit_tool_exec(ctx, "read_text_file", {"path": "/tmp/f"}, False, "req-123")

        ctx.services.audit_logger.info.assert_called_once()
        logged = ctx.services.audit_logger.info.call_args[0][0]
        assert "tool_exec" in logged
        assert "req-123" in logged
        assert "operation_type" in logged
        assert "resource_scope" in logged

    def test_skips_when_audit_logger_is_none(self) -> None:
        ctx = _make_ctx()
        ctx.services.audit_logger = None
        # No error raised even though logger is None
        _audit_tool_exec(ctx, "read_text_file", {}, False, "req-123")

    def test_skips_when_mcp_request_id_is_empty(self) -> None:
        ctx = _make_ctx()
        ctx.services.audit_logger = MagicMock()
        _audit_tool_exec(ctx, "read_text_file", {}, False, "")
        ctx.services.audit_logger.info.assert_not_called()


# ── execute_one_tool_call() ───────────────────────────────────────────────────


class TestExecuteOneToolCall:
    @pytest.mark.asyncio
    async def test_unpacks_three_tuple_from_execute(self) -> None:
        ctx = _make_ctx()
        ctx.services.tools = MagicMock()
        ctx.services.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="result text", is_error=False, request_id="", server_key=""
            )
        )
        ctx.services.gateway = MagicMock()
        ctx.services.gateway.execute = AsyncMock(
            return_value=ToolCallResult(
                output="result text", is_error=False, request_id="", server_key=""
            )
        )
        ctx.services.audit_logger = None
        ctx.cfg.use_tool_summarize = False
        ctx.cfg.tool_result_max_llm_chars = 4000
        ctx.cfg.masked_fields = []

        tc = {
            "id": "call_1",
            "function": {"name": "read_text_file", "arguments": '{"path": "/tmp/f"}'},
        }
        tc_id, name, args, full_text, is_error, llm_text = await execute_one_tool_call(
            ctx, tc, 0
        )

        assert tc_id == "call_1"
        assert name == "read_text_file"
        assert full_text == "result text"
        assert not is_error
        ctx.services.gateway.execute.assert_awaited_once_with(
            ctx, "read_text_file", {"path": "/tmp/f"}
        )

    @pytest.mark.asyncio
    async def test_audit_tool_exec_called_with_x_request_id(self) -> None:
        ctx = _make_ctx()
        ctx.services.tools = MagicMock()
        ctx.services.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="ok", is_error=False, request_id="req-999", server_key=""
            )
        )
        ctx.services.gateway = MagicMock()
        ctx.services.gateway.execute = AsyncMock(
            return_value=ToolCallResult(
                output="ok", is_error=False, request_id="req-999", server_key=""
            )
        )
        ctx.services.audit_logger = MagicMock()
        ctx.cfg.use_tool_summarize = False
        ctx.cfg.tool_result_max_llm_chars = 4000
        ctx.cfg.masked_fields = []
        ctx.turn.current_turn_id = "turn-x"

        tc = {"id": "call_2", "function": {"name": "read_text_file", "arguments": "{}"}}
        await execute_one_tool_call(ctx, tc, 0)

        ctx.services.audit_logger.info.assert_called_once()
        logged = ctx.services.audit_logger.info.call_args[0][0]
        assert "req-999" in logged


# ── log_approval_decision ─────────────────────────────────────────────────────


class TestLogApprovalDecision:
    def test_logs_structured_event(self) -> None:
        ctx = _make_ctx()
        ctx.services.audit_logger = MagicMock()
        ctx.turn.current_turn_id = "turn-xyz"
        outcome = ApprovalOutcome(
            tool_name="write_file",
            risk_level=RiskLevel.MEDIUM,
            decision=ApprovalDecisionType.APPROVED,
            escalation_reason="",
        )
        log_approval_decision(ctx, outcome)
        ctx.services.audit_logger.info.assert_called_once()
        logged = ctx.services.audit_logger.info.call_args[0][0]
        assert "approval_decision" in logged
        assert "write_file" in logged
        assert "task_id" in logged
        assert "turn-xyz" in logged
        assert "ts" in logged

    def test_no_op_when_audit_logger_none(self) -> None:
        ctx = _make_ctx()
        ctx.services.audit_logger = None
        outcome = ApprovalOutcome(
            tool_name="write_file",
            risk_level=RiskLevel.MEDIUM,
            decision=ApprovalDecisionType.APPROVED,
        )
        log_approval_decision(ctx, outcome)  # must not raise


# ── run_approval_checks() ─────────────────────────────────────────────────────


class TestRunApprovalChecks:
    @pytest.mark.asyncio
    async def test_approved_calls_returned(self) -> None:
        cfg = _make_cfg(approval_risk_rules={"list_directory": "none"})
        ctx = _make_ctx(cfg)
        tool_calls = [
            {
                "id": "call_1",
                "function": {
                    "name": "list_directory",
                    "arguments": '{"path": "/tmp"}',
                },
            }
        ]
        approved, denied = await run_approval_checks(ctx, tool_calls)
        assert len(approved) == 1
        assert denied == []

    @pytest.mark.asyncio
    async def test_denied_calls_collected(self) -> None:
        cfg = _make_cfg(approval_risk_rules={"write_file": "medium"})
        ctx = _make_ctx(cfg)
        ctx.services.audit_logger = MagicMock()
        tool_calls = [
            {
                "id": "call_1",
                "function": {
                    "name": "write_file",
                    "arguments": '{"path": "/tmp/f"}',
                },
            }
        ]
        with patch("asyncio.to_thread", new=AsyncMock(return_value="n")):
            approved, denied = await run_approval_checks(ctx, tool_calls)
        assert approved == []
        assert denied == ["call_1"]

    @pytest.mark.asyncio
    async def test_plan_mode_blocks_configured_tools(self) -> None:
        cfg = _make_cfg(
            approval_risk_rules={"write_file": "medium"},
            plan_blocked_tools=["write_file"],
        )
        ctx = _make_ctx(cfg)
        ctx.conv.plan_mode = True
        ctx.services.audit_logger = MagicMock()
        tool_calls = [
            {
                "id": "call_1",
                "function": {
                    "name": "write_file",
                    "arguments": '{"path": "/tmp/f"}',
                },
            }
        ]
        approved, denied = await run_approval_checks(ctx, tool_calls)
        assert approved == []
        assert denied == ["call_1"]
        # Should not prompt the user
        with patch("asyncio.to_thread") as mock_thread:
            mock_thread.assert_not_called()

    @pytest.mark.asyncio
    async def test_plan_mode_does_not_block_unlisted_tools(self) -> None:
        cfg = _make_cfg(
            approval_risk_rules={"list_directory": "none"},
            plan_blocked_tools=["write_file"],
        )
        ctx = _make_ctx(cfg)
        ctx.conv.plan_mode = True
        ctx.services.audit_logger = MagicMock()
        tool_calls = [
            {
                "id": "call_1",
                "function": {
                    "name": "list_directory",
                    "arguments": '{"path": "/tmp"}',
                },
            }
        ]
        approved, denied = await run_approval_checks(ctx, tool_calls)
        assert len(approved) == 1
        assert denied == []

    @pytest.mark.asyncio
    async def test_invalid_json_arguments_does_not_crash(self) -> None:
        cfg = _make_cfg(approval_risk_rules={"list_directory": "none"})
        ctx = _make_ctx(cfg)
        tool_calls = [
            {
                "id": "call_1",
                "function": {
                    "name": "list_directory",
                    "arguments": "not valid json",
                },
            }
        ]
        approved, denied = await run_approval_checks(ctx, tool_calls)
        assert len(approved) == 1
